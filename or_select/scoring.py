"""Calibrated confidence scoring for candidates.

score_fn is any callable that returns a confidence in [0, 1] for a
(query, candidate_text) pair — e.g. log-likelihood, a self-rating prompt,
or an external validator. Kept pluggable so the OR core never depends on
a specific scoring method.
"""

from __future__ import annotations

from collections.abc import Callable

from .core import Candidate

ScoreFn = Callable[[str, str], float]


def score_candidates(query: str, candidates: list[Candidate], score_fn: ScoreFn) -> list[Candidate]:
    for candidate in candidates:
        candidate.confidence = max(0.0, min(1.0, score_fn(query, candidate.text)))
        candidate.cost = len(candidate.text.split())
    return candidates
