"""Pairwise comparison matrix via permutation self-consistency.

For each unordered pair (i, j), the judge is asked twice — once as
(i, j) and once as (j, i) — and the two votes are averaged. This cancels
positional bias (judges tend to favor whichever answer comes first/last),
per Permutation Self-Consistency (Tang et al., 2024).
"""

from __future__ import annotations

from collections.abc import Callable

from .core import Candidate

# judge_fn(query, text_a, text_b) -> weight in [0, 1] that a beats b
JudgeFn = Callable[[str, str, str], float]


def build_pairwise_matrix(
    query: str, candidates: list[Candidate], judge_fn: JudgeFn
) -> dict[tuple[str, str], float]:
    """Return W[(i, j)] = averaged, position-debiased weight that i beats j."""
    weights: dict[tuple[str, str], float] = {}
    for a in candidates:
        for b in candidates:
            if a.id == b.id:
                continue
            forward = judge_fn(query, a.text, b.text)
            backward = 1.0 - judge_fn(query, b.text, a.text)
            weights[(a.id, b.id)] = (forward + backward) / 2.0
    return weights
