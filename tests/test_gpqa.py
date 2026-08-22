from __future__ import annotations

import unittest

from or_select.gpqa import extract_choice, is_correct


class ExtractChoiceTest(unittest.TestCase):
    def test_answer_marker(self) -> None:
        self.assertEqual(extract_choice("Reasoning...\n\nANSWER: B"), "B")

    def test_answer_marker_case_insensitive(self) -> None:
        self.assertEqual(extract_choice("blah\nanswer: c"), "C")

    def test_answer_marker_with_parens(self) -> None:
        self.assertEqual(extract_choice("blah\nANSWER: (D)"), "D")

    def test_takes_last_answer_marker_when_multiple(self) -> None:
        text = "First I think ANSWER: A, but reconsidering, ANSWER: C"
        self.assertEqual(extract_choice(text), "C")

    def test_falls_back_to_bare_letter_on_its_own_line(self) -> None:
        self.assertEqual(extract_choice("Long reasoning here.\n\nB"), "B")

    def test_bare_letter_with_period(self) -> None:
        self.assertEqual(extract_choice("Reasoning.\n\nA."), "A")

    def test_does_not_false_positive_on_stray_letter_in_reasoning(self) -> None:
        # No ANSWER: marker and the last line is prose, not a bare letter --
        # must not guess from a stray "A" appearing mid-sentence.
        self.assertIsNone(extract_choice("A is a variable representing energy, not the answer."))

    def test_no_marker_and_no_bare_letter_returns_none(self) -> None:
        self.assertIsNone(extract_choice("I'm not sure what the answer is."))

    def test_empty_text_returns_none(self) -> None:
        self.assertIsNone(extract_choice(""))


class IsCorrectTest(unittest.TestCase):
    def test_exact_match(self) -> None:
        self.assertTrue(is_correct("B", "B"))

    def test_case_insensitive(self) -> None:
        self.assertTrue(is_correct("b", "B"))

    def test_wrong_letter_is_incorrect(self) -> None:
        self.assertFalse(is_correct("A", "B"))

    def test_none_prediction_is_never_correct(self) -> None:
        self.assertFalse(is_correct(None, "B"))


if __name__ == "__main__":
    unittest.main()
