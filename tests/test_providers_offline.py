from __future__ import annotations

import unittest

from or_select.providers import _parse_score, _stable_seed


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


class StableSeedTest(unittest.TestCase):
    def test_same_prompt_same_seed(self) -> None:
        self.assertEqual(_stable_seed("hello"), _stable_seed("hello"))

    def test_different_prompt_different_seed(self) -> None:
        self.assertNotEqual(_stable_seed("hello"), _stable_seed("world"))


if __name__ == "__main__":
    unittest.main()
