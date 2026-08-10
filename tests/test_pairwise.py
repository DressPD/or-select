from __future__ import annotations

import unittest

from or_select.core import Candidate
from or_select.pairwise import build_pairwise_matrix


class PairwiseTest(unittest.TestCase):
    def test_judge_call_count_is_not_doubled(self) -> None:
        candidates = [Candidate(id=f"c{i}", text=f"answer {i}", source_model="m") for i in range(5)]
        call_count = 0

        def judge_fn(query: str, text_a: str, text_b: str) -> float:
            nonlocal call_count
            call_count += 1
            return 1.0 if text_a < text_b else 0.0

        build_pairwise_matrix("q", candidates, judge_fn)
        n = len(candidates)
        # Exactly 2 calls per unordered pair (forward + backward), not 2 per
        # ordered pair -- N*(N-1) total, not 2*N*(N-1).
        self.assertEqual(call_count, n * (n - 1))

    def test_reverse_weight_is_exact_complement(self) -> None:
        candidates = [Candidate(id="a", text="A", source_model="m"), Candidate(id="b", text="B", source_model="m")]

        def judge_fn(query: str, text_a: str, text_b: str) -> float:
            return 0.7 if text_a == "A" else 0.3

        weights = build_pairwise_matrix("q", candidates, judge_fn)
        self.assertAlmostEqual(weights[("a", "b")] + weights[("b", "a")], 1.0)

    def test_matches_manual_two_call_computation(self) -> None:
        candidates = [Candidate(id="a", text="A", source_model="m"), Candidate(id="b", text="B", source_model="m")]

        def judge_fn(query: str, text_a: str, text_b: str) -> float:
            return {("A", "B"): 0.8, ("B", "A"): 0.6}[(text_a, text_b)]

        weights = build_pairwise_matrix("q", candidates, judge_fn)
        expected_ab = (0.8 + (1.0 - 0.6)) / 2.0
        self.assertAlmostEqual(weights[("a", "b")], expected_ab)
        self.assertAlmostEqual(weights[("b", "a")], 1.0 - expected_ab)


if __name__ == "__main__":
    unittest.main()
