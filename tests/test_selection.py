from __future__ import annotations

import unittest

from or_select.consistency import compute_consistency
from or_select.core import Candidate
from or_select.pairwise import build_pairwise_matrix
from or_select.selection import aggregate_quality, select_best


class SelectionTest(unittest.TestCase):
    def test_selection_is_deterministic_across_repeated_solves(self) -> None:
        candidates = [
            Candidate(id="a", text="Paris", source_model="m", confidence=0.9, cost=1),
            Candidate(id="b", text="Berlin", source_model="m", confidence=0.5, cost=1),
            Candidate(id="c", text="Paris, the capital of France", source_model="m", confidence=0.8, cost=5),
        ]

        def judge_fn(query: str, text_a: str, text_b: str) -> float:
            return 1.0 if "Paris" in text_a and "Paris" not in text_b else (0.5 if "Paris" in text_a else 0.0)

        pairwise = build_pairwise_matrix("capital of France", candidates, judge_fn)
        quality = aggregate_quality(candidates, pairwise)

        winners = {select_best(candidates, quality)[0] for _ in range(5)}
        self.assertEqual(len(winners), 1, "same inputs must always yield the same winner")

    def test_winner_beats_a_clearly_worse_candidate(self) -> None:
        candidates = [
            Candidate(id="good", text="Paris", source_model="m", confidence=0.95, cost=1),
            Candidate(id="bad", text="I don't know", source_model="m", confidence=0.1, cost=1),
        ]

        def judge_fn(query: str, text_a: str, text_b: str) -> float:
            return 1.0 if text_a == "Paris" else 0.0

        pairwise = build_pairwise_matrix("capital of France", candidates, judge_fn)
        quality = aggregate_quality(candidates, pairwise)
        winner_id, _ = select_best(candidates, quality)
        self.assertEqual(winner_id, "good")

    def test_select_best_raises_on_empty_candidates(self) -> None:
        with self.assertRaises(ValueError):
            select_best([], {})

    def test_consistency_is_optional_and_backward_compatible(self) -> None:
        candidates = [
            Candidate(id="a", text="Paris", source_model="m", confidence=0.9, cost=1),
            Candidate(id="b", text="Berlin", source_model="m", confidence=0.5, cost=1),
        ]

        def judge_fn(query: str, text_a: str, text_b: str) -> float:
            return 1.0 if text_a == "Paris" else 0.0

        pairwise = build_pairwise_matrix("q", candidates, judge_fn)
        quality = aggregate_quality(candidates, pairwise)
        winner_without, _ = select_best(candidates, quality)
        winner_with_none, _ = select_best(candidates, quality, consistency=None)
        self.assertEqual(winner_without, winner_with_none)

    def test_consistency_can_flip_a_close_tie_toward_the_majority_answer(self) -> None:
        # Two candidates say "Paris" (agree with each other), one says
        # "Lutetia" -- an obscure but not-wrong historical name. Quality/
        # confidence alone are set to a near-tie; consistency should push
        # the majority answer over the singleton.
        candidates = [
            Candidate(id="a", text="Paris", source_model="m", confidence=0.7, cost=1),
            Candidate(id="b", text="Paris", source_model="m", confidence=0.7, cost=1),
            Candidate(id="c", text="Lutetia", source_model="m", confidence=0.71, cost=1),
        ]

        def judge_fn(query: str, text_a: str, text_b: str) -> float:
            return 0.5  # judge is indifferent -- all quality scores land at 0.5

        pairwise = build_pairwise_matrix("q", candidates, judge_fn)
        quality = aggregate_quality(candidates, pairwise)
        consistency = compute_consistency(candidates)
        winner_id, _ = select_best(candidates, quality, consistency)
        self.assertIn(winner_id, ("a", "b"))


if __name__ == "__main__":
    unittest.main()
