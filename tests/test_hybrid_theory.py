"""Checks for the vote-first (Rule H) optimality result and the difficulty-mixture threshold (zero API calls)."""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import difficulty_mixture as mix  # noqa: E402
import hybrid_rule as hyb  # noqa: E402


class HybridTheoryTest(unittest.TestCase):
    def test_hybrid_is_bayes_optimal_and_dominates(self):
        for n in (3, 4):
            for p in (Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)):
                for q in (Fraction(1, 2), Fraction(3, 5), Fraction(1)):
                    plur, cop, h = hyb.accuracies(n, p, q)
                    self.assertEqual(hyb.bayes_optimal(n, p, q), h)
                    self.assertGreaterEqual(h, plur)
                    self.assertGreaterEqual(h, cop)

    def test_three_candidate_lone_correct_closed_form(self):
        q = Fraction(3, 5)
        self.assertEqual(hyb.copeland_correct_prob(3, 1, q), q * q + q * (1 - q) / 3)

    def test_point_mass_mixture_recovers_single_p_threshold(self):
        p = 0.6
        m1, m2 = p * (1 - p) ** 2, p**2 * (1 - p)
        self.assertAlmostEqual(mix.q_star_mixture(m1, m2), mix.th.q_star(p), places=6)

    def test_dispersion_changes_threshold_at_fixed_mean(self):
        mu = 0.8
        spread = mix.q_star_mixture(mix.beta_moment(mu, 1 - mu, 1, 2), mix.beta_moment(mu, 1 - mu, 2, 1))
        self.assertLess(spread, mix.th.q_star(mu) - 0.05)


if __name__ == "__main__":
    unittest.main()
