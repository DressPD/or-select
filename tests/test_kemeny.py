from __future__ import annotations

import unittest

from or_select.core import Candidate
from or_select.kemeny import solve_kemeny_ranking

CANDS3 = [
    Candidate(id="a", text="A", source_model="m"),
    Candidate(id="b", text="B", source_model="m"),
    Candidate(id="c", text="C", source_model="m"),
]


class KemenyTest(unittest.TestCase):
    def test_transitive_preferences_give_the_obvious_ranking(self) -> None:
        pairwise = {
            ("a", "b"): 0.9, ("b", "a"): 0.1,
            ("b", "c"): 0.9, ("c", "b"): 0.1,
            ("a", "c"): 0.95, ("c", "a"): 0.05,
        }
        ranking, is_optimal = solve_kemeny_ranking(CANDS3, pairwise)
        self.assertEqual(ranking, ["a", "b", "c"])
        self.assertTrue(is_optimal)

    def test_single_candidate(self) -> None:
        ranking, is_optimal = solve_kemeny_ranking(CANDS3[:1], {})
        self.assertEqual(ranking, ["a"])
        self.assertTrue(is_optimal)

    def test_raises_on_empty_candidates(self) -> None:
        with self.assertRaises(ValueError):
            solve_kemeny_ranking([], {})

    def test_two_candidates_ranks_the_preferred_one_first(self) -> None:
        pairwise = {("a", "b"): 0.7, ("b", "a"): 0.3}
        ranking, is_optimal = solve_kemeny_ranking(CANDS3[:2], pairwise)
        self.assertEqual(ranking, ["a", "b"])
        self.assertTrue(is_optimal)

    def test_returns_a_valid_permutation_of_all_ids(self) -> None:
        pairwise = {
            ("a", "b"): 0.6, ("b", "a"): 0.4,
            ("b", "c"): 0.6, ("c", "b"): 0.4,
            ("a", "c"): 0.4, ("c", "a"): 0.6,  # Condorcet cycle: a>b>c>a
        }
        ranking, _ = solve_kemeny_ranking(CANDS3, pairwise)
        self.assertEqual(sorted(ranking), ["a", "b", "c"])

    def test_deterministic_across_repeated_solves_even_under_a_cycle(self) -> None:
        pairwise = {
            ("a", "b"): 0.6, ("b", "a"): 0.4,
            ("b", "c"): 0.6, ("c", "b"): 0.4,
            ("a", "c"): 0.4, ("c", "a"): 0.6,
        }
        results = {tuple(solve_kemeny_ranking(CANDS3, pairwise)[0]) for _ in range(5)}
        self.assertEqual(len(results), 1, "same pairwise matrix must always yield the same ranking")

    def test_matches_manual_best_response_for_four_candidates(self) -> None:
        cands = CANDS3 + [Candidate(id="d", text="D", source_model="m")]
        # d beats everyone narrowly; a beats b and c comfortably; b beats c.
        pairwise = {
            ("a", "b"): 0.8, ("b", "a"): 0.2,
            ("a", "c"): 0.8, ("c", "a"): 0.2,
            ("b", "c"): 0.7, ("c", "b"): 0.3,
            ("a", "d"): 0.4, ("d", "a"): 0.6,
            ("b", "d"): 0.3, ("d", "b"): 0.7,
            ("c", "d"): 0.3, ("d", "c"): 0.7,
        }
        ranking, is_optimal = solve_kemeny_ranking(cands, pairwise)
        self.assertEqual(ranking, ["d", "a", "b", "c"])
        self.assertTrue(is_optimal)

    def test_tight_conflict_budget_is_still_deterministic_and_reports_not_optimal(self) -> None:
        """A budget too small to prove optimality must still be exactly
        reproducible (same budget -> same truncated search -> same result)
        and must say so via is_optimal=False, never silently claim an
        unverified ranking is the true Kemeny consensus."""
        cands = CANDS3 + [Candidate(id="d", text="D", source_model="m"), Candidate(id="e", text="E", source_model="m")]
        pairwise = {}
        ids = [c.id for c in cands]
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                pairwise[(a, b)] = 0.5
                pairwise[(b, a)] = 0.5
        results = [solve_kemeny_ranking(cands, pairwise, max_conflicts=1) for _ in range(3)]
        rankings = {tuple(r) for r, _ in results}
        self.assertEqual(len(rankings), 1, "a tight budget must still be exactly reproducible")
        self.assertTrue(all(sorted(r) == sorted(ids) for r, _ in results))


if __name__ == "__main__":
    unittest.main()
