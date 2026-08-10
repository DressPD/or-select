"""Non-OR baselines, computed from an already-generated candidate set.

These exist purely for comparison against or_select.selection.select_best
(docs/methodology.md's "Baselines to compare against"). None of them make
an API call: they operate on candidates already produced by the pipeline,
so comparing OR-Select's winner against these is free.
"""

from __future__ import annotations

from .core import Candidate


def self_consistency_winner(candidates: list[Candidate]) -> tuple[Candidate, bool]:
    """Pick the majority-text candidate (classic self-consistency voting).

    Returns (winner, had_majority). had_majority is False when no text
    repeats (every candidate is unique) -- in that case "winner" is just
    the first candidate by seed order, an arbitrary tie-break, not a
    principled choice. This degenerate case is itself a finding: self-
    consistency alone is undefined once candidates stop clustering.
    """
    if not candidates:
        raise ValueError("no candidates to select from")
    normalized = [c.text.strip() for c in candidates]
    counts: dict[str, int] = {}
    for text in normalized:
        counts[text] = counts.get(text, 0) + 1
    best_text = max(counts, key=lambda t: counts[t])
    had_majority = counts[best_text] > 1
    winner = next(c for c, t in zip(candidates, normalized) if t == best_text)
    return winner, had_majority


def greedy_single_sample(candidates: list[Candidate]) -> Candidate:
    """The 'just take one sample, no ensemble at all' baseline: seed 0."""
    if not candidates:
        raise ValueError("no candidates to select from")
    return min(candidates, key=lambda c: c.metadata.get("seed", 0))
