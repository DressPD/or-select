import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bayes_gate as bg  # noqa: E402
import collision_model as cm  # noqa: E402


class BayesGateTests(unittest.TestCase):
    def test_posteriors_match_brute_force(self):
        bg.verify_posteriors()

    def test_gate_dominates_margin_gates(self):
        for n in (3, 5):
            for p, s, q in [(0.5, 0.5, 0.8), (0.3, 0.9, 0.7), (0.8, 0.2, 0.95)]:
                best = max(cm.evaluate(n, p, s, q, t)[0] for t in (None, 0, 1, 2, 10**6))
                self.assertGreaterEqual(bg.gate(n, p, s, q, 0.0)[0], best - 1e-12)

    def test_comparing_top_two_is_optimal_single_comparison(self):
        # expected accuracy after one comparison of classes (a, b) followed by the Bayes-optimal choice
        for sizes, p, s, q in [((3, 2, 1), 0.5, 0.5, 0.8), ((2, 2, 1, 1), 0.4, 0.7, 0.9), ((2, 1, 1, 1), 0.6, 0.3, 0.7)]:
            pis, _ = bg.posteriors(sizes, p, s)
            order = sorted(range(len(pis)), key=lambda i: -pis[i])

            def value(a, b):
                m = max([pis[k] for k in range(len(pis)) if k not in (a, b)] + [0.0])
                v1 = max(pis[a] * q, pis[b] * (1 - q), m / 2)
                v2 = max(pis[a] * (1 - q), pis[b] * q, m / 2)
                return v1 + v2

            top = value(order[0], order[1])
            for a in range(len(pis)):
                for b in range(a + 1, len(pis)):
                    self.assertLessEqual(value(a, b), top + 1e-12)
            gain = top - max(pis)
            self.assertAlmostEqual(gain, max(q * pis[order[1]] - (1 - q) * pis[order[0]], 0.0), places=12)

    def test_sequential_policy_is_control_limit(self):
        for q, c in [(0.7, 0.01), (0.85, 0.02), (0.9, 0.005)]:
            _, _, dec = bg.solve_sequence(0.45, 0.30, 0.25, q, c, rmax=9)
            by_n: dict = {}
            for (w1, w2), cont in dec.items():
                by_n.setdefault(w1 + w2, []).append((w1 - w2, cont))
            for n, items in by_n.items():
                cont_d = sorted(d for d, cont in items if cont)
                if cont_d:
                    # continuation states form a contiguous run of the difference d (a log-odds interval)
                    self.assertEqual(cont_d, list(range(cont_d[0], cont_d[-1] + 2, 2))[: len(cont_d)])

    def test_closed_form_threshold(self):
        # two classes of size >= 2: gate compares iff margin < log(q/(1-q))/log(rho)
        p, s, q = 0.6, 0.5, 0.9
        thr = bg.margin_threshold(p, s, q)
        for m1, m2 in [(2, 2), (3, 2), (4, 2), (5, 2), (6, 2)]:
            pis, _ = bg.posteriors((m1, m2), p, s)
            gain = q * pis[1] - (1 - q) * pis[0]
            self.assertEqual(gain > 0, (m1 - m2) < thr)


if __name__ == "__main__":
    unittest.main()
