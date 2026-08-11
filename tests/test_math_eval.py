from __future__ import annotations

import unittest

from or_select.math_eval import extract_boxed, is_correct, normalize


class ExtractBoxedTest(unittest.TestCase):
    def test_simple_number(self) -> None:
        self.assertEqual(extract_boxed("Steps... The answer is \\boxed{42}."), "42")

    def test_nested_braces_fraction(self) -> None:
        self.assertEqual(extract_boxed("So x = \\boxed{\\frac{1}{2}}."), "\\frac{1}{2}")

    def test_takes_last_boxed_when_multiple(self) -> None:
        text = "First try \\boxed{5} was wrong, correct answer is \\boxed{7}."
        self.assertEqual(extract_boxed(text), "7")

    def test_deeply_nested_braces(self) -> None:
        text = "\\boxed{\\left(3, \\frac{\\pi}{2}\\right)}"
        self.assertEqual(extract_boxed(text), "\\left(3, \\frac{\\pi}{2}\\right)")

    def test_no_boxed_returns_none(self) -> None:
        self.assertIsNone(extract_boxed("I think the answer is 42."))

    def test_unbalanced_braces_returns_none(self) -> None:
        self.assertIsNone(extract_boxed("\\boxed{\\frac{1}{2}"))


class NormalizeTest(unittest.TestCase):
    def test_dfrac_equals_frac(self) -> None:
        self.assertEqual(normalize("\\dfrac{1}{2}"), normalize("\\frac{1}{2}"))

    def test_strips_left_right(self) -> None:
        self.assertEqual(normalize("\\left(3, \\frac{\\pi}{2}\\right)"), normalize("(3, \\frac{\\pi}{2})"))

    def test_strips_dollar_signs(self) -> None:
        self.assertEqual(normalize("$42$"), normalize("42"))

    def test_strips_text_wrapper(self) -> None:
        self.assertEqual(normalize("\\text{p - q}"), normalize("p - q"))

    def test_ignores_whitespace_differences(self) -> None:
        self.assertEqual(normalize("p - q"), normalize("p-q"))

    def test_case_insensitive(self) -> None:
        self.assertEqual(normalize("ABC"), normalize("abc"))

    def test_does_not_simplify_unequal_fractions(self) -> None:
        # Known limitation, not a bug: 2/4 and 1/2 are mathematically equal
        # but this normalizer does not do algebraic simplification.
        self.assertNotEqual(normalize("\\frac{2}{4}"), normalize("\\frac{1}{2}"))


class IsCorrectTest(unittest.TestCase):
    def test_exact_match(self) -> None:
        self.assertTrue(is_correct("p - q", "p - q"))

    def test_none_prediction_is_never_correct(self) -> None:
        self.assertFalse(is_correct(None, "42"))

    def test_wrong_answer_is_incorrect(self) -> None:
        self.assertFalse(is_correct("41", "42"))

    def test_formatting_differences_still_match(self) -> None:
        self.assertTrue(is_correct("\\dfrac{1}{2}", "\\frac{1}{2}"))


if __name__ == "__main__":
    unittest.main()
