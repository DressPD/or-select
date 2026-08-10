from __future__ import annotations

import unittest

from or_select.consistency import compute_consistency
from or_select.core import Candidate


class ConsistencyTest(unittest.TestCase):
    def test_majority_text_scores_higher(self) -> None:
        candidates = [
            Candidate(id="a", text="Paris", source_model="m"),
            Candidate(id="b", text="Paris", source_model="m"),
            Candidate(id="c", text="Berlin", source_model="m"),
        ]
        scores = compute_consistency(candidates)
        self.assertAlmostEqual(scores["a"], 2 / 3)
        self.assertAlmostEqual(scores["b"], 2 / 3)
        self.assertAlmostEqual(scores["c"], 1 / 3)

    def test_all_unique_gives_flat_uniform_scores(self) -> None:
        candidates = [Candidate(id=f"c{i}", text=f"answer {i}", source_model="m") for i in range(4)]
        scores = compute_consistency(candidates)
        self.assertTrue(all(abs(v - 0.25) < 1e-9 for v in scores.values()))

    def test_whitespace_is_normalized(self) -> None:
        candidates = [
            Candidate(id="a", text="Paris", source_model="m"),
            Candidate(id="b", text="  Paris  ", source_model="m"),
        ]
        scores = compute_consistency(candidates)
        self.assertAlmostEqual(scores["a"], 1.0)
        self.assertAlmostEqual(scores["b"], 1.0)


if __name__ == "__main__":
    unittest.main()
