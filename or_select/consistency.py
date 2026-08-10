"""Deterministic self-consistency scoring -- no LLM call.

consistency_i = (# candidates whose normalized text matches i's, including
itself) / N

This is the classic self-consistency-voting signal (the majority answer
wins) made exact and OR-computable: a candidate that many independent
samples converged on scores higher, purely by counting, with zero API
calls and zero risk of provider-side non-determinism. Used as an
objective term in or_select/selection.py alongside the LLM-judged
quality score, not as a replacement for it -- consistency only captures
agreement frequency, not semantic quality, so it degenerates to a flat
1/N for a set of candidates that never happen to repeat.
"""

from __future__ import annotations

from .core import Candidate


def compute_consistency(candidates: list[Candidate]) -> dict[str, float]:
    normalized = [c.text.strip() for c in candidates]
    counts: dict[str, int] = {}
    for text in normalized:
        counts[text] = counts.get(text, 0) + 1
    n = len(candidates)
    return {c.id: counts[text] / n for c, text in zip(candidates, normalized)}
