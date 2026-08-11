from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from or_select.core import Candidate, SelectionResult
from scripts.gsm8k_benchmark import _accuracy_summary, run_benchmark


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


def _ok_result(query: str, n: int, provider: str) -> SelectionResult:
    c = Candidate(id="c0", text="42", source_model="m", confidence=1.0, cost=1)
    return SelectionResult(query=query, winner_id="c0", winner_text="42", scores={"c0": 1.0}, candidates=[c])


class RetryFailuresTest(unittest.TestCase):
    def setUp(self) -> None:
        self.problems = [{"query": "q_ok", "ground_truth": 42.0}, {"query": "q_fail", "ground_truth": 42.0}]
        self.tmpdir = tempfile.TemporaryDirectory()
        self.output = Path(self.tmpdir.name) / "out.json"

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _run(self, pipeline_fn, **kwargs) -> list[dict]:
        with patch("scripts.gsm8k_benchmark.run_pipeline", side_effect=pipeline_fn):
            return run_benchmark(self.problems, 1, "placeholder", self.output, **kwargs)

    def test_plain_resume_leaves_a_failed_row_failed(self) -> None:
        def failing(query, n, provider):
            if query.startswith("q_fail"):
                raise RuntimeError("simulated")
            return _ok_result(query)

        first = self._run(failing, resume=False)
        self.output.write_text(json.dumps({"results": first}))
        self.assertTrue(any("error" in r for r in first))

        calls = []

        def track_and_fail(query, n, provider):
            calls.append(query)
            return failing(query, n, "placeholder")

        second = self._run(track_and_fail, resume=True)
        self.assertEqual(calls, [], "resume without --retry-failures must not re-call a failed problem")
        self.assertTrue(any("error" in r for r in second))

    def test_retry_failures_re_attempts_and_can_succeed(self) -> None:
        def always_fails(query, n, provider):
            raise RuntimeError("simulated")

        first = self._run(always_fails, resume=False)
        self.output.write_text(json.dumps({"results": first}))
        self.assertTrue(all("error" in r for r in first))

        # Provider "recovers" on the next attempt.
        second = self._run(_ok_result, resume=True, retry_failures=True)
        self.assertTrue(all("error" not in r for r in second))


if __name__ == "__main__":
    unittest.main()
