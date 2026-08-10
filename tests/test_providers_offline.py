from __future__ import annotations

import unittest

from or_select.providers import _is_retryable_error, _parse_score, _stable_seed


class ParseScoreTest(unittest.TestCase):
    def test_clean_number_parses(self) -> None:
        self.assertAlmostEqual(_parse_score("0.85"), 0.85)

    def test_takes_last_number_not_first(self) -> None:
        # A reasoning model restating a fact from the query (e.g. a year)
        # before giving its actual confidence must not have that fact
        # mistaken for the score.
        text = "The Berlin Wall fell in 1989, so I'd rate my confidence as 0.95"
        self.assertAlmostEqual(_parse_score(text), 0.95)

    def test_clamps_out_of_range_values(self) -> None:
        self.assertEqual(_parse_score("42"), 1.0)
        self.assertEqual(_parse_score("-3"), 0.0)

    def test_no_number_falls_back_to_midpoint(self) -> None:
        self.assertEqual(_parse_score("no numeric answer here"), 0.5)


class RetryableErrorTest(unittest.TestCase):
    def test_rate_limit_429_is_retryable(self) -> None:
        self.assertTrue(_is_retryable_error(Exception("Error code: 429 - too many requests")))

    def test_gemini_resource_exhausted_is_retryable(self) -> None:
        self.assertTrue(_is_retryable_error(Exception("429 RESOURCE_EXHAUSTED: quota exceeded")))

    def test_proxy_error_is_retryable(self) -> None:
        self.assertTrue(_is_retryable_error(Exception("407 Proxy Authentication Required")))

    def test_insufficient_quota_429_is_not_retryable(self) -> None:
        exc = Exception(
            "Error code: 429 - {'error': {'message': 'You have no credits remaining.', "
            "'type': 'insufficient_quota', 'code': 'credit_balance_exhausted'}}"
        )
        self.assertFalse(_is_retryable_error(exc))

    def test_unrelated_error_is_not_retryable(self) -> None:
        self.assertFalse(_is_retryable_error(Exception("model not found")))


class StableSeedTest(unittest.TestCase):
    def test_same_prompt_same_seed(self) -> None:
        self.assertEqual(_stable_seed("hello"), _stable_seed("hello"))

    def test_different_prompt_different_seed(self) -> None:
        self.assertNotEqual(_stable_seed("hello"), _stable_seed("world"))


if __name__ == "__main__":
    unittest.main()
