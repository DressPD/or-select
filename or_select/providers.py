"""Real LLM backends: OpenAI, Gemini, and OpenRouter generation, scoring,
and judging.

Requires OPENAI_API_KEY / GOOGLE_API_KEY / OPENROUTER_API_KEY in the
environment (see .env, created from .env.example). Used to validate the
OR-Select pipeline against real, heterogeneous model output instead of the
deterministic placeholders in pipeline.py.

Clients are created lazily (only when a function is first called) so
importing this module never requires both providers' keys to be set.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import zlib
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-terra")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")

_NUMBER_RE = re.compile(r"[-+]?\d*\.?\d+")
# Lowercase, no-underscore markers: matches "RESOURCE_EXHAUSTED" (Gemini),
# "ResourceExhausted" (OpenRouter's upstream-wrapped Nvidia error), generic
# "rate limit" / "429" phrasing from any provider, and transient network/
# proxy failures (this environment's corporate proxy occasionally 407s mid
# -batch, same class of blip as a rate limit from the caller's perspective).
_RETRYABLE_MARKERS = (
    "429",
    "resourceexhausted",
    "rate limit",
    "ratelimit",
    "407",
    "proxy",
    "connection error",
    "apiconnectionerror",
    # OpenRouter's generic wrapper for an upstream provider hiccup (seen live
    # as a bare 404 with no message body from Nvidia) -- deliberately not a
    # bare "404" marker, since a real "model not found" 404 should fail fast,
    # not retry forever.
    "provider returned error",
)
# Checked BEFORE _RETRYABLE_MARKERS and wins on conflict: these are 429s
# that will never resolve by waiting (no credits, not "too many requests
# per minute"), so retrying them just burns ~4 minutes of backoff before
# failing anyway. Fail fast instead.
_PERMANENT_ERROR_MARKERS = (
    "insufficientquota",
    "creditbalanceexhausted",
    "billing",
)


STALL_TIMEOUT_SECONDS = 120.0


class StallTimeout(Exception):
    """A single API call produced neither a result nor an error within
    STALL_TIMEOUT_SECONDS of real wall-clock time.

    Observed live under severe OpenRouter free-tier saturation as hangs
    lasting 30+ minutes to multiple hours with no exception ever raised
    (docs/benchmark_results.md, Track C) -- plausibly a trickle of
    keep-alive bytes resetting the HTTP client's own read-timeout on every
    partial receive, so a per-read timeout never fires even though the
    request is never actually progressing. _call_with_stall_timeout enforces
    a real deadline regardless of that activity by running the call in a
    worker thread and giving up on waiting for it, rather than trusting the
    SDK's own timeout. This turns an indefinite hang into an explicit,
    retryable failure -- this repo's design boundary (README: failed
    candidates stay explicit, never silently dropped/hung) applied to the
    one failure mode that previously required a human to notice and kill
    the process by hand.
    """


def _call_with_stall_timeout(fn, timeout: float = STALL_TIMEOUT_SECONDS):
    # A ThreadPoolExecutor was tried first, but its worker threads are
    # non-daemon and concurrent.futures.thread registers a module-level
    # atexit hook that joins every worker thread ever created, from every
    # pool, even ones explicitly shut down with wait=False. When a call
    # genuinely stalls (the exact case this function exists to handle),
    # that orphaned thread is stuck in a hung network call forever, so the
    # interpreter hangs at process exit -- observed live: a benchmark run
    # printed its final summary and `written: ...` but the process itself
    # sat alive (confirmed via `ps -M`, 5 leftover worker threads) instead
    # of terminating, silently defeating the whole point of this mechanism.
    # A plain daemon Thread has no such atexit registration -- daemon
    # threads are simply abandoned at interpreter shutdown, so a stuck one
    # can no longer block the process from actually exiting.
    box: list = []
    errors: list = []

    def _run() -> None:
        try:
            box.append(fn())
        except BaseException as exc:  # noqa: BLE001 -- re-raised on the caller's thread below
            errors.append(exc)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise StallTimeout(f"no result after {timeout:.0f}s")
    if errors:
        raise errors[0]
    return box[0]


def _is_retryable_error(exc: Exception) -> bool:
    # A hard wall-clock deadline was exceeded waiting for this call -- by
    # construction the same class of transient infra failure as a rate
    # limit, just caught by our own timer instead of an HTTP error.
    if isinstance(exc, StallTimeout):
        return True
    # A truncated/malformed response body breaks the SDK's own JSON parsing
    # before our code ever sees a status code or error field -- observed
    # live under the same upstream saturation that produces the 502/504/404
    # markers below, just caught one layer earlier. Its message ("Expecting
    # value: line N column M") carries no provider-specific marker to match
    # on, so it's checked by exception type instead of by text.
    if isinstance(exc, json.JSONDecodeError):
        return True
    # openai.APITimeoutError (a subclass of APIConnectionError) is raised by
    # the SDK's *own* internal timeout, separate from our StallTimeout above
    # -- observed live as ~84 consecutive failures with zero retries during
    # a sustained OpenRouter outage, because its message is just "Request
    # timed out." with no provider-specific text marker, so the
    # "apiconnectionerror" text marker below never actually matched it (the
    # class name never appears in str(exc)). Checked by type for the same
    # reason as the two cases above.
    try:
        from openai import APIConnectionError

        if isinstance(exc, APIConnectionError):
            return True
    except ImportError:
        pass
    text = str(exc).lower().replace("_", "")
    if any(marker in text for marker in _PERMANENT_ERROR_MARKERS):
        return False
    return any(marker in text for marker in _RETRYABLE_MARKERS)


def _reset_clients_if_connection_error(exc: Exception) -> None:
    """Force fresh HTTP clients (and connection pools) after a connection
    error, rather than reusing whatever pooled connection just failed.

    Observed live during a very long run: once a client's underlying
    connection pool picks up one bad connection (e.g. a corporate proxy
    silently closing an idle keep-alive), the cached client can keep
    reusing that same broken connection, producing an unbroken streak of
    identical APIConnectionErrors across every retry and every subsequent
    problem -- confirmed by the fact that a direct curl to the same
    endpoint succeeded instantly while the long-running process kept
    failing. A manual process restart cleared it (fresh client, fresh
    pool); this does the same thing automatically, mid-run.
    """
    try:
        from openai import APIConnectionError
    except ImportError:
        return
    if isinstance(exc, APIConnectionError):
        _openai_client.cache_clear()
        _openrouter_client.cache_clear()


def _with_rate_limit_retry(fn, *, max_attempts: int = 5, base_delay: float = 15.0):
    """Retry fn() on rate-limit / transient-network errors with linear backoff.
    Re-raises anything else."""
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - re-raised below if not retryable
            if not _is_retryable_error(exc):
                raise
            _reset_clients_if_connection_error(exc)
            last_exc = exc
            delay = base_delay * (attempt + 1)
            print(
                f"  retry {attempt + 1}/{max_attempts} after {type(exc).__name__}: "
                f"{str(exc)[:200]!r} (sleeping {delay:.0f}s)",
                flush=True,
            )
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def _parse_score(text: str) -> float:
    # Take the LAST number in the response, not the first: prompts ask for
    # "only the number," but reasoning-tuned models often explain themselves
    # anyway (e.g. restating a year from the query before giving the actual
    # confidence), and the first number in that case is the wrong one.
    matches = _NUMBER_RE.findall(text)
    return max(0.0, min(1.0, float(matches[-1]))) if matches else 0.5


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()


def _stable_seed(prompt: str) -> int:
    """Deterministic seed derived from prompt content.

    generate_* calls pass an explicit seed (0..n-1) for candidate diversity.
    score_*/judge_* calls don't have a natural seed of their own, but still
    need to be as reproducible as the provider allows: the same prompt
    should always get the same seed, so re-running a pipeline over an
    unchanged candidate set doesn't silently reshuffle confidence/judge
    values on providers that honor `seed` (OpenAI, OpenRouter).
    """
    return zlib.crc32(prompt.encode("utf-8"))


@lru_cache(maxsize=1)
def _openai_client():
    from openai import OpenAI

    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@lru_cache(maxsize=1)
def _gemini_client():
    from google import genai

    return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


@lru_cache(maxsize=1)
def _openrouter_client():
    from openai import OpenAI

    return OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")


def _openai_complete(prompt: str, *, seed: int | None = None) -> str:
    resolved_seed = seed if seed is not None else _stable_seed(prompt)

    def call() -> str:
        resp = _openai_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            seed=resolved_seed,
        )
        return (resp.choices[0].message.content or "").strip()

    return _with_rate_limit_retry(lambda: _call_with_stall_timeout(call))


def _gemini_complete(prompt: str) -> str:
    def call() -> str:
        resp = _gemini_client().models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return (resp.text or "").strip()

    return _with_rate_limit_retry(lambda: _call_with_stall_timeout(call))


def _openrouter_complete(prompt: str, *, seed: int | None = None, model: str | None = None) -> str:
    resolved_seed = seed if seed is not None else _stable_seed(prompt)
    resolved_model = model or OPENROUTER_MODEL

    def call() -> str:
        resp = _openrouter_client().chat.completions.create(
            model=resolved_model,
            messages=[{"role": "user", "content": prompt}],
            seed=resolved_seed,
        )
        # OpenRouter returns HTTP 200 with no `choices` and an `error` field
        # when the upstream (free-tier) provider is saturated, instead of a
        # 429 the SDK would raise on its own.
        if not resp.choices:
            raise RuntimeError(f"OpenRouter error (treated as rate limit): {resp.error}")
        return (resp.choices[0].message.content or "").strip()

    return _with_rate_limit_retry(lambda: _call_with_stall_timeout(call))


# --- generation -------------------------------------------------------


def openai_generate(query: str, seed: int) -> str:
    return _openai_complete(query, seed=seed)


def gemini_generate(query: str, seed: int) -> str:
    # Gemini has no seed parameter; sampling variance across calls stands in
    # for the seed sweep used with OpenAI.
    return _gemini_complete(query)


def openrouter_generate(query: str, seed: int, model: str | None = None) -> str:
    return _openrouter_complete(query, seed=seed, model=model)


def openrouter_heterogeneous_backends(model_ids: list[str]) -> list[tuple[str, Callable[[str, int], str]]]:
    """(model_id, generate_fn) pairs for generate_candidates_heterogeneous,
    one real OpenRouter model per backend rather than one model resampled N
    times. Built to test whether candidate diversity -- not judge accuracy
    (see docs/reward_bench_preregistration.md, which ruled the judge out as
    the bottleneck) -- is what's suppressing disagreement on every
    same-model benchmark run so far (Tracks A-C).
    """
    return [
        (model_id, lambda query, seed, _model=model_id: openrouter_generate(query, seed, model=_model))
        for model_id in model_ids
    ]


# --- confidence scoring -------------------------------------------------

_CONFIDENCE_PROMPT = (
    "Query: {query}\n\nAnswer: {text}\n\n"
    "Rate your confidence that this answer is correct, as a single number "
    "between 0.0 and 1.0. Reply with only the number."
)


def openai_score(query: str, text: str) -> float:
    prompt = _CONFIDENCE_PROMPT.format(query=query, text=text)
    return _parse_score(_openai_complete(prompt))


def gemini_score(query: str, text: str) -> float:
    prompt = _CONFIDENCE_PROMPT.format(query=query, text=text)
    return _parse_score(_gemini_complete(prompt))


def openrouter_score(query: str, text: str) -> float:
    prompt = _CONFIDENCE_PROMPT.format(query=query, text=text)
    return _parse_score(_openrouter_complete(prompt))


# --- pairwise judging -----------------------------------------------------


def _judge_prompt(query: str, text_a: str, text_b: str) -> str:
    template = _load_prompt("judge_prompt.txt")
    return template.format(query=query, text_a=text_a, text_b=text_b)


def openai_judge(query: str, text_a: str, text_b: str) -> float:
    return _parse_score(_openai_complete(_judge_prompt(query, text_a, text_b)))


def gemini_judge(query: str, text_a: str, text_b: str) -> float:
    return _parse_score(_gemini_complete(_judge_prompt(query, text_a, text_b)))


def openrouter_judge(query: str, text_a: str, text_b: str) -> float:
    return _parse_score(_openrouter_complete(_judge_prompt(query, text_a, text_b)))
