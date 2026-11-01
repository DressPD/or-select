from __future__ import annotations

import json
import unittest
from pathlib import Path

from or_select.mmlu_pro import extract_choice, format_question, is_correct


class ExtractChoiceTest(unittest.TestCase):
    def test_answer_marker_is_preferred_and_covers_a_to_j(self) -> None:
        self.assertEqual(extract_choice("reasoning...\nANSWER: J"), "J")
        self.assertEqual(extract_choice("ANSWER: (e)"), None)  # lower-case letter is not an option
        self.assertEqual(extract_choice("answer: C"), "C")
        self.assertEqual(extract_choice("ANSWER: B\nlater\nANSWER: F"), "F")

    def test_boxed_and_prose_fallbacks(self) -> None:
        self.assertEqual(extract_choice(r"so \boxed{D}"), "D")
        self.assertEqual(extract_choice("Therefore the answer is H."), "H")

    def test_prose_never_reads_an_article_as_option_a(self) -> None:
        self.assertIsNone(extract_choice("the answer is a function of x"))
        self.assertIsNone(extract_choice("The answer is an integer."))

    def test_bare_last_line_letter_and_no_answer(self) -> None:
        self.assertEqual(extract_choice("thinking\n\nG"), "G")
        self.assertIsNone(extract_choice("thinking about it"))
        self.assertIsNone(extract_choice(""))

    def test_is_correct(self) -> None:
        self.assertTrue(is_correct("I", "i"))
        self.assertFalse(is_correct("A", "B"))
        self.assertFalse(is_correct(None, "A"))


class FormatQuestionTest(unittest.TestCase):
    def test_options_are_lettered_in_order(self) -> None:
        text = format_question("Q?", ["x", "y", "z"])
        self.assertTrue(text.endswith("A. x\nB. y\nC. z"))


class SampleFileTest(unittest.TestCase):
    def test_sample_is_well_formed_if_present(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "mmlu_pro_sample.jsonl"
        if not path.exists():
            self.skipTest("run scripts/fetch_mmlu_pro_sample.py first")
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 100)
        for r in rows:
            self.assertIn(r["ground_truth"], list("ABCDEFGHIJ"))
            self.assertIn(f"\n{r['ground_truth']}. ", r["query"])
        self.assertEqual(len({r["unique_id"] for r in rows}), 100)


if __name__ == "__main__":
    unittest.main()
