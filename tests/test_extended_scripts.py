from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from or_select import providers
from or_select.generate import ValidityExhausted
from scripts import gpqa_benchmark, math_benchmark

SCRIPTS = [gpqa_benchmark, math_benchmark]
POOL = [
    "nvidia/nemotron-3.5-lightning-20260807:free",
    "poolside/laguna-s-2.1:free",
    "cohere/north-mini-code:free",
]
METHODS = ("or_select", "self_consistency", "greedy", "kemeny_young")


def _valid(query: str, correct: bool) -> dict:
    return {"query": query, "ground_truth": "A", **{m: {"answer": "A", "correct": correct} for m in METHODS}}


def _truncated(query: str, seed: int) -> dict:
    return {
        "query": query,
        "ground_truth": "A",
        "error": f"ValidityExhausted: seed={seed} no valid answer in 3 attempts, output truncated at the token cap",
        "truncated": True,
        "truncated_at_tokens": 32768,
        "truncation_attempts": 1,
    }


class FailedRowCapTest(unittest.TestCase):
    def test_stamps_the_cap_the_failing_call_ran_with(self) -> None:
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                exc = ValidityExhausted(0, "cut", truncated=True, cap=64000)
                row = script._failed_row({"query": "q", "ground_truth": "A"}, exc)
                self.assertEqual(row["truncated_at_tokens"], 64000)

    def test_default_stamp_is_the_global_cap(self) -> None:
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                exc = ValidityExhausted(0, "cut", truncated=True)
                row = script._failed_row({"query": "q", "ground_truth": "A"}, exc)
                self.assertEqual(row["truncated_at_tokens"], 32768)


class AccuracySummaryTest(unittest.TestCase):
    def test_main_protocol_accuracy_leaves_out_rescued_rows(self) -> None:
        rescued = {**_valid("r", True), "extended_cap_pass": True}
        results = [_valid("a", True), _valid("b", False), rescued, _truncated("t", 0)]
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                summary = script._accuracy_summary(results)
                self.assertEqual(summary["n_valid"], 3)
                self.assertEqual(summary["n_failed"], 1)
                self.assertEqual(summary["n_extended_rescued"], 1)
                self.assertAlmostEqual(summary["accuracy_of_valid"]["or_select"], 2 / 3)
                self.assertAlmostEqual(summary["accuracy_of_valid_main_protocol"]["or_select"], 1 / 2)

    def test_no_extended_rows_means_the_two_accuracies_agree(self) -> None:
        results = [_valid("a", True), _valid("b", False)]
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                summary = script._accuracy_summary(results)
                self.assertEqual(summary["n_extended_rescued"], 0)
                self.assertEqual(summary["accuracy_of_valid"], summary["accuracy_of_valid_main_protocol"])


class RunExtendedBenchmarkTest(unittest.TestCase):
    def setUp(self) -> None:
        self._cap = providers.MAX_OUTPUT_TOKENS
        self._stream = providers.STREAM_TIMEOUT_SECONDS
        self.tmp = tempfile.TemporaryDirectory()
        self.output = Path(self.tmp.name) / "out.json"

    def tearDown(self) -> None:
        providers.MAX_OUTPUT_TOKENS = self._cap
        providers.STREAM_TIMEOUT_SECONDS = self._stream
        self.tmp.cleanup()

    def _store(self, script, rows: list[dict]) -> None:
        script._write_output(self.output, rows, 3, "openrouter_mixed")

    def test_missing_output_is_refused(self) -> None:
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                with self.assertRaises(SystemExit):
                    script.run_extended_benchmark([], 3, "openrouter_mixed", self.output, 65536)

    def test_untried_problems_refuse_the_pass_and_leave_the_file_alone(self) -> None:
        problems = [{"query": "t", "ground_truth": "A"}, {"query": "new", "ground_truth": "A"}]
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                self._store(script, [_truncated("t", 0)])
                before = self.output.read_text()
                with self.assertRaises(SystemExit):
                    script.run_extended_benchmark(problems, 3, "openrouter_mixed", self.output, 65536)
                self.assertEqual(self.output.read_text(), before)

    def test_only_the_truncated_row_is_regraded_and_flagged_on_disk(self) -> None:
        problems = [
            {"query": "ok", "ground_truth": "A"},
            {"query": "t", "ground_truth": "A"},
            {"query": "lag", "ground_truth": "A"},
        ]
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                self._store(script, [_valid("ok", True), _truncated("t", 0), _truncated("lag", 1)])
                with patch.object(script, "_grade_one", side_effect=lambda p, n, prov: _valid(p["query"], True)) as grade:
                    script.run_extended_benchmark(problems, 3, "openrouter_mixed", self.output, 65536)
                self.assertEqual([c.args[0]["query"] for c in grade.call_args_list], ["t"])
                saved = json.loads(self.output.read_text())
                by_q = {r["query"]: r for r in saved["results"]}
                self.assertNotIn("extended_cap_pass", by_q["ok"])
                self.assertTrue(by_q["t"]["extended_cap_pass"])
                self.assertEqual(by_q["t"]["main_protocol"]["truncated_at_tokens"], 32768)
                self.assertNotIn("extended_cap_pass", by_q["lag"])  # laguna cannot go higher
                self.assertEqual(saved["n_extended_rescued"], 1)
                self.assertEqual(saved["n_valid"], 2)
                providers.MAX_OUTPUT_TOKENS = 32768
                providers.STREAM_TIMEOUT_SECONDS = 3600.0


if __name__ == "__main__":
    unittest.main()
