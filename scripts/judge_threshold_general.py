"""General-N, pair-dependent and correlated-wrong-answer version of the judge-accuracy threshold.

    python3 scripts/judge_threshold_general.py            # writes manuscript/ThresholdGeneral_data.tex (exact thresholds N=3..6, Monte Carlo validation)

Zero API calls. Extends scripts/judge_threshold_theory.py (N = 3, closed form).

Model. N candidates, each correct independently with probability p. A wrong candidate takes one shared
"attractor" wrong value with probability rho, otherwise a value distinct from every other candidate's
(rho = 0 is the N = 3 theorem's setting). A judge compares every pair once: on a pair with exactly one correct candidate it
prefers the correct one with probability q_ij (a matrix; the uniform case is q_ij = q); on any other pair it picks uniformly.
Selection is the Copeland winner (most pairwise wins), ties broken uniformly over candidates. Plurality voting returns the most
frequent answer, ties broken uniformly over the tied *answers*.

  exact_gap(N, p, rho, Q)     exact acc(Copeland) - acc(plurality), enumerating all 2^(N(N-1)/2) comparison outcomes (N <= 7)
  mc_gap(N, p, rho, q, ...)   the same by simulation with common random numbers (validation only)
  q_star_exact(N, p, rho)     smallest uniform q at which the gap is >= 0, by bisection (the gap is nondecreasing in q)

Lemma (coupling; checked numerically below): P(correct selected) is nondecreasing in every q_ij, so q_min >= q*(p, N, rho) is
sufficient for a pair-dependent judge to match voting, and q_max < q* is sufficient for it to lose.
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "manuscript" / "ThresholdGeneral_data.tex"


def vote_acc_given_k(N: int, k: int, rho: float) -> float:
    """P(plurality returns the correct answer | k correct), wrong answers attractor w.p. rho else distinct."""
    total = 0.0
    for m in range(N - k + 1):
        pm = math.comb(N - k, m) * rho**m * (1 - rho) ** (N - k - m)
        d = N - k - m
        counts = ([k] if k else []) + ([m] if m else []) + [1] * d
        top = max(counts)
        tied = [c == top for c in counts]
        total += pm * (tied[0] / sum(tied) if k else 0.0)
    return total


def copeland_acc_given_k(N: int, k: int, Q: np.ndarray) -> float:
    """Exact P(correct selected | the first k candidates are the correct ones), Q[i, j] = P(i preferred | i correct, j wrong)."""
    if k == 0:
        return 0.0
    if k == N:
        return 1.0
    pairs = list(itertools.combinations(range(N), 2))
    M = len(pairs)
    bits = ((np.arange(2**M)[:, None] >> np.arange(M)[None, :]) & 1).astype(np.int8)  # 1: first element of the pair wins
    prob = np.ones(2**M)
    score = np.zeros((2**M, N))
    for col, (i, j) in enumerate(pairs):
        if i < k <= j:
            pf = Q[i, j]
        elif j < k <= i:
            pf = 1 - Q[j, i]
        else:
            pf = 0.5
        b = bits[:, col]
        prob *= np.where(b == 1, pf, 1 - pf)
        score[:, i] += b
        score[:, j] += 1 - b
    top = score == score.max(axis=1, keepdims=True)
    frac = top[:, :k].sum(axis=1) / top.sum(axis=1)
    return float((prob * frac).sum())


def exact_gap(N: int, p: float, rho: float, Q: np.ndarray) -> float:
    gap = 0.0
    for k in range(N + 1):
        w = math.comb(N, k) * p**k * (1 - p) ** (N - k)
        gap += w * (copeland_acc_given_k(N, k, Q) - vote_acc_given_k(N, k, rho))
    return gap


def uniform_Q(N: int, q: float) -> np.ndarray:
    return np.full((N, N), q)


def q_star_exact(N: int, p: float, rho: float = 0.0, tol: float = 1e-5) -> float:
    lo, hi = 0.5, 1.0
    if exact_gap(N, p, rho, uniform_Q(N, hi)) < 0:
        return float("nan")
    while hi - lo > tol:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if exact_gap(N, p, rho, uniform_Q(N, mid)) < 0 else (lo, mid)
    return hi


def mc_gap(N: int, p: float, rho: float, q: float, n: int = 40000, seed: int = 0, chunk: int = 4000) -> tuple[float, float]:
    """Monte Carlo accuracy difference (Copeland - plurality) with its standard error; common random numbers across q."""
    rng = np.random.default_rng(seed)
    iu = np.triu_indices(N, 1)
    diffs = []
    for _ in range(0, n, chunk):
        ok = rng.random((chunk, N)) < p
        att = rng.random((chunk, N)) < rho
        u = rng.random((chunk, len(iu[0])))
        a, b = ok[:, iu[0]], ok[:, iu[1]]
        pf = np.where(a & ~b, q, np.where(b & ~a, 1 - q, 0.5))
        first = u < pf
        score = np.zeros((chunk, N))
        for col in range(len(iu[0])):
            score[np.arange(chunk), iu[0][col]] += first[:, col]
            score[np.arange(chunk), iu[1][col]] += ~first[:, col]
        tie = rng.random((chunk, N))
        pick = np.argmax(np.where(score == score.max(1, keepdims=True), 1 + tie, 0), axis=1)
        or_ok = ok[np.arange(chunk), pick]
        # plurality over answers: value 0 = correct, 1 = attractor, 2+i = distinct
        val = np.where(ok, 0, np.where(att, 1, 2 + np.arange(N)[None, :]))
        vote_ok = np.empty(chunk, bool)
        for r in range(chunk):
            vals, cnt = np.unique(val[r], return_counts=True)
            winners = vals[cnt == cnt.max()]
            vote_ok[r] = rng.choice(winners) == 0
        diffs.append(or_ok.astype(float) - vote_ok.astype(float))
    d = np.concatenate(diffs)
    return float(d.mean()), float(d.std(ddof=1) / math.sqrt(len(d)))


def check_monotone(N: int = 4, trials: int = 40, seed: int = 1) -> bool:
    """Coupling lemma: raising any single q_ij never lowers exact Copeland accuracy."""
    rng = np.random.default_rng(seed)
    for _ in range(trials):
        Q = rng.uniform(0.3, 0.95, (N, N))
        k = int(rng.integers(1, N))
        i, j = int(rng.integers(0, k)), int(rng.integers(k, N))
        base = copeland_acc_given_k(N, k, Q)
        Q2 = Q.copy()
        Q2[i, j] = min(1.0, Q[i, j] + 0.05)
        if copeland_acc_given_k(N, k, Q2) < base - 1e-12:
            return False
    return True


def main() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import judge_threshold_theory as th

    # exactness / consistency checks
    for p in (0.3, 0.6, 0.85):
        g = exact_gap(3, p, 0.0, uniform_Q(3, 0.7))
        assert abs(g - float(th.delta_closed(th.Fraction(p).limit_denominator(10**6), th.Fraction(7, 10)))) < 1e-9, p
    assert check_monotone(4) and check_monotone(5, trials=15)
    print("N=3 closed form reproduced by the general enumerator; coupling monotonicity holds on random Q (N=4,5)")

    L = ["% Generated by scripts/judge_threshold_general.py -- do not hand-edit."]
    rows = []
    for N in (3, 4, 5, 6):
        cells = [f"{q_star_exact(N, p, rho):.3f}" for rho in (0.0, 0.5) for p in (0.5, 0.8)]
        rows.append(f"{N} & " + " & ".join(cells) + " \\\\")
        print(N, cells)
    L.append(r"\def\ThresholdNRows{" + "\n".join(rows) + "}")

    # Monte Carlo engine reproduces the exact values (common random numbers, fixed seed, 200k draws)
    val = []
    for N, p, rho, q in ((4, 0.5, 0.0, 0.7), (5, 0.8, 0.5, 0.8), (6, 0.5, 0.5, 0.7), (6, 0.8, 0.0, 0.9)):
        ex = exact_gap(N, p, rho, uniform_Q(N, q))
        mc, se = mc_gap(N, p, rho, q, n=200000, seed=7, chunk=10000)
        val.append(f"{N} & {p:.1f} & {rho:.1f} & {q:.1f} & {100 * ex:+.2f} & {100 * mc:+.2f} $\\pm$ {100 * se:.2f} \\\\")
        print(val[-1])
        assert abs(mc - ex) < 4 * se + 1e-4, (N, p, rho, q, ex, mc, se)
    L.append(r"\def\ThresholdValidationRows{" + "\n".join(val) + "}")

    # pair-dependent judge: the gap lies between the gaps at q_min and q_max (coupling lemma)
    rng = np.random.default_rng(3)
    inside = 0
    trials = 30
    for _ in range(trials):
        N = 5
        Q = rng.uniform(0.55, 0.95, (N, N))
        p, rho = float(rng.uniform(0.3, 0.9)), float(rng.uniform(0, 0.6))
        lo, hi = exact_gap(N, p, rho, uniform_Q(N, Q.min())), exact_gap(N, p, rho, uniform_Q(N, Q.max()))
        inside += lo - 1e-9 <= exact_gap(N, p, rho, Q) <= hi + 1e-9
    print(f"pair-dependent Q: gap between q_min and q_max gaps in {inside}/{trials} random cases (N=5)")
    assert inside == trials
    L.append(rf"\def\PairDepInside{{{inside}}}\def\PairDepTrials{{{trials}}}")
    DEST.write_text("\n".join(L) + "\n")

if __name__ == "__main__":
    main()
