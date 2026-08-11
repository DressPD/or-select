from __future__ import annotations

import unittest

from scripts.gsm8k_benchmark import _accuracy_summary


def _valid_row(correct: bool) -> dict:
    return {
        "query": "q",
        "ground_truth": 1.0,
        "or_select": {"answer": 1.0 if correct else 2.0, "correct": correct},
        "self_consistency": {"answer": 1.0 if correct else 2.0, "correct": correct, "had_majority": True},
        "greedy": {"answer": 1.0 if correct else 2.0, "correct": correct},
    }


def _failed_row() -> dict:
    return {
        "query": "q",
        "ground_truth": 1.0,
        "error": "NotFoundError: simulated",
        "or_select": {"answer": None, "correct": False},
        "self_consistency": {"answer": None, "correct": False, "had_majority": False},
        "greedy": {"answer": None, "correct": False},
    }


class AccuracySummaryTest(unittest.TestCase):
    def test_failed_problems_excluded_from_accuracy_denominator(self) -> None:
        # 2 correct, 1 failed-to-grade -- accuracy must be 2/2 = 100%, not 2/3.
        results = [_valid_row(True), _valid_row(True), _failed_row()]
        summary = _accuracy_summary(results)
        self.assertEqual(summary["n_total"], 3)
        self.assertEqual(summary["n_valid"], 2)
        self.assertEqual(summary["n_failed"], 1)
        self.assertEqual(summary["accuracy_of_valid"]["or_select"], 1.0)

    def test_all_failed_gives_empty_accuracy_not_a_crash(self) -> None:
        summary = _accuracy_summary([_failed_row(), _failed_row()])
        self.assertEqual(summary["n_valid"], 0)
        self.assertEqual(summary["accuracy_of_valid"], {})

    def test_mixed_correctness_among_valid_problems(self) -> None:
        results = [_valid_row(True), _valid_row(False), _failed_row()]
        summary = _accuracy_summary(results)
        self.assertEqual(summary["accuracy_of_valid"]["or_select"], 0.5)


if __name__ == "__main__":
    unittest.main()
