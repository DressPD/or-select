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
    """Return W[(i, j)] = averaged, position-debiased weight that i beats j.

    Each unordered pair is judged in both text orders exactly once. W[(j, i)]
    is derived as 1 - W[(i, j)] rather than re-judged: by construction the
    forward/backward average makes the two exact complements, so judging the
    reverse pair again would just repeat the same two API calls for the same
    result (halves the judge call count for a given N).
    """
    weights: dict[tuple[str, str], float] = {}
    for i, a in enumerate(candidates):
        for b in candidates[i + 1 :]:
            forward = judge_fn(query, a.text, b.text)
            backward = 1.0 - judge_fn(query, b.text, a.text)
            w_ab = (forward + backward) / 2.0
            weights[(a.id, b.id)] = w_ab
            weights[(b.id, a.id)] = 1.0 - w_ab
    return weights
