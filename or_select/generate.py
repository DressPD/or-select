"""Sample N candidate answers for a query.

Backend-agnostic: plug in any callable that takes (query, seed) -> text.
Kept separate from scoring/selection so generation can stay probabilistic
while everything downstream is deterministic.
"""

from __future__ import annotations

from collections.abc import Callable

from .core import Candidate, DEFAULT_N_CANDIDATES

GenerateFn = Callable[[str, int], str]
ValidityFn = Callable[[str], bool]

VALIDITY_RETRY_ATTEMPTS = 3
# A call can come back non-empty and within STALL_TIMEOUT_SECONDS/
# MAX_OUTPUT_TOKENS (providers.py already retries the empty-text and
# runaway-length failure modes) and still be garbage for this domain's
# purposes -- e.g. GPQA text that never reaches an ANSWER:/\boxed{} marker.
# That used to be silently accepted as one "valid" graded candidate; per an
# explicit request to treat it the same way empty completions already are
# (a failure to retry, not a measured outcome), a caller can now pass
# validity_fn and have a rejected candidate re-sampled up to
# VALIDITY_RETRY_ATTEMPTS times before giving up. Kept domain-agnostic here
# (no GPQA/MATH-specific import) -- callers supply whatever predicate fits
# their answer format.


class TruncatedOutput(Exception):
    """The backend stopped because it hit the output-token cap, so the text
    is a cut-off fragment, not an answer. Carries that fragment."""

    def __init__(self, text: str, cap: int | None = None):
        self.text = text
        # The max_tokens the call actually ran with (the model's effective
        # cap), so a failed row can record the cap it was truncated at.
        self.cap = cap
        super().__init__(f"output truncated at the token cap ({len(text)} chars)")


class ValidityExhausted(RuntimeError):
    """All VALIDITY_RETRY_ATTEMPTS attempts for one seed produced text that
    failed validity_fn; truncated=True when at least one of those attempts was
    cut off at the output token cap. Carries the last attempt's full text
    (not just its length) so a caller can log/persist it for diagnosis --
    previously this was discarded entirely along with the other successful
    candidates already generated for the same problem, leaving no way to
    tell why extraction kept failing."""

    def __init__(self, seed: int, last_response: str, truncated: bool = False, cap: int | None = None):
        self.seed = seed
        self.last_response = last_response
        self.truncated = truncated
        # Largest effective token cap a truncated attempt ran with, if known.
        self.cap = cap
        if truncated:
            super().__init__(
                f"seed={seed} no valid answer in {VALIDITY_RETRY_ATTEMPTS} attempts, "
                f"output truncated at the token cap in at least one "
                f"(last response: {len(last_response)} chars)"
            )
        else:
            super().__init__(
                f"seed={seed} produced no valid candidate in {VALIDITY_RETRY_ATTEMPTS} attempts "
                f"(last response: {len(last_response)} chars)"
            )


MAX_TRUNCATION_ATTEMPTS = 1


def is_settled_truncation(row: dict, current_cap: int, max_attempts: int = MAX_TRUNCATION_ATTEMPTS) -> bool:
    """A failed row that hit the output-token cap at `current_cap` or higher
    on `max_attempts` separate attempts. Truncation is partly random (a
    32768-token test finished 1 of 6 previously-truncated rows on a fresh
    sample), so a truncated row is reprocessed on resume until it has been
    truncated that many times; rows flagged before attempts were counted
    count as one attempt."""
    return (
        bool(row.get("truncated"))
        and row.get("truncated_at_tokens", 0) >= current_cap
        and row.get("truncation_attempts", 1) >= max_attempts
    )


def truncation_attempts_so_far(previous_rows: list[dict], query: str) -> int:
    """How many times `query` has already failed by truncation (0 if never)."""
    for r in previous_rows:
        if r.get("query") == query and "error" in r and r.get("truncated"):
            return r.get("truncation_attempts", 1)
    return 0


def _generate_valid(generate_fn: GenerateFn, query: str, seed: int, validity_fn: ValidityFn | None) -> str:
    if validity_fn is None:
        return generate_fn(query, seed)
    text = ""
    truncated = False
    trunc_cap: int | None = None
    for attempt in range(VALIDITY_RETRY_ATTEMPTS):
        # Vary the seed actually sent on each retry. Reusing the identical
        # seed on all 3 attempts meant a backend that honors `seed` for
        # reproducibility would deterministically repeat the exact same
        # invalid completion 3x -- burning the whole retry budget for zero
        # additional chance of success. The seed recorded on the resulting
        # Candidate (in generate_candidates below) is still the caller's
        # original seed, unaffected by this -- only what's sent to the API
        # on retries changes.
        attempt_seed = seed if attempt == 0 else seed + attempt * 10_000
        try:
            text = generate_fn(query, attempt_seed)
        except TruncatedOutput as exc:
            # A completion cut off at the token cap has no final answer, like
            # any other output the validity predicate rejects. Measured:
            # whether a given prompt loops to the cap is largely stochastic
            # (the same AIME prompt hit 16K tokens in one draw and solved in
            # 5K in the next), so it gets a freshly seeded re-sample from the
            # same budget instead of failing the slot on the first cut-off.
            truncated = True
            text = exc.text
            if exc.cap is not None:
                trunc_cap = max(trunc_cap or 0, exc.cap)
            continue
        if validity_fn(text):
            return text
    raise ValidityExhausted(seed, text, truncated=truncated, cap=trunc_cap)


def generate_candidates(
    query: str,
    generate_fn: GenerateFn,
    n: int = DEFAULT_N_CANDIDATES,
    source_model: str = "unknown",
    seeds: list[int] | None = None,
    validity_fn: ValidityFn | None = None,
) -> list[Candidate]:
    """Sample n candidates for query using generate_fn(query, seed) -> text."""
    seeds = seeds or list(range(n))
    candidates = []
    for i, seed in enumerate(seeds[:n]):
        text = _generate_valid(generate_fn, query, seed, validity_fn)
        candidates.append(
            Candidate(id=f"c{i}", text=text, source_model=source_model, metadata={"seed": seed})
        )
    return candidates


def generate_candidates_heterogeneous(
    query: str,
    backends: list[tuple[str, GenerateFn]],
    n: int = DEFAULT_N_CANDIDATES,
    validity_fn: ValidityFn | None = None,
) -> list[Candidate]:
    """Round-robin n candidates across multiple (model_name, generate_fn) backends.

    Used to validate OR-Select across providers (e.g. OpenAI + Gemini) instead
    of just different seeds of one model.
    """
    if not backends:
        raise ValueError("no backends given")
    candidates = []
    for i in range(n):
        name, fn = backends[i % len(backends)]
        text = _generate_valid(fn, query, i, validity_fn)
        candidates.append(Candidate(id=f"c{i}", text=text, source_model=name, metadata={"seed": i}))
    return candidates
