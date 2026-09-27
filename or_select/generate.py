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


class ValidityExhausted(RuntimeError):
    """All VALIDITY_RETRY_ATTEMPTS attempts for one seed produced text that
    failed validity_fn. Carries the last attempt's full text (not just its
    length) so a caller can log/persist it for diagnosis -- previously this
    was discarded entirely along with the other successful candidates
    already generated for the same problem, leaving no way to tell why
    extraction kept failing."""

    def __init__(self, seed: int, last_response: str):
        self.seed = seed
        self.last_response = last_response
        super().__init__(
            f"seed={seed} produced no valid candidate in {VALIDITY_RETRY_ATTEMPTS} attempts "
            f"(last response: {len(last_response)} chars)"
        )


def _generate_valid(generate_fn: GenerateFn, query: str, seed: int, validity_fn: ValidityFn | None) -> str:
    if validity_fn is None:
        return generate_fn(query, seed)
    text = ""
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
        text = generate_fn(query, attempt_seed)
        if validity_fn(text):
            return text
    raise ValidityExhausted(seed, text)


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
