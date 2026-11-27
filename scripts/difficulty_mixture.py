"""Difficulty-mixture threshold (result A): problems differ in difficulty, so a pooled accuracy p misstates the break-even judge accuracy.

    python3 scripts/difficulty_mixture.py

Zero API calls. Model of judge_threshold_theory (N = 3, wrong answers distinct, binary mixed-pair judge accuracy q,
Copeland with uniform ties) with the candidate accuracy drawn per problem, p ~ F. Because
    Delta(p, q) = A(q) p (1-p)^2 - B(q) p^2 (1-p),   A = (2q-1)(q+1),  B = (3-2q)(1-q),
the gap between Copeland and plurality is Delta_F(q) = A(q) m1 - B(q) m2 with m1 = E[p(1-p)^2], m2 = E[p^2(1-p)].
The break-even accuracy therefore depends on F only through the effective odds r_F = m2 / m1:  q*_F solves A/B = r_F.

This script (1) checks the closed form against numerical integration for Beta difficulty, (2) tabulates q*_F, and
(3) tests the model on the stored homogeneous judgments: with the measured binary mixed-pair accuracy q-hat, the exact
conditional accuracy a_k(q-hat) for k correct of 3, summed over each problem's own k, predicts binary-Copeland accuracy;
this is compared with the observed binary-Copeland accuracy and with a pooled-p prediction.
Writes manuscript/Mixture_data.tex.
"""

from __future__ import annotations

import itertools
import json
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import judge_threshold_theory as th  # noqa: E402

DEST = ROOT / "manuscript" / "Mixture_data.tex"
VOTE = [0.0, 1 / 3, 1.0, 1.0]  # plurality accuracy given k of 3 correct (wrong answers distinct)


def a_k_float(k: int, q: float) -> float:
    return float(th.a_k(k, Fraction(q).limit_denominator(10**6)))


def A(q: float) -> float:
    return (2 * q - 1) * (q + 1)


def B(q: float) -> float:
    return (3 - 2 * q) * (1 - q)


def beta_moment(alpha: float, beta: float, a: int, b: int) -> float:
    """E[p^a (1-p)^b] for p ~ Beta(alpha, beta)."""
    lb = lambda x, y: math.lgamma(x) + math.lgamma(y) - math.lgamma(x + y)  # noqa: E731
    return math.exp(lb(alpha + a, beta + b) - lb(alpha, beta))


def q_star_mixture(m1: float, m2: float) -> float:
    """Smallest q in (1/2, 1] with A(q) m1 >= B(q) m2."""
    lo, hi = 0.5, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if A(mid) * m1 < B(mid) * m2 else (lo, mid)
    return hi


def check_closed_form() -> None:
    """Delta_F(q) = A m1 - B m2 against midpoint quadrature of Delta(p, q) over Beta densities."""
    for mu, kappa in ((0.6, 2.0), (0.4, 5.0), (0.8, 3.0)):
        alpha, beta = mu * kappa, (1 - mu) * kappa
        lg = math.lgamma(alpha + beta) - math.lgamma(alpha) - math.lgamma(beta)
        n = 40000
        num = 0.0
        for i in range(n):
            p = (i + 0.5) / n
            dens = math.exp(lg + (alpha - 1) * math.log(p) + (beta - 1) * math.log(1 - p))
            for q in (0.55, 0.75, 0.9):
                pass
            num += dens * float(th.delta_closed(Fraction(p).limit_denominator(10**9), Fraction(7, 10))) / n
        m1, m2 = beta_moment(alpha, beta, 1, 2), beta_moment(alpha, beta, 2, 1)
        closed = A(0.7) * m1 - B(0.7) * m2
        assert abs(num - closed) < 2e-4, (mu, kappa, num, closed)
    print("mixture closed form agrees with numerical integration over Beta difficulty")


def threshold_table() -> list[str]:
    rows = []
    print("mean p | kappa | q*(F) | q*(point mass at mean)")
    for mu in (0.4, 0.6, 0.8):
        cells = [f"{mu:.1f}"]
        for kappa in (1.0, 2.0, 5.0, 20.0):
            alpha, beta = mu * kappa, (1 - mu) * kappa
            m1, m2 = beta_moment(alpha, beta, 1, 2), beta_moment(alpha, beta, 2, 1)
            cells.append(f"{q_star_mixture(m1, m2):.3f}")
        cells.append(f"{th.q_star(mu):.3f}")
        rows.append(" & ".join(cells) + r" \\")
        print(" | ".join(cells))
    return rows


def load(fname: str, kind: str):
    path = th.OUT / fname
    if not path.exists():
        return []
    out = []
    for row in json.loads(path.read_text())["results"]:
        if "error" in row or row.get("judge_version") != "short-answer" or not row.get("judgments"):
            continue
        n = len(row["candidates"])
        if n != 3:
            continue
        ok = [bool(th.CORRECT[kind](th.EXTRACT[kind](c["text"]), row["ground_truth"])) for c in row["candidates"]]
        pair = row["judgments"]["pairwise"]
        wins = [0.0] * 3
        mixed = []
        for a, b in itertools.combinations(range(3), 2):
            pab = pair[f"c{a}|c{b}"]
            outcome_a = 1.0 if pab > 0.5 else (0.0 if pab < 0.5 else 0.5)
            wins[a] += outcome_a
            wins[b] += 1 - outcome_a
            if ok[a] != ok[b]:
                mixed.append(outcome_a if ok[a] else 1 - outcome_a)
        best = max(wins)
        top = [i for i in range(3) if wins[i] == best]
        cop = sum(ok[i] for i in top) / len(top)
        ans = [str(th.EXTRACT[kind](c["text"])) for c in row["candidates"]]
        counts = {a: ans.count(a) for a in set(ans)}
        lead = [a for a, c in counts.items() if c == max(counts.values())]
        vote = sum(any(ok[i] for i in range(3) if ans[i] == a) for a in lead) / len(lead)
        out.append({"k": sum(ok), "cop": cop, "vote": vote, "mixed": mixed})
    return out


def predict(rows, q: float):
    return sum(a_k_float(r["k"], q) for r in rows) / len(rows), sum(VOTE[r["k"]] for r in rows) / len(rows)


def naive_predict(p_hat: float, q: float):
    w = [math.comb(3, k) * p_hat**k * (1 - p_hat) ** (3 - k) for k in range(4)]
    return sum(w[k] * a_k_float(k, q) for k in range(4)), sum(w[k] * VOTE[k] for k in range(4))


def qhat(rows) -> float:
    m = [x for r in rows for x in r["mixed"]]
    return sum(m) / len(m)


def analyse(label: str, rows, rng: random.Random):
    n = len(rows)
    nmix = sum(len(r["mixed"]) for r in rows)
    q = qhat(rows)
    p_hat = sum(r["k"] for r in rows) / (3 * n)
    obs_cop = sum(r["cop"] for r in rows) / n
    obs_vote = sum(r["vote"] for r in rows) / n
    pred_cop, pred_vote = predict(rows, q)
    nv_cop, nv_vote = naive_predict(p_hat, q)
    boot_err, boot_gap_err = [], []
    for _ in range(2000):
        s = [rows[rng.randrange(n)] for _ in range(n)]
        if not any(r["mixed"] for r in s):
            continue
        qb = qhat(s)
        pc, pv = predict(s, qb)
        oc = sum(r["cop"] for r in s) / n
        ov = sum(r["vote"] for r in s) / n
        boot_err.append(oc - pc)
        boot_gap_err.append((oc - ov) - (pc - pv))
    boot_err.sort()
    boot_gap_err.sort()
    ci = lambda v: (v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1])  # noqa: E731
    shares = [sum(r["k"] == k for r in rows) / n for k in range(4)]
    res = {
        "label": label, "n": n, "nmix": nmix, "p": p_hat, "q": q, "shares": shares,
        "obs_cop": obs_cop, "pred_cop": pred_cop, "naive_cop": nv_cop,
        "obs_vote": obs_vote, "pred_vote": pred_vote, "naive_vote": nv_vote,
        "err": obs_cop - pred_cop, "err_ci": ci(boot_err),
        "gap_obs": obs_cop - obs_vote, "gap_pred": pred_cop - pred_vote, "gap_naive": nv_cop - nv_vote,
        "gap_err_ci": ci(boot_gap_err),
    }
    print(
        f"{label:14} n={n:3} p^={p_hat:.3f} k-shares={[round(s, 2) for s in shares]} q^={q:.3f} ({nmix} mixed)\n"
        f"   Copeland acc obs {obs_cop:.3f} | pred (own k) {pred_cop:.3f} | pred (pooled p) {nv_cop:.3f} | obs-pred {res['err']:+.3f} CI {res['err_ci'][0]:+.3f}..{res['err_ci'][1]:+.3f}\n"
        f"   plurality acc obs {obs_vote:.3f} | model {pred_vote:.3f} | pooled {nv_vote:.3f}\n"
        f"   gap Copeland-plurality obs {res['gap_obs']:+.3f} | pred (own k) {res['gap_pred']:+.3f} | pred (pooled p) {res['gap_naive']:+.3f}"
    )
    return res


def main() -> None:
    check_closed_form()
    table = threshold_table()
    rng = random.Random(20261127)
    tracks = [("GSM8K", "gsm8k_benchmark_initial.json", "gsm"), ("MATH L5", "math_benchmark_full.json", "math"),
              ("AIME 2026", "aime_2026_benchmark.json", "math"), ("AIME 2025", "aime_2025_benchmark.json", "math"),
              ("MMLU-Pro", "mmlu_pro_benchmark.json", "mmlu")]
    results, pooled = [], []
    for label, fname, kind in tracks:
        rows = load(fname, kind)
        if len(rows) < 8 or sum(len(r["mixed"]) for r in rows) < 10:
            print(f"{label}: skipped ({len(rows)} judged rows)")
            continue
        results.append(analyse(label, rows, rng))
        pooled += rows
    results.append(analyse("Pooled", pooled, rng))
    L = ["% Generated by scripts/difficulty_mixture.py -- do not hand-edit.", r"\def\MixtureThresholdRows{" + "\n".join(table) + "}"]
    body = []
    for r in results:
        body.append(
            f"{r['label']} & {r['n']} & {100 * r['p']:.1f} & {100 * r['q']:.1f} & {100 * r['obs_cop']:.1f} & "
            f"{100 * r['pred_cop']:.1f} & {100 * r['naive_cop']:.1f} & "
            f"{100 * r['gap_obs']:+.1f} & {100 * r['gap_pred']:+.1f} & {100 * r['gap_naive']:+.1f} \\\\"
        )
    L.append(r"\def\MixtureEmpiricalRows{" + "\n".join(body) + "}")
    pr = results[-1]
    L += [rf"\def\MixPooledN{{{pr['n']}}}", rf"\def\MixPooledQ{{{100 * pr['q']:.1f}}}", rf"\def\MixPooledObsCop{{{100 * pr['obs_cop']:.1f}}}",
          rf"\def\MixPooledPredCop{{{100 * pr['pred_cop']:.1f}}}", rf"\def\MixPooledNaiveCop{{{100 * pr['naive_cop']:.1f}}}",
          rf"\def\MixPooledErrLo{{{100 * pr['err_ci'][0]:+.1f}}}", rf"\def\MixPooledErrHi{{{100 * pr['err_ci'][1]:+.1f}}}",
          rf"\def\MixPooledGapObs{{{100 * pr['gap_obs']:+.1f}}}", rf"\def\MixPooledGapPred{{{100 * pr['gap_pred']:+.1f}}}",
          rf"\def\MixPooledGapNaive{{{100 * pr['gap_naive']:+.1f}}}",
          rf"\def\MixPooledObsVote{{{100 * pr['obs_vote']:.1f}}}", rf"\def\MixPooledPredVote{{{100 * pr['pred_vote']:.1f}}}",
          rf"\def\MixPooledNaiveVote{{{100 * pr['naive_vote']:.1f}}}"]
    DEST.write_text("\n".join(L) + "\n")
    print("wrote", DEST)


if __name__ == "__main__":
    main()
