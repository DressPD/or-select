"""Judge-accuracy threshold for beating plurality voting: exact model, simulation check, empirical calibration.

    python3 scripts/judge_threshold_theory.py

Zero API calls. Model (N = 3 candidates, the homogeneous setting): each candidate is correct independently with
probability p; wrong answers are pairwise distinct (the case where voting is weakest on ties); the judge, on a pair
with exactly one correct candidate, prefers the correct one with probability q, and on any other pair picks uniformly;
selection is the Copeland winner of one comparison per pair, ties broken uniformly. Plurality voting picks a correct
answer iff at least two candidates are correct (a three-way tie, one correct, is broken uniformly: 1/3).

Closed forms (proved in the manuscript appendix):
    a1(q) = q^2 + q(1-q)/3          P(correct selected | exactly one correct)
    a2(q) = q^2 + 5q(1-q)/3         P(correct selected | exactly two correct)
    Delta(p,q) = acc_OR - acc_vote = p(1-p) [ (1-p)(2q-1)(q+1) - p(3-2q)(1-q) ]
so the judge beats voting iff p/(1-p) < (2q-1)(q+1) / ((3-2q)(1-q)).

This script (1) checks the closed forms against exhaustive enumeration of the comparison outcomes,
(2) measures p-hat and q-hat on the stored judgments of the homogeneous tracks (q-hat: mean stored pairwise
probability assigned to the correct candidate over pairs with exactly one correct candidate), and
(3) writes manuscript/Theory_data.tex (macros for the threshold table and the empirical rows).
"""

from __future__ import annotations

import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from or_select import gpqa, gsm8k, math_eval, mmlu_pro  # noqa: E402

OUT = ROOT / "outputs"
DEST = ROOT / "manuscript" / "Theory_data.tex"
EXTRACT = {"gsm": gsm8k.extract_answer, "math": math_eval.extract_boxed, "gpqa": gpqa.extract_choice, "mmlu": mmlu_pro.extract_choice}
CORRECT = {"gsm": gsm8k.is_correct, "math": math_eval.is_correct, "gpqa": gpqa.is_correct, "mmlu": mmlu_pro.is_correct}
HOMOG = [
    ("GSM8K", "gsm8k_benchmark_initial.json", "gsm"),
    ("MATH L5", "math_benchmark_full.json", "math"),
    ("AIME 2026", "aime_2026_benchmark.json", "math"),
    ("GPQA Diamond", "gpqa_benchmark.json", "gpqa"),
    ("AIME 2025", "aime_2025_benchmark.json", "math"),
    ("MMLU-Pro", "mmlu_pro_benchmark.json", "mmlu"),
]
HETERO = [
    ("GSM8K", "gsm8k_benchmark_heterogeneous.json", "gsm"),
    ("MATH L5", "math_benchmark_heterogeneous.json", "math"),
    ("AIME 2026", "aime_2026_heterogeneous.json", "math"),
    ("GPQA Diamond", "gpqa_heterogeneous.json", "gpqa"),
]


def a_k(k: int, q: Fraction) -> Fraction:
    """P(correct selected | k of 3 correct) by exhaustive enumeration of the 3 pair outcomes."""
    if k in (0, 3):
        return Fraction(k // 3)
    correct = [True] * k + [False] * (3 - k)
    pairs = list(itertools.combinations(range(3), 2))
    total = Fraction(0)
    for outcome in itertools.product([0, 1], repeat=3):  # outcome bit 1: first element of the pair wins
        prob = Fraction(1)
        score = [0, 0, 0]
        for (i, j), o in zip(pairs, outcome):
            p_first = q if (correct[i] and not correct[j]) else (1 - q if (correct[j] and not correct[i]) else Fraction(1, 2))
            prob *= p_first if o else 1 - p_first
            score[i if o else j] += 1
        best = max(score)
        top = [i for i in range(3) if score[i] == best]
        total += prob * Fraction(sum(correct[i] for i in top), len(top))
    return total


def acc(p: Fraction, q: Fraction):
    ors = vote = Fraction(0)
    v = [Fraction(0), Fraction(1, 3), Fraction(1), Fraction(1)]
    for k, c in enumerate((1, 3, 3, 1)):
        w = c * p**k * (1 - p) ** (3 - k)
        ors += w * a_k(k, q)
        vote += w * v[k]
    return ors, vote


def delta_closed(p: Fraction, q: Fraction) -> Fraction:
    return p * (1 - p) * ((1 - p) * (2 * q - 1) * (q + 1) - p * (3 - 2 * q) * (1 - q))


def q_star(p: float) -> float:
    """Smallest pairwise accuracy at which the judge ties voting (root of Delta = 0 in q, in (1/2, 1])."""
    lo, hi = 0.5, 1.0
    f = lambda q: (1 - p) * (2 * q - 1) * (q + 1) - p * (3 - 2 * q) * (1 - q)
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return hi


def measure(fname: str, kind: str):
    path = OUT / fname
    if not path.exists():
        return None
    n_cand = n_ok = 0
    mixed = []
    for row in json.loads(path.read_text())["results"]:
        if "error" in row or row.get("judge_version") != "short-answer":
            continue
        ok = [bool(CORRECT[kind](EXTRACT[kind](c["text"]), row["ground_truth"])) for c in row["candidates"]]
        n_cand += len(ok)
        n_ok += sum(ok)
        j = row.get("judgments")
        if not j:
            continue
        for a, b in itertools.permutations(range(len(ok)), 2):
            if ok[a] and not ok[b]:
                mixed.append(j["pairwise"][f"c{a}|c{b}"])
    return n_cand, n_ok, mixed


def main() -> None:
    # (1) closed form vs enumeration on a grid
    for p in (Fraction(i, 10) for i in range(1, 10)):
        for q in (Fraction(i, 10) for i in range(5, 11)):
            o, v = acc(p, q)
            assert o - v == delta_closed(p, q), (p, q)
    for q in (Fraction(1, 3), Fraction(3, 5), Fraction(4, 5)):
        assert a_k(1, q) == q * q + q * (1 - q) / 3 and a_k(2, q) == q * q + 5 * q * (1 - q) / 3
    print("closed forms agree with exhaustive enumeration on the grid")

    L = ["% Generated by scripts/judge_threshold_theory.py -- do not hand-edit."]
    rows = []
    for p in (0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        rows.append(f"{p:.1f} & {q_star(p):.3f} \\\\")
    L.append(r"\def\ThresholdRows{" + "\n".join(rows) + "}")

    emp = []
    for label, fname, kind in HOMOG:
        m = measure(fname, kind)
        if not m or len(m[2]) < 20:
            continue
        n_cand, n_ok, mixed = m
        p_hat, q_hat = n_ok / n_cand, sum(mixed) / len(mixed)
        emp.append(f"{label} & {p_hat:.3f} & {len(mixed)} & {q_hat:.3f} & {q_star(p_hat):.3f} \\\\")
        print(f"{label:14} p^={p_hat:.3f} q^={q_hat:.3f} (mixed pairs {len(mixed)}) q*={q_star(p_hat):.3f}")
    L.append(r"\def\ThresholdEmpiricalRows{" + "\n".join(emp) + "}")
    het = []
    for label, fname, kind in HETERO:
        m = measure(fname, kind)
        if not m or len(m[2]) < 20:
            continue
        n_cand, n_ok, mixed = m
        het.append(f"{label} & {n_ok / n_cand:.3f} & {len(mixed)} & {sum(mixed) / len(mixed):.3f} \\\\")
        print(f"hetero {label:14} p^={n_ok / n_cand:.3f} q^={sum(mixed) / len(mixed):.3f} (mixed pairs {len(mixed)})")
    L.append(r"\def\ThresholdHeteroRows{" + "\n".join(het) + "}")
    DEST.write_text("\n".join(L) + "\n")
    print("wrote", DEST)


if __name__ == "__main__":
    main()
