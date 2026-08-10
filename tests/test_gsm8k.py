from __future__ import annotations

import unittest

from or_select.gsm8k import extract_answer, is_correct


class ExtractAnswerTest(unittest.TestCase):
    def test_clean_final_answer(self) -> None:
        self.assertEqual(extract_answer("The final answer is 18."), 18.0)

    def test_takes_last_number_despite_earlier_numbers_in_reasoning(self) -> None:
        text = "Janet has 16 eggs, eats 3, bakes with 4, leaving 9. 9 * 2 = 18. The final answer is 18."
        self.assertEqual(extract_answer(text), 18.0)

    def test_handles_comma_formatted_numbers(self) -> None:
        self.assertEqual(extract_answer("The final answer is 70,000."), 70000.0)

    def test_handles_negative_numbers(self) -> None:
        self.assertEqual(extract_answer("The final answer is -5."), -5.0)

    def test_no_number_returns_none(self) -> None:
        self.assertIsNone(extract_answer("I don't know."))


class IsCorrectTest(unittest.TestCase):
    def test_exact_match(self) -> None:
        self.assertTrue(is_correct(18.0, 18.0))

    def test_none_prediction_is_never_correct(self) -> None:
        self.assertFalse(is_correct(None, 18.0))

    def test_wrong_answer_is_incorrect(self) -> None:
        self.assertFalse(is_correct(17.0, 18.0))

    def test_float_precision_tolerance(self) -> None:
        self.assertTrue(is_correct(18.00000001, 18.0))


if __name__ == "__main__":
    unittest.main()
