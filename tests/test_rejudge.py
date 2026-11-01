from __future__ import annotations

import unittest

from or_select.pipeline import run_pipeline
from or_select.rejudge import (
    JUDGE_VERSION,
    LEGACY_JUDGE_VERSION,
    needs_rejudge,
    needs_reslot,
    rejudge_row,
    reslot_row,
    stale_slots,
)


def _generate(query: str, seed: int) -> str:
    return "ANSWER: " + "x" * (seed % 5) * 7 + f" #{seed % 3}"


def _answer(text: str):
    return text.split("ANSWER:")[-1].strip() if "ANSWER:" in text else None


class RejudgeReplayTest(unittest.TestCase):
    def _live_and_row(self):
        live = run_pipeline("q", n=4, provider="placeholder", generate_fn=_generate, validity_fn=lambda t: "ANSWER:" in t)
        row = {
            "query": "q",
            "ground_truth": live.winner_text.split("ANSWER:")[-1].strip(),
            "or_select": {"answer": "stale", "correct": False},
            "kemeny_young": {"answer": "stale", "correct": False, "is_optimal": None},
            "winner_texts": {"or_select": "stale", "kemeny_young": "stale", "greedy": "keep"},
            "candidates": [
                {"seed": c.metadata["seed"], "source_model": c.source_model, "text": c.text} for c in live.candidates
            ],
        }
        return live, row

    def test_replay_picks_the_same_winner_as_the_live_pipeline(self) -> None:
        live, row = self._live_and_row()
        new = rejudge_row(row, "q", "placeholder", _answer, lambda a, gt: a == gt, lambda t: "ANSWER:" in t)
        self.assertEqual(new["winner_texts"]["or_select"], live.winner_text)
        self.assertEqual(new["or_select"]["answer"], _answer(live.winner_text))
        self.assertTrue(new["or_select"]["correct"])

    def test_judge_independent_fields_and_inputs_are_untouched(self) -> None:
        _, row = self._live_and_row()
        new = rejudge_row(row, "q", "placeholder", _answer, lambda a, gt: a == gt, lambda t: "ANSWER:" in t)
        self.assertEqual(new["winner_texts"]["greedy"], "keep")
        self.assertEqual(new["candidates"], row["candidates"])
        self.assertEqual(row["or_select"]["answer"], "stale")  # input row not mutated

    def test_version_is_bumped_and_no_stale_result_is_kept(self) -> None:
        _, row = self._live_and_row()
        new = rejudge_row(row, "q", "placeholder", _answer, lambda a, gt: a == gt, lambda t: "ANSWER:" in t)
        self.assertEqual(new["judge_version"], JUDGE_VERSION)
        self.assertNotIn("prior_judge", new)

    def test_failed_judge_call_raises_and_leaves_row_untouched(self) -> None:
        _, row = self._live_and_row()
        snapshot = repr(row)

        from unittest import mock

        with mock.patch("or_select.rejudge.resolve_score_judge", return_value=(lambda q, t: 0.5, mock.Mock(side_effect=RuntimeError("boom")))):
            with self.assertRaises(RuntimeError):
                rejudge_row(row, "q", "placeholder", _answer, lambda a, gt: a == gt, lambda t: True)
        self.assertEqual(repr(row), snapshot)

    def test_judge_verdicts_are_stored_with_the_row(self) -> None:
        live, row = self._live_and_row()
        new = rejudge_row(row, "q", "placeholder", _answer, lambda a, gt: a == gt, lambda t: "ANSWER:" in t)
        judgments = new["judgments"]
        ids = {c.id for c in live.candidates}
        self.assertEqual(set(judgments["confidence"]), ids)
        self.assertEqual(set(judgments["selection_scores"]), ids)
        self.assertEqual({k.split("|")[0] for k in judgments["pairwise"]} | {k.split("|")[1] for k in judgments["pairwise"]}, ids)
        self.assertEqual(judgments["pairwise"], {f"{a}|{b}": w for (a, b), w in live.pairwise.items()})

    def test_needs_rejudge_rules(self) -> None:
        base = {"candidates": [{"text": "a"}]}
        self.assertTrue(needs_rejudge(base))
        self.assertTrue(needs_rejudge({**base, "judge_version": LEGACY_JUDGE_VERSION}))
        self.assertFalse(needs_rejudge({**base, "judge_version": JUDGE_VERSION}))
        self.assertFalse(needs_rejudge({**base, "error": "x"}))  # failed rows are regenerated, not re-judged
        self.assertFalse(needs_rejudge({"candidates": None}))  # nothing stored to replay


POOL = ["a", "b", "new"]


def _stale_row():
    models = ["a", "b", "old", "a", "b", "old"]
    return {
        "query": "q",
        "ground_truth": "x",
        "or_select": {"answer": "stale", "correct": False},
        "self_consistency": {"answer": "stale", "correct": False, "had_majority": False},
        "greedy": {"answer": "stale", "correct": False},
        "kemeny_young": {"answer": "stale", "correct": False, "is_optimal": None},
        "winner_texts": {"or_select": "stale", "self_consistency": "stale", "greedy": "stale", "kemeny_young": "stale"},
        "candidates": [
            {"seed": i, "source_model": m, "text": f"ANSWER: {m}{i}"} for i, m in enumerate(models)
        ],
    }


def _backends(pool):
    return [(m, lambda query, seed, _m=m: f"ANSWER: {_m}{seed}") for m in pool]


class ReslotTest(unittest.TestCase):
    def _reslot(self, row, **kwargs):
        from unittest import mock

        with mock.patch("or_select.providers.openrouter_heterogeneous_backends", side_effect=_backends):
            return reslot_row(row, "q", "placeholder", _answer, lambda a, gt: a == gt, lambda t: "ANSWER:" in t, POOL, **kwargs)

    def test_needs_reslot_only_for_valid_rows_with_a_retired_model(self) -> None:
        row = _stale_row()
        self.assertEqual(stale_slots(row, POOL), [2, 5])
        self.assertTrue(needs_reslot(row, POOL))
        self.assertFalse(needs_reslot({**row, "error": "boom"}, POOL))
        self.assertFalse(needs_reslot({**row, "candidates": [{"source_model": "a", "seed": 0, "text": "t"}]}, POOL))
        self.assertFalse(needs_reslot({"candidates": None}, POOL))

    def test_dated_nemotron_slug_is_current_but_laguna_is_retired(self) -> None:
        from or_select.pipeline import OPENROUTER_MIXED_MODELS, RETIRED_MIXED_MODELS, canonical_model

        dated = "nvidia/nemotron-3.5-lightning-20260807:free"
        laguna = "poolside/laguna-s-2.1:free"
        self.assertEqual(canonical_model(dated), OPENROUTER_MIXED_MODELS[0])
        self.assertEqual(canonical_model("x/y:free"), "x/y:free")
        self.assertNotIn(laguna, OPENROUTER_MIXED_MODELS)
        self.assertEqual(RETIRED_MIXED_MODELS[laguna], OPENROUTER_MIXED_MODELS[1])
        row = {
            "candidates": [
                {"source_model": dated, "seed": 0, "text": "t"},
                {"source_model": laguna, "seed": 1, "text": "t"},
                {"source_model": OPENROUTER_MIXED_MODELS[2], "seed": 2, "text": "t"},
            ]
        }
        self.assertEqual(stale_slots(row, OPENROUTER_MIXED_MODELS), [1])

    def test_only_the_retired_slots_are_regenerated_by_the_slot_owner(self) -> None:
        row = _stale_row()
        new = self._reslot(row)
        self.assertEqual([c["source_model"] for c in new["candidates"]], ["a", "b", "new", "a", "b", "new"])
        self.assertEqual([c["seed"] for c in new["candidates"]], [0, 1, 2, 3, 4, 5])
        for i in (0, 1, 3, 4):  # kept untouched
            self.assertEqual(new["candidates"][i], row["candidates"][i])
        self.assertEqual(new["candidates"][2]["text"], "ANSWER: new2")
        self.assertEqual(new["candidates"][5]["text"], "ANSWER: new5")
        self.assertFalse(needs_reslot(new, POOL))

    def test_selection_and_baselines_are_recomputed_and_nothing_stale_is_kept(self) -> None:
        row = _stale_row()
        new = self._reslot(row)
        self.assertEqual(new["judge_version"], JUDGE_VERSION)
        for key in ("or_select", "self_consistency", "greedy", "kemeny_young"):
            self.assertNotEqual(new[key]["answer"], "stale", key)
        self.assertNotIn("stale", new["winner_texts"].values())
        self.assertEqual(new["greedy"]["answer"], "a0")
        self.assertEqual(row["or_select"]["answer"], "stale")  # input row not mutated

    def test_rows_without_kemeny_or_winner_texts_still_work(self) -> None:
        row = _stale_row()
        del row["kemeny_young"], row["winner_texts"]
        new = self._reslot(row)
        self.assertNotIn("kemeny_young", new)
        self.assertNotIn("winner_texts", new)
        self.assertEqual(new["candidates"][2]["source_model"], "new")

    def test_failed_regeneration_raises_and_leaves_row_untouched(self) -> None:
        from unittest import mock

        row = _stale_row()
        snapshot = repr(row)
        broken = [("a", lambda q, s: "ANSWER: a"), ("b", lambda q, s: "ANSWER: b"), ("new", mock.Mock(side_effect=RuntimeError("boom")))]
        with mock.patch("or_select.providers.openrouter_heterogeneous_backends", return_value=broken):
            with self.assertRaises(RuntimeError):
                reslot_row(row, "q", "placeholder", _answer, lambda a, gt: a == gt, lambda t: True, POOL)
        self.assertEqual(repr(row), snapshot)


if __name__ == "__main__":
    unittest.main()
