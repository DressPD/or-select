import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import collision_model as cm  # noqa: E402


class CollisionModelTests(unittest.TestCase):
    def test_exact_matches_simulation(self):
        for n, p, s, q, t in [(5, 0.4, 0.5, 0.8, 0), (6, 0.3, 0.8, 0.7, 1), (5, 0.4, 0.5, 0.8, None)]:
            ex = cm.evaluate(n, p, s, q, t)
            mc = cm.monte_carlo(n, p, s, q, t, reps=60000)
            self.assertAlmostEqual(ex[0], mc[0], delta=0.012)
            self.assertAlmostEqual(ex[1], mc[1], delta=0.012)

    def test_tie_only_judging_equals_plurality_at_chance(self):
        for n in (3, 5):
            for s in (0.0, 0.6):
                self.assertAlmostEqual(cm.evaluate(n, 0.4, s, 0.5, 0)[0], cm.evaluate(n, 0.4, s, 0.5, None)[0], places=12)

    def test_tie_only_judging_never_worse_for_good_judge(self):
        for n in (3, 5):
            for p in (0.2, 0.5, 0.8):
                for s in (0.0, 0.5, 0.9):
                    for q in (0.5, 0.7, 1.0):
                        self.assertGreaterEqual(cm.evaluate(n, p, s, q, 0)[0], cm.evaluate(n, p, s, q, None)[0] - 1e-12)

    def test_breakeven_falls_with_collisions(self):
        values = [cm.breakeven_q(5, 0.5, s, 10**6) for s in (0.0, 0.5, 0.9)]
        self.assertTrue(values[0] > values[1] > values[2])


if __name__ == "__main__":
    unittest.main()
