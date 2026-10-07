from __future__ import annotations

import unittest

from or_select.pipeline import run_pipeline
from or_select.rejudge import JUDGE_VERSION, LEGACY_JUDGE_VERSION, needs_rejudge, rejudge_row


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

    def test_needs_rejudge_rules(self) -> None:
        base = {"candidates": [{"text": "a"}]}
        self.assertTrue(needs_rejudge(base))
        self.assertTrue(needs_rejudge({**base, "judge_version": LEGACY_JUDGE_VERSION}))
        self.assertFalse(needs_rejudge({**base, "judge_version": JUDGE_VERSION}))
        self.assertFalse(needs_rejudge({**base, "error": "x"}))  # failed rows are regenerated, not re-judged
        self.assertFalse(needs_rejudge({"candidates": None}))  # nothing stored to replay


if __name__ == "__main__":
    unittest.main()
