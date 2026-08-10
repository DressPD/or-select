"""Sample N candidate answers for a query.

Backend-agnostic: plug in any callable that takes (query, seed) -> text.
Kept separate from scoring/selection so generation can stay probabilistic
while everything downstream is deterministic.
"""

from __future__ import annotations

from collections.abc import Callable

from .core import Candidate, DEFAULT_N_CANDIDATES

GenerateFn = Callable[[str, int], str]


def generate_candidates(
    query: str,
    generate_fn: GenerateFn,
    n: int = DEFAULT_N_CANDIDATES,
    source_model: str = "unknown",
    seeds: list[int] | None = None,
) -> list[Candidate]:
    """Sample n candidates for query using generate_fn(query, seed) -> text."""
    seeds = seeds or list(range(n))
    candidates = []
    for i, seed in enumerate(seeds[:n]):
        text = generate_fn(query, seed)
        candidates.append(
            Candidate(id=f"c{i}", text=text, source_model=source_model, metadata={"seed": seed})
        )
    return candidates
