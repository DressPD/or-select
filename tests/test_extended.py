from __future__ import annotations

import unittest

from or_select import extended, providers
from or_select.generate import TruncatedOutput, ValidityExhausted, generate_candidates

NEMOTRON = "nvidia/nemotron-3.5-lightning-20260807:free"
LAGUNA = "poolside/laguna-s-2.1:free"
COHERE = "cohere/north-mini-code:free"
POOL = [NEMOTRON, LAGUNA, COHERE]


class _RestoreProviderGlobals(unittest.TestCase):
    def setUp(self) -> None:
        self._cap = providers.MAX_OUTPUT_TOKENS
        self._stream = providers.STREAM_TIMEOUT_SECONDS

    def tearDown(self) -> None:
        providers.MAX_OUTPUT_TOKENS = self._cap
        providers.STREAM_TIMEOUT_SECONDS = self._stream


class OutputCapTest(_RestoreProviderGlobals):
    def test_default_cap_is_unchanged_for_every_pool_model(self) -> None:
        self.assertEqual(providers.MAX_OUTPUT_TOKENS, 32768)
        self.assertEqual(providers.STREAM_TIMEOUT_SECONDS, 3600.0)
        for model in POOL:
            self.assertEqual(providers._output_cap(model), 32768)

    def test_extended_cap_is_clamped_per_model(self) -> None:
        extended.configure(65536)
        self.assertEqual(providers._output_cap(NEMOTRON), 65536)
        self.assertEqual(providers._output_cap(COHERE), 64000)
        self.assertEqual(providers._output_cap(LAGUNA), 32768)
        self.assertEqual(providers.STREAM_TIMEOUT_SECONDS, 7200.0)


class TruncationCapRecordedTest(unittest.TestCase):
    def test_exhausted_exception_carries_the_largest_truncation_cap(self) -> None:
        caps = iter([1000, 3000, 2000])

        def gen(query: str, seed: int) -> str:
            raise TruncatedOutput("cut", cap=next(caps))

        with self.assertRaises(ValidityExhausted) as ctx:
            generate_candidates("q", gen, n=1, validity_fn=lambda t: True)
        self.assertTrue(ctx.exception.truncated)
        self.assertEqual(ctx.exception.cap, 3000)

    def test_cap_defaults_to_none_when_the_backend_does_not_say(self) -> None:
        def gen(query: str, seed: int) -> str:
            raise TruncatedOutput("cut")

        with self.assertRaises(ValidityExhausted) as ctx:
            generate_candidates("q", gen, n=1, validity_fn=lambda t: True)
        self.assertIsNone(ctx.exception.cap)


def _trunc_row(query: str, seed: int, cap: int = 32768, attempts: int = 1) -> dict:
    return {
        "query": query,
        "error": f"ValidityExhausted: seed={seed} no valid answer in 3 attempts, output truncated at the token cap",
        "truncated": True,
        "truncated_at_tokens": cap,
        "truncation_attempts": attempts,
    }


class FailingModelTest(unittest.TestCase):
    def test_homogeneous_uses_the_single_model(self) -> None:
        self.assertEqual(extended.failing_model(_trunc_row("q", 2), "openrouter", POOL), providers.OPENROUTER_MODEL)

    def test_mixed_pool_maps_the_failing_seed_round_robin(self) -> None:
        self.assertEqual(extended.failing_model(_trunc_row("q", 0), "openrouter_mixed", POOL), NEMOTRON)
        self.assertEqual(extended.failing_model(_trunc_row("q", 1), "openrouter_mixed", POOL), LAGUNA)
        self.assertEqual(extended.failing_model(_trunc_row("q", 5), "openrouter_mixed", POOL), COHERE)

    def test_unknown_provider_or_missing_seed_gives_none(self) -> None:
        self.assertIsNone(extended.failing_model(_trunc_row("q", 0), "placeholder", POOL))
        self.assertIsNone(extended.failing_model({"error": "boom"}, "openrouter_mixed", POOL))


class SelectTargetsTest(_RestoreProviderGlobals):
    def test_selects_only_truncated_rows_whose_model_can_go_higher(self) -> None:
        extended.configure(65536)
        results = [
            {"query": "valid", "or_select": {"answer": "A", "correct": True}},
            {"query": "api-failure", "error": "APIError: boom"},
            _trunc_row("nemotron", 0),
            _trunc_row("laguna", 1),
            _trunc_row("cohere", 2),
            _trunc_row("cohere-already-extended", 2, cap=64000, attempts=2),
            _trunc_row("nemotron-already-extended", 3, cap=65536, attempts=2),
        ]
        picked = [r["query"] for r in extended.select_targets(results, "openrouter_mixed", POOL)]
        self.assertEqual(picked, ["nemotron", "cohere"])

    def test_nothing_is_selected_at_the_default_cap(self) -> None:
        results = [_trunc_row("a", 0), _trunc_row("b", 2)]
        self.assertEqual(extended.select_targets(results, "openrouter_mixed", POOL), [])


class RunExtendedPassTest(_RestoreProviderGlobals):
    def _problems(self, *queries: str) -> list[dict]:
        return [{"query": q, "ground_truth": "A"} for q in queries]

    def _run(self, results, problems, grade_one, provider="openrouter_mixed"):
        persisted: list[list[dict]] = []
        out = extended.run_extended_pass(
            results,
            problems,
            provider,
            POOL,
            65536,
            grade_one=grade_one,
            failed_row=lambda problem, exc: {
                "query": problem["query"],
                "error": f"{type(exc).__name__}: {exc}",
                **({"truncated": True, "truncated_at_tokens": exc.cap} if getattr(exc, "truncated", False) else {}),
            },
            persist=lambda rows: persisted.append([dict(r) for r in rows]),
        )
        return out, persisted

    def test_refuses_to_run_while_any_problem_is_untried(self) -> None:
        results = [_trunc_row("t", 0)]
        with self.assertRaises(RuntimeError):
            self._run(results, self._problems("t", "never-attempted"), lambda p: {"query": p["query"]})
        self.assertEqual(providers.MAX_OUTPUT_TOKENS, 32768)  # the cap was not raised

    def test_rescued_row_replaces_the_failure_in_place_and_keeps_the_main_record(self) -> None:
        keep = {"query": "ok", "or_select": {"answer": "A", "correct": True}}
        results = [keep, _trunc_row("t", 0), {"query": "also-ok"}]
        out, persisted = self._run(
            results, self._problems("ok", "t", "also-ok"), lambda p: {"query": p["query"], "or_select": {"correct": True}}
        )
        self.assertEqual([r["query"] for r in out], ["ok", "t", "also-ok"])
        rescued = out[1]
        self.assertNotIn("error", rescued)
        self.assertTrue(rescued["extended_cap_pass"])
        self.assertEqual(rescued["extended_cap_requested"], 65536)
        self.assertEqual(rescued["main_protocol"]["truncated_at_tokens"], 32768)
        self.assertIn("seed=0", rescued["main_protocol"]["error"])
        self.assertIs(out[0], keep)
        self.assertEqual(len(persisted), 1)  # persisted after the (single) row

    def test_row_truncated_again_is_flagged_and_stamped_with_its_effective_cap(self) -> None:
        results = [_trunc_row("t", 2, attempts=1)]

        def grade(problem: dict) -> dict:
            raise ValidityExhausted(2, "cut", truncated=True, cap=64000)

        out, _ = self._run(results, self._problems("t"), grade)
        row = out[0]
        self.assertTrue(row["truncated"])
        self.assertEqual(row["truncated_at_tokens"], 64000)
        self.assertEqual(row["truncation_attempts"], 2)
        self.assertTrue(row["extended_cap_pass"])
        self.assertEqual(row["main_protocol"]["truncated_at_tokens"], 32768)
        # ...and a second extended pass would not pick it again.
        self.assertEqual(extended.select_targets(out, "openrouter_mixed", POOL), [])

    def test_infrastructure_failure_keeps_the_stored_row_and_stays_selectable(self) -> None:
        old = _trunc_row("t", 0)
        results = [old]

        def grade(problem: dict) -> dict:
            raise RuntimeError("proxy down")

        out, _ = self._run(results, self._problems("t"), grade)
        self.assertIs(out[0], old)
        self.assertEqual(old["truncated_at_tokens"], 32768)
        self.assertIn("proxy down", old["extended_attempt_error"])
        self.assertNotIn("extended_cap_pass", old)
        self.assertEqual(len(extended.select_targets(out, "openrouter_mixed", POOL)), 1)

    def test_main_protocol_record_survives_a_second_extended_attempt(self) -> None:
        first = extended.mark_extended({"query": "t"}, _trunc_row("t", 0), 65536)
        second = extended.mark_extended({"query": "t"}, first, 65536)
        self.assertEqual(second["main_protocol"]["truncated_at_tokens"], 32768)


if __name__ == "__main__":
    unittest.main()
