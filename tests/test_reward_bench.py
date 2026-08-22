from __future__ import annotations

import unittest

from or_select.reward_bench import (
    CATEGORIES,
    SUBSET_TO_CATEGORY,
    category_for_subset,
    score_summary,
    wilson_interval,
)


class CategoryMappingTest(unittest.TestCase):
    def test_every_subset_maps_to_one_of_the_four_categories(self) -> None:
        for subset, category in SUBSET_TO_CATEGORY.items():
            self.assertIn(category, CATEGORIES, f"{subset} maps to unknown category {category!r}")

    def test_covers_all_23_known_subsets(self) -> None:
        self.assertEqual(len(SUBSET_TO_CATEGORY), 23)

    def test_unknown_subset_raises(self) -> None:
        with self.assertRaises(ValueError):
            category_for_subset("not-a-real-subset")

    def test_category_for_subset_matches_the_mapping(self) -> None:
        self.assertEqual(category_for_subset("math-prm"), "Reasoning")
        self.assertEqual(category_for_subset("alpacaeval-easy"), "Chat")


class WilsonIntervalTest(unittest.TestCase):
    def test_interval_always_within_unit_range(self) -> None:
        for k, n in [(0, 10), (10, 10), (5, 10), (1, 1), (0, 1)]:
            lo, hi = wilson_interval(k, n)
            self.assertGreaterEqual(lo, 0.0)
            self.assertLessEqual(hi, 1.0)
            self.assertLessEqual(lo, hi)

    def test_near_perfect_score_upper_bound_stays_below_one(self) -> None:
        # A naive Wald interval overshoots past 1.0 here (p=0.9, margin~0.186
        # -> hi~1.086); Wilson must stay inside [0, 1].
        _, hi = wilson_interval(9, 10)
        self.assertLess(hi, 1.0)

    def test_exactly_perfect_score_reaches_but_does_not_exceed_one(self) -> None:
        _, hi = wilson_interval(10, 10)
        self.assertEqual(hi, 1.0)

    def test_more_data_narrows_the_interval(self) -> None:
        lo10, hi10 = wilson_interval(7, 10)
        lo100, hi100 = wilson_interval(70, 100)
        self.assertLess(hi100 - lo100, hi10 - lo10)

    def test_zero_n_returns_maximally_uninformative_interval(self) -> None:
        self.assertEqual(wilson_interval(0, 0), (0.0, 1.0))


class ScoreSummaryTest(unittest.TestCase):
    def test_category_score_is_mean_of_subset_accuracies_not_micro_average(self) -> None:
        # Reasoning has 2 subsets here: math-prm (1/1 correct) and hep-python
        # (0/9 correct). Micro-average would be 1/10 = 10%; the category
        # score must be the mean of the two subset accuracies: (1.0+0.0)/2 = 50%.
        results = [{"subset": "math-prm", "correct": True}] + [
            {"subset": "hep-python", "correct": False} for _ in range(9)
        ]
        summary = score_summary(results)
        self.assertAlmostEqual(summary["category_scores"]["Reasoning"]["accuracy"], 0.5)

    def test_overall_is_mean_of_category_scores(self) -> None:
        results = (
            [{"subset": "alpacaeval-easy", "correct": True}] * 4  # Chat: 100%
            + [{"subset": "llmbar-natural", "correct": False}] * 4  # Chat Hard: 0%
            + [{"subset": "xstest-should-refuse", "correct": True}] * 2  # Safety: 100%
            + [{"subset": "math-prm", "correct": False}] * 2  # Reasoning: 0%
        )
        summary = score_summary(results)
        self.assertAlmostEqual(summary["overall_accuracy"], 0.5)

    def test_empty_results_do_not_crash(self) -> None:
        summary = score_summary([])
        self.assertEqual(summary["overall_accuracy"], 0.0)
        self.assertEqual(summary["category_scores"], {})


if __name__ == "__main__":
    unittest.main()
