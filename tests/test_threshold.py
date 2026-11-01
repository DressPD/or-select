from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import judge_threshold_general as gen  # noqa: E402
import judge_threshold_theory as th  # noqa: E402


class ThresholdTest(unittest.TestCase):
    def test_closed_form_matches_enumeration(self) -> None:
        for p in (Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)):
            for q in (Fraction(1, 2), Fraction(3, 5), Fraction(9, 10)):
                ors, vote = th.acc(p, q)
                self.assertEqual(ors - vote, th.delta_closed(p, q))

    def test_general_enumerator_reproduces_n3(self) -> None:
        for p, q in ((0.3, 0.6), (0.8, 0.9)):
            got = gen.exact_gap(3, p, 0.0, gen.uniform_Q(3, q))
            want = float(th.delta_closed(Fraction(p).limit_denominator(10**6), Fraction(q).limit_denominator(10**6)))
            self.assertAlmostEqual(got, want, places=9)

    def test_chance_judge_selects_with_accuracy_p(self) -> None:
        # q = 1/2: Copeland ties are uniform, so the selected candidate is correct w.p. k/N given k
        for N, k in ((4, 1), (4, 3), (5, 2)):
            self.assertAlmostEqual(gen.copeland_acc_given_k(N, k, gen.uniform_Q(N, 0.5)), k / N, places=12)

    def test_threshold_values_and_rho_direction(self) -> None:
        self.assertAlmostEqual(gen.q_star_exact(3, 0.8), 0.804, places=3)
        self.assertGreater(gen.q_star_exact(4, 0.8), gen.q_star_exact(3, 0.8))
        self.assertLess(gen.q_star_exact(4, 0.8, rho=0.5), gen.q_star_exact(4, 0.8, rho=0.0))

    def test_vote_accuracy_with_attractor(self) -> None:
        self.assertAlmostEqual(gen.vote_acc_given_k(3, 1, 0.0), 1 / 3)
        self.assertAlmostEqual(gen.vote_acc_given_k(3, 1, 1.0), 0.0)  # both wrong answers coincide and win
        self.assertAlmostEqual(gen.vote_acc_given_k(3, 2, 1.0), 1.0)

    def test_coupling_monotonicity(self) -> None:
        self.assertTrue(gen.check_monotone(4, trials=15))

    def test_monte_carlo_agrees_with_exact(self) -> None:
        ex = gen.exact_gap(4, 0.5, 0.0, gen.uniform_Q(4, 0.7))
        mc, se = gen.mc_gap(4, 0.5, 0.0, 0.7, n=20000, seed=11, chunk=5000)
        self.assertLess(abs(mc - ex), 4 * se + 1e-3)
        self.assertIsInstance(np.float64(mc), float)


if __name__ == "__main__":
    unittest.main()
