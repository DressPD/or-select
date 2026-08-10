from __future__ import annotations

import unittest

from or_select.baselines import greedy_single_sample, self_consistency_winner
from or_select.core import Candidate


class SelfConsistencyBaselineTest(unittest.TestCase):
    def test_majority_text_wins_and_reports_majority(self) -> None:
        candidates = [
            Candidate(id="a", text="Paris", source_model="m", metadata={"seed": 0}),
            Candidate(id="b", text="Paris", source_model="m", metadata={"seed": 1}),
            Candidate(id="c", text="Berlin", source_model="m", metadata={"seed": 2}),
        ]
        winner, had_majority = self_consistency_winner(candidates)
        self.assertEqual(winner.text, "Paris")
        self.assertTrue(had_majority)

    def test_all_unique_reports_no_majority(self) -> None:
        candidates = [Candidate(id=f"c{i}", text=f"answer {i}", source_model="m", metadata={"seed": i}) for i in range(3)]
        winner, had_majority = self_consistency_winner(candidates)
        self.assertFalse(had_majority)
        self.assertEqual(winner.id, "c0")  # arbitrary tie-break: first by seed order

    def test_raises_on_empty(self) -> None:
        with self.assertRaises(ValueError):
            self_consistency_winner([])


class GreedyBaselineTest(unittest.TestCase):
    def test_picks_lowest_seed(self) -> None:
        candidates = [
            Candidate(id="a", text="X", source_model="m", metadata={"seed": 2}),
            Candidate(id="b", text="Y", source_model="m", metadata={"seed": 0}),
            Candidate(id="c", text="Z", source_model="m", metadata={"seed": 1}),
        ]
        self.assertEqual(greedy_single_sample(candidates).id, "b")

    def test_raises_on_empty(self) -> None:
        with self.assertRaises(ValueError):
            greedy_single_sample([])


if __name__ == "__main__":
    unittest.main()
