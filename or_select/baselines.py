"""Non-OR baselines, computed from an already-generated candidate set.

These exist purely for comparison against or_select.selection.select_best
(docs/methodology.md's "Baselines to compare against"). None of them make
an API call: they operate on candidates already produced by the pipeline,
so comparing OR-Select's winner against these is free.
"""

from __future__ import annotations

from collections.abc import Callable

from .core import Candidate


def self_consistency_winner(
    candidates: list[Candidate], key: Callable[[Candidate], str] | None = None
) -> tuple[Candidate, bool]:
    """Pick the majority candidate (classic self-consistency voting).

    key extracts the value candidates are compared on -- defaults to
    normalized text (exact-answer match). For tasks with a checkable final
    answer distinct from the reasoning text (e.g. GSM8K), pass
    key=lambda c: str(extract_answer(c.text)): two candidates can reach the
    same correct number via different reasoning, which is exactly the case
    Wang et al.'s original self-consistency definition is built around.

    Returns (winner, had_majority). had_majority is False when no key value
    repeats (every candidate is unique under key) -- in that case "winner"
    is just the first candidate by seed order, an arbitrary tie-break, not
    a principled choice. This degenerate case is itself a finding: self-
    consistency alone is undefined once candidates stop clustering.
    """
    if not candidates:
        raise ValueError("no candidates to select from")
    key = key or (lambda c: c.text.strip())
    keys = [key(c) for c in candidates]
    counts: dict[str, int] = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    best_key = max(counts, key=lambda k: counts[k])
    had_majority = counts[best_key] > 1
    winner = next(c for c, k in zip(candidates, keys) if k == best_key)
    return winner, had_majority


def greedy_single_sample(candidates: list[Candidate]) -> Candidate:
    """The 'just take one sample, no ensemble at all' baseline: seed 0."""
    if not candidates:
        raise ValueError("no candidates to select from")
    return min(candidates, key=lambda c: c.metadata.get("seed", 0))
