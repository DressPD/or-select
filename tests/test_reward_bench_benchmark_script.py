from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.reward_bench_benchmark import _judge_fn_for, run_benchmark


class JudgeFnForTest(unittest.TestCase):
    def test_openrouter_mixed_binds_the_given_model(self) -> None:
        with patch("or_select.providers.openrouter_judge", return_value=0.9) as judge:
            fn = _judge_fn_for("openrouter_mixed", model="model-a")
            score = fn("query", "chosen text", "rejected text")
        self.assertEqual(score, 0.9)
        judge.assert_called_once_with("query", "chosen text", "rejected text", model="model-a")


class HeterogeneousRoundRobinTest(unittest.TestCase):
    # Mirrors pipeline.py's openrouter_heterogeneous_backends round-robin
    # pattern (one real model per slot), applied here per ROW since each
    # RewardBench row is a single fixed (chosen, rejected) pair rather than
    # N generated candidates.

    def setUp(self) -> None:
        self.rows = [
            {"id": i, "subset": "alpacaeval-easy", "prompt": "p", "chosen": "c", "rejected": "r"} for i in range(5)
        ]
        self.tmpdir = tempfile.TemporaryDirectory()
        self.output = Path(self.tmpdir.name) / "out.json"
        self.models = ["model-a", "model-b", "model-c"]

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_each_row_gets_a_distinct_model_round_robin(self) -> None:
        # random.randrange is pinned to 0 so the round-robin's starting
        # offset is reproducible here; test_relaunch_offset_varies below
        # covers the offset itself.
        with patch("or_select.pipeline.OPENROUTER_MIXED_MODELS", self.models), patch(
            "or_select.providers.openrouter_judge", return_value=1.0
        ), patch("scripts.reward_bench_benchmark.random.randrange", return_value=0):
            results = run_benchmark(self.rows, "openrouter_mixed", self.output, resume=False, retry_failures=False)
        used_models = [r["judge_model"] for r in results]
        self.assertEqual(used_models, ["model-a", "model-b", "model-c", "model-a", "model-b"])

    def test_relaunch_offset_varies_a_stuck_rows_judge_model(self) -> None:
        # The bug this covers: a row's judge model was a pure function of
        # its position, so a row stuck on an underperforming model (live
        # evidence: RewardBench ids 4678/4681, StallTimeout/APITimeoutError
        # on every relaunch) had zero chance of a different outcome no
        # matter how many times it was retried. Different random offsets
        # across two "relaunches" must route the same row to a different
        # model.
        with patch("or_select.pipeline.OPENROUTER_MIXED_MODELS", self.models), patch(
            "or_select.providers.openrouter_judge", return_value=1.0
        ):
            with patch("scripts.reward_bench_benchmark.random.randrange", return_value=0):
                first = run_benchmark(self.rows[:1], "openrouter_mixed", self.output, resume=False, retry_failures=False)
            with patch("scripts.reward_bench_benchmark.random.randrange", return_value=1):
                second = run_benchmark(self.rows[:1], "openrouter_mixed", self.output, resume=False, retry_failures=False)
        self.assertNotEqual(first[0]["judge_model"], second[0]["judge_model"])

    def test_homogeneous_runs_do_not_record_a_judge_model(self) -> None:
        with patch("or_select.providers.openrouter_judge", return_value=1.0):
            results = run_benchmark(self.rows, "openrouter", self.output, resume=False, retry_failures=False)
        self.assertTrue(all("judge_model" not in r for r in results))

    def test_retry_failures_still_works_in_heterogeneous_mode(self) -> None:
        calls = {"n": 0}

        def flaky(query, a, b, model=None):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise RuntimeError("simulated")
            return 1.0

        with patch("or_select.pipeline.OPENROUTER_MIXED_MODELS", self.models), patch(
            "or_select.providers.openrouter_judge", side_effect=flaky
        ), patch("scripts.reward_bench_benchmark.random.randrange", return_value=0):
            first = run_benchmark(self.rows[:2], "openrouter_mixed", self.output, resume=False, retry_failures=False)
            self.output.write_text(json.dumps({"results": first}))
            self.assertTrue(all("error" in r for r in first))

            second = run_benchmark(self.rows[:2], "openrouter_mixed", self.output, resume=True, retry_failures=True)
        self.assertTrue(all("error" not in r for r in second))
        self.assertEqual([r["judge_model"] for r in second], ["model-a", "model-b"])


if __name__ == "__main__":
    unittest.main()
