"""Bayes-optimal judging under colliding wrong answers (result D): log-odds gate and sequential judging.

    python3 scripts/bayes_gate.py

Zero API calls. Model of scripts/collision_model.py: each of N candidates is correct with probability p; a wrong candidate
repeats one shared distractor with probability s and otherwise gives an answer nobody else gives. The observation is the
answer partition. Facts verified here by exhaustive enumeration:

  (i)   Posterior of class i being the correct class (closed form below) equals brute-force enumeration over all
        candidate-level labelings (N <= 7).
  (ii)  With both top classes of size >= 2 and all other classes singletons, the posterior odds of the larger class
        equal rho^(m1-m2), rho = p / ((1-p) s)  (the vote margin is prior log-odds).
  (iii) One judge comparison between the two best classes changes expected accuracy by  q*pi2 - (1-q)*pi1  (pi_i the
        posterior of class i), so the Bayes gate "compare iff q*pi2 - (1-q)*pi1 > c" is optimal among single-comparison
        policies; it is at least as accurate as every margin-gated rule G_t at c = 0 (exact enumeration).
  (iv)  With repeated independent comparisons and linear cost c per comparison, optimal stopping on the posterior is
        computed exactly by dynamic programming (control-limit / SPRT structure).
Writes manuscript/Bayes_data.tex.
"""

from __future__ import annotations

import itertools
import sys
from functools import lru_cache
from math import factorial, log
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import collision_model as cm  # noqa: E402

DEST = ROOT / "manuscript" / "Bayes_data.tex"


def others_weight(others: tuple, s: float) -> float:
    """Probability that wrong candidates form exactly these answer classes (other than correct one), given s."""
    big = [x for x in others if x >= 2]
    singles = sum(1 for x in others if x == 1)
    if len(big) >= 2:
        return 0.0
    if len(big) == 1:
        return s ** big[0] * (1 - s) ** singles
    return (1 - s) ** singles + (singles * s * (1 - s) ** (singles - 1) if singles else 0.0)


def posteriors(sizes: tuple, p: float, s: float):
    """(pi_1..pi_K, pi_none) posterior that class i is the correct class, from the class sizes only."""
    n = sum(sizes)
    like = []
    for i, m in enumerate(sizes):
        rest = sizes[:i] + sizes[i + 1:]
        like.append(p**m * (1 - p) ** (n - m) * others_weight(rest, s))
    none = (1 - p) ** n * others_weight(sizes, s)
    z = sum(like) + none
    return [x / z for x in like], none / z


def brute_force_posterior(partition: list, p: float, s: float):
    """Posterior of each class being the correct one, by enumerating all labelings in {C, A, U}^N."""
    n = sum(len(c) for c in partition)
    target = frozenset(frozenset(c) for c in partition)
    mass = {frozenset(c): 0.0 for c in partition}
    none_mass = 0.0
    for lab in itertools.product("CAU", repeat=n):
        pr = 1.0
        for x in lab:
            pr *= p if x == "C" else ((1 - p) * s if x == "A" else (1 - p) * (1 - s))
        cs = frozenset(i for i, x in enumerate(lab) if x == "C")
        a_set = frozenset(i for i, x in enumerate(lab) if x == "A")
        classes = [c for c in (cs, a_set) if c] + [frozenset([i]) for i, x in enumerate(lab) if x == "U"]
        if frozenset(classes) != target:
            continue
        if cs:
            mass[cs] += pr
        else:
            none_mass += pr
    z = sum(mass.values()) + none_mass
    return [mass[frozenset(c)] / z for c in partition], none_mass / z


def verify_posteriors() -> None:
    cases = [[(0, 1), (2,), (3,), (4,)], [(0, 1, 2), (3, 4)], [(0, 1), (2, 3), (4,)], [(0,), (1,), (2,), (3,), (4,)],
             [(0, 1, 2), (3,), (4,), (5,)], [(0, 1, 2), (3, 4, 5), (6,)], [(0, 1), (2, 3, 4, 5, 6)]]
    for p, s in [(0.4, 0.6), (0.7, 0.3), (0.5, 0.9), (0.2, 0.5)]:
        for part in cases:
            sizes = tuple(len(c) for c in part)
            pi, none = posteriors(sizes, p, s)
            bf, bf_none = brute_force_posterior(part, p, s)
            assert all(abs(a - b) < 1e-12 for a, b in zip(pi, bf)) and abs(none - bf_none) < 1e-12, (p, s, part, pi, bf)
    # closed-form odds rho^(m1-m2) when the top two classes have size >= 2 and the rest are singletons
    for p, s in [(0.4, 0.6), (0.7, 0.3), (0.5, 0.9)]:
        rho = p / ((1 - p) * s)
        for m1, m2, extra in [(3, 2, 0), (4, 2, 1), (5, 3, 2), (4, 4, 0), (6, 2, 1)]:
            sizes = (m1, m2) + (1,) * extra
            pi, _ = posteriors(sizes, p, s)
            assert abs(pi[0] / pi[1] - rho ** (m1 - m2)) < 1e-9 * max(1.0, rho ** (m1 - m2)), (p, s, sizes)
    print("verified: closed-form posteriors = brute force (N<=7); odds = rho^(m1-m2) for two classes of size >= 2")


def _firsts(pis: list):
    top = max(pis)
    idx = [i for i, x in enumerate(pis) if abs(x - top) < 1e-12]
    return [(i, 1 / len(idx)) for i in idx]


def gate(n: int, p: float, s: float, q: float, c: float = 0.0):
    """(accuracy, expected judge comparisons) of the Bayes gate with comparison cost c (in units of accuracy)."""
    acc = calls = 0.0
    for k in range(n + 1):
        for a in range(n - k + 1):
            u = n - k - a
            pr = factorial(n) / (factorial(k) * factorial(a) * factorial(u)) * p**k * ((1 - p) * s) ** a * ((1 - p) * (1 - s)) ** u
            if pr == 0:
                continue
            classes = cm._classes(k, a, u)
            sizes = tuple(sz for _, sz in classes)
            if len(classes) == 1:
                acc += pr * (classes[0][0] == "C")
                continue
            pis, _ = posteriors(sizes, p, s)
            for i, wi in _firsts(pis):
                rest = [j for j in range(len(classes)) if j != i]
                for j, wj in _firsts([pis[r] for r in rest]):
                    jj = rest[j]
                    w = wi * wj
                    p1, p2 = pis[i], pis[jj]
                    if q * p2 - (1 - q) * p1 > c:
                        calls += pr * w
                        one = (classes[i][0] == "C") != (classes[jj][0] == "C")
                        acc += pr * w * (q if one else 0.0)
                    else:
                        acc += pr * w * (classes[i][0] == "C")
    return acc, calls


def margin_threshold(p: float, s: float, q: float) -> float:
    """Largest vote margin (real-valued bound) below which a judge of accuracy q should overrule: margin < this."""
    rho = p / ((1 - p) * s)
    return log(q / (1 - q)) / log(rho) if rho > 1 else float("inf")


def sequential(n: int, p: float, s: float, q: float, c: float, rmax: int = 9):
    """Optimal stopping with repeated independent comparisons of the two best classes: (accuracy, expected calls)."""
    acc = calls = 0.0
    for k in range(n + 1):
        for a in range(n - k + 1):
            u = n - k - a
            pr = factorial(n) / (factorial(k) * factorial(a) * factorial(u)) * p**k * ((1 - p) * s) ** a * ((1 - p) * (1 - s)) ** u
            if pr == 0:
                continue
            classes = cm._classes(k, a, u)
            sizes = tuple(sz for _, sz in classes)
            if len(classes) == 1:
                acc += pr * (classes[0][0] == "C")
                continue
            pis, pnone = posteriors(sizes, p, s)
            for i, wi in _firsts(pis):
                rest = [j for j in range(len(classes)) if j != i]
                for j, wj in _firsts([pis[r] for r in rest]):
                    jj = rest[j]
                    w = wi * wj
                    v, ncalls, _ = solve_sequence(pis[i], pis[jj], 1 - pis[i] - pis[jj], q, c, rmax)
                    # v includes -c per call; recover pure accuracy by adding c * expected calls
                    acc += pr * w * (v + c * ncalls)
                    calls += pr * w * ncalls
    return acc, calls


def solve_sequence(p1: float, p2: float, p0: float, q: float, c: float, rmax: int = 9):
    """Optimal stopping for repeated independent comparisons between two classes with prior masses p1, p2 (p0: neither
    is correct; the judge then answers by a fair coin). Returns (net value, expected calls, decisions) where decisions maps
    (wins of class 1, wins of class 2) -> True if the optimal policy continues there."""
    decisions: dict = {}

    @lru_cache(maxsize=None)
    def value(w1: int, w2: int):
        m1 = p1 * q**w1 * (1 - q) ** w2
        m2 = p2 * (1 - q) ** w1 * q**w2
        m0 = p0 * 0.5 ** (w1 + w2)
        z = m1 + m2 + m0
        stop = max(m1, m2) / z
        if w1 + w2 >= rmax:
            decisions[(w1, w2)] = False
            return stop, 0.0
        pw = (m1 * q + m2 * (1 - q) + m0 * 0.5) / z
        v1, c1 = value(w1 + 1, w2)
        v2, c2 = value(w1, w2 + 1)
        cont = pw * v1 + (1 - pw) * v2 - c
        if cont > stop:
            decisions[(w1, w2)] = True
            return cont, 1 + pw * c1 + (1 - pw) * c2
        decisions[(w1, w2)] = False
        return stop, 0.0

    v, ncalls = value(0, 0)
    return v, ncalls, decisions


def verify_dominance() -> list:
    rows = []
    for n in (3, 5, 6):
        for p in (0.3, 0.5, 0.7, 0.85):
            for s in (0.0, 0.3, 0.6, 0.9):
                for q in (0.55, 0.7, 0.85, 0.95):
                    g, _ = gate(n, p, s, q, 0.0)
                    best = max(cm.evaluate(n, p, s, q, t)[0] for t in (None, 0, 1, 2, 10**6))
                    assert g >= best - 1e-12, (n, p, s, q, g, best)
    print("verified: Bayes gate (c=0) >= plurality and every margin gate G_t (t=0,1,2,inf) for N in {3,5,6}")
    for p, s, q in [(0.5, 0.5, 0.8), (0.5, 0.9, 0.8), (0.3, 0.5, 0.8), (0.7, 0.9, 0.9)]:
        n = 5
        pl = cm.evaluate(n, p, s, q, None)[0]
        g0, c0 = cm.evaluate(n, p, s, q, 0)
        g1, c1 = cm.evaluate(n, p, s, q, 1)
        gi, ci = cm.evaluate(n, p, s, q, 10**6)
        gb, cb = gate(n, p, s, q, 0.0)
        print(f"p={p} s={s} q={q}: PL {100*pl:.1f} G0 {100*g0:.1f}({c0:.2f}) G1 {100*g1:.1f}({c1:.2f}) Ginf {100*gi:.1f}({ci:.2f}) Bayes {100*gb:.1f}({cb:.2f})")
        rows.append(f"{p:.1f} & {s:.1f} & {q:.2f} & {100*pl:.1f} & {100*g0:.1f} ({c0:.2f}) & {100*g1:.1f} ({c1:.2f}) & {100*gi:.1f} ({ci:.2f}) & {100*gb:.1f} ({cb:.2f}) \\\\")
    return rows


def main() -> None:
    verify_posteriors()
    rows = verify_dominance()
    # margin thresholds
    thr = []
    print("margin threshold: judge should overrule a vote margin m only if m < log(q/(1-q))/log(rho)")
    for p, s in [(0.5, 0.5), (0.7, 0.5), (0.83, 0.52), (0.84, 0.38), (0.85, 0.9)]:
        cells = []
        for q in (0.6, 0.7, 0.8, 0.9, 0.95, 0.99):
            cells.append(f"{margin_threshold(p, s, q):.2f}")
        print(p, s, cells)
        thr.append(f"{p:.2f} & {s:.2f} & " + " & ".join(cells) + " \\\\")
    # sequential
    seq = []
    print("sequential optimal stopping vs single-comparison Bayes gate (N=5, p=0.5, s=0.5)")
    for q in (0.7, 0.9):
        for c in (0.02, 0.005):
            sg, sc = gate(5, 0.5, 0.5, q, c)
            qa, qc = sequential(5, 0.5, 0.5, q, c)
            pl = cm.evaluate(5, 0.5, 0.5, q, None)[0]
            print(f"q={q} c={c}: plurality {100*pl:.1f} | single {100*sg:.1f} ({sc:.2f} calls) | sequential {100*qa:.1f} ({qc:.2f} calls)")
            seq.append(f"{q:.1f} & {c:.3f} & {100*pl:.1f} & {100*sg:.1f} ({sc:.2f}) & {100*qa:.1f} ({qc:.2f}) \\\\")
    DEST.write_text(
        "% generated by scripts/bayes_gate.py\n"
        "\\newcommand{\\BayesRows}{%\n" + "\n".join(rows) + "}\n"
        "\\newcommand{\\BayesThrRows}{%\n" + "\n".join(thr) + "}\n"
        "\\newcommand{\\BayesSeqRows}{%\n" + "\n".join(seq) + "}\n"
    )
    print("wrote", DEST)


if __name__ == "__main__":
    main()
