"""Vote-then-judge rule (result B): exact optimality under the finite-pool model, and an offline audit on stored runs.

    python3 scripts/hybrid_rule.py

Zero API calls. Rule H ("vote, then judge only on ties"): return an answer repeated by the most candidates; if several
answers tie for the most votes, run binary Copeland on the comparisons among the tied candidates only.

Model (as judge_threshold_theory, any N): candidates are independently correct with probability p, correct candidates
share one answer, wrong answers are pairwise distinct, the judge prefers the correct candidate on a mixed pair with
probability q >= 1/2 and picks uniformly on any other pair, independently across pairs.
Claims checked here by exhaustive enumeration (exact rational arithmetic for N <= 4, floats for N = 5, 6):
  (i)  H attains the Bayes-optimal accuracy: the maximum over all rules that see the answer partition and the
       comparison outcomes, which is  P(k >= 2) + N p (1-p)^(N-1) a1_N(q);
  (ii) H >= plurality and H >= Copeland for every p and every q >= 1/2 (no break-even threshold).
Then (iii) the stored-run audit: H against stored self-consistency (ties to the first candidate), Copeland alone and the
stored OR-Select winner, with paired exact tests, on every graded problem whose judge outputs were stored.
Writes manuscript/Hybrid_data.tex.
"""

from __future__ import annotations

import itertools
import json
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import judge_threshold_theory as th  # noqa: E402

DEST = ROOT / "manuscript" / "Hybrid_data.tex"


def copeland_correct_prob(n: int, k: int, q):
    """P(selected candidate is correct | k of n correct), Copeland with uniform ties, one comparison per pair."""
    ok = [True] * k + [False] * (n - k)
    pairs = list(itertools.combinations(range(n), 2))
    total = 0 * q
    for outcome in itertools.product([0, 1], repeat=len(pairs)):
        prob = 1 + 0 * q
        score = [0] * n
        for (i, j), o in zip(pairs, outcome):
            pf = q if (ok[i] and not ok[j]) else (1 - q if (ok[j] and not ok[i]) else (1 + 0 * q) / 2)
            prob *= pf if o else 1 - pf
            score[i if o else j] += 1
        top = [i for i in range(n) if score[i] == max(score)]
        total += prob * sum(ok[i] for i in top) / len(top)
    return total


def accuracies(n: int, p, q):
    """(plurality, Copeland, hybrid) accuracy under the model."""
    w = [comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1)]
    plur = sum(w[k] * (1 if k >= 2 else (0 if k == 0 else 1 / n if isinstance(p, float) else Fraction(1, n))) for k in range(n + 1))
    cop = sum(w[k] * (copeland_correct_prob(n, k, q) if 0 < k < n else (1 if k == n else 0)) for k in range(n + 1))
    hyb = sum(w[k] * (1 if k >= 2 else (copeland_correct_prob(n, 1, q) if k == 1 else 0)) for k in range(n + 1))
    return plur, cop, hyb


def bayes_optimal(n: int, p, q):
    """Max over all rules seeing (answer partition, comparison outcomes): sum over observations of max_i P(i correct, obs)."""
    pairs = list(itertools.combinations(range(n), 2))
    obs_mass: dict[tuple, list] = {}
    for c in itertools.product([0, 1], repeat=n):
        k = sum(c)
        prior = p**k * (1 - p) ** (n - k)
        agree = tuple(i for i in range(n) if c[i]) if k >= 2 else ()
        for outcome in itertools.product([0, 1], repeat=len(pairs)):
            lik = 1 + 0 * q
            for (i, j), o in zip(pairs, outcome):
                pf = q if (c[i] and not c[j]) else (1 - q if (c[j] and not c[i]) else (1 + 0 * q) / 2)
                lik *= pf if o else 1 - pf
            slot = obs_mass.setdefault((agree, outcome), [0 * q] * n)
            for i in range(n):
                if c[i]:
                    slot[i] += prior * lik
    return sum(max(m) for m in obs_mass.values())


def verify_theory() -> list[str]:
    for n in (3, 4):
        for p in (Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)):
            for q in (Fraction(1, 2), Fraction(3, 5), Fraction(4, 5), Fraction(1)):
                plur, cop, hyb = accuracies(n, p, q)
                assert bayes_optimal(n, p, q) == hyb, (n, p, q)
                assert hyb >= plur and hyb >= cop, (n, p, q)
    for n in (5, 6):
        for p in (0.2, 0.5, 0.8):
            for q in (0.5, 0.65, 0.9):
                plur, cop, hyb = accuracies(n, p, q)
                assert hyb >= plur - 1e-12 and hyb >= cop - 1e-12, (n, p, q)
    print("verified: hybrid = Bayes-optimal (N=3,4 exact), hybrid >= plurality and Copeland (N=3..6), q in [1/2, 1]")
    rows = []
    print("N | p | q | plurality | Copeland | hybrid")
    for n in (3, 6):
        for p in (0.3, 0.6, 0.85):
            for q in (0.6, 0.8):
                plur, cop, hyb = accuracies(n, p, q)
                print(f"{n} | {p} | {q} | {plur:.3f} | {cop:.3f} | {hyb:.3f}")
                rows.append(f"{n} & {p:.2f} & {q:.1f} & {100 * float(plur):.1f} & {100 * float(cop):.1f} & {100 * float(hyb):.1f} \\\\")
    return rows


# ---- empirical audit on stored runs ----------------------------------------------------------------------------
TRACKS = [
    ("MATH L5", "math_benchmark_full.json", "math", False),
    ("AIME 2026", "aime_2026_benchmark.json", "math", False),
    ("AIME 2025", "aime_2025_benchmark.json", "math", False),
    ("MMLU-Pro", "mmlu_pro_benchmark.json", "mmlu", False),
    ("GSM8K", "gsm8k_benchmark_initial.json", "gsm", False),
    ("MATH L5", "math_benchmark_heterogeneous.json", "math", True),
    ("AIME 2026", "aime_2026_heterogeneous.json", "math", True),
    ("GSM8K", "gsm8k_benchmark_heterogeneous.json", "gsm", True),
]


def mcnemar_p(b: int, c: int):
    n = b + c
    return None if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) * 0.5**n)


def select(row, kind):
    """(hybrid index, copeland index, tie among leaders?) with deterministic first-index tie breaks."""
    cands = row["candidates"]
    n = len(cands)
    ext = th.EXTRACT[kind]
    ans = [ext(c["text"]) for c in cands]
    valid = [i for i in range(n) if ans[i] is not None] or list(range(n))
    counts: dict[str, int] = {}
    for i in valid:
        counts[str(ans[i])] = counts.get(str(ans[i]), 0) + 1
    top = max(counts.values())
    leaders = [a for a, c in counts.items() if c == top]
    pair = row["judgments"]["pairwise"]

    def win(i, j):
        v = pair[f"c{i}|c{j}"]
        return 1.0 if v > 0.5 else (0.5 if v == 0.5 else 0.0)

    def copeland(pool):
        score = {i: sum(win(i, j) for j in pool if j != i) for i in pool}
        return max(pool, key=lambda i: (score[i], -i))

    cop = copeland(valid)
    pool = [i for i in valid if str(ans[i]) in leaders]
    tie = len(leaders) > 1
    hyb = copeland(pool) if tie else min(pool)
    # unordered pairs the judge must compare: Rule H only inside the tied pool, Copeland over every valid candidate
    pairs_h = len(pool) * (len(pool) - 1) // 2 if tie else 0
    pairs_c = len(valid) * (len(valid) - 1) // 2
    return hyb, cop, tie, pairs_h, pairs_c


def audit():
    stats: dict[tuple, dict] = {}
    for label, fname, kind, het in TRACKS:
        path = th.OUT / fname
        if not path.exists():
            continue
        for row in json.loads(path.read_text())["results"]:
            if "error" in row or row.get("judge_version") != "short-answer" or not row.get("judgments"):
                continue
            ok = [bool(th.CORRECT[kind](th.EXTRACT[kind](c["text"]), row["ground_truth"])) for c in row["candidates"]]
            hyb, cop, tie, pairs_h, pairs_c = select(row, kind)
            rec = {
                "pairs_h": pairs_h, "pairs_c": pairs_c,
                "hyb": ok[hyb], "cop": ok[cop], "sc": bool(row["self_consistency"]["correct"]),
                "ors": bool(row["or_select"]["correct"]) if isinstance(row.get("or_select"), dict) and "correct" in row["or_select"] else None,
                "tie": tie, "opp": tie and any(ok[i] for i in range(len(ok))),
            }
            for key in ((het, label), (het, "All")):
                stats.setdefault(key, {"rows": []})["rows"].append(rec)
    return stats


def main() -> None:
    table = verify_theory()
    stats = audit()
    L = ["% Generated by scripts/hybrid_rule.py -- do not hand-edit.", r"\def\HybridTheoryRows{" + "\n".join(table) + "}"]
    out = []
    print("\ntrack | n | ties | tie&correct-present | SC | Copeland | hybrid | hybrid vs SC (b/c, p) | hybrid vs Copeland (b/c, p) | OR-Select")
    for (het, label), v in sorted(stats.items(), key=lambda kv: (kv[0][0], kv[0][1] == "All", kv[0][1])):
        r = v["rows"]
        n = len(r)
        f = lambda key: 100 * sum(x[key] for x in r) / n  # noqa: E731
        b_sc = sum(1 for x in r if x["hyb"] and not x["sc"])
        c_sc = sum(1 for x in r if x["sc"] and not x["hyb"])
        b_cp = sum(1 for x in r if x["hyb"] and not x["cop"])
        c_cp = sum(1 for x in r if x["cop"] and not x["hyb"])
        ties = sum(x["tie"] for x in r)
        opp = sum(x["opp"] for x in r)
        ors = [x["ors"] for x in r if x["ors"] is not None]
        ors_s = f"{100 * sum(ors) / len(ors):.1f}" if len(ors) == n else "--"
        p1, p2 = mcnemar_p(b_sc, c_sc), mcnemar_p(b_cp, c_cp)
        fp = lambda p: "--" if p is None else ("$<$0.001" if p < 0.001 else f"{p:.3f}")  # noqa: E731
        tag = "Het" if het else "Hom"
        print(f"{'het' if het else 'hom'} {label:10} n={n:3} ties={ties:3} opp={opp:3} SC={f('sc'):.1f} Cop={f('cop'):.1f} Hyb={f('hyb'):.1f} "
              f"| H vs SC {b_sc}/{c_sc} p={fp(p1)} | H vs Cop {b_cp}/{c_cp} p={fp(p2)} | OR-Select {ors_s}")
        out.append(f"{'Het.' if het else 'Hom.'} {label} & {n} & {ties}/{opp} & {f('sc'):.1f} & {f('cop'):.1f} & {f('hyb'):.1f} & {b_sc}/{c_sc} ({fp(p1)}) & {b_cp}/{c_cp} ({fp(p2)}) \\\\")
        if label == "All":
            for name, val in (("N", n), ("Ties", ties), ("Opp", opp), ("SC", round(f("sc"), 1)), ("Cop", round(f("cop"), 1)),
                              ("Hyb", round(f("hyb"), 1)), ("BSC", b_sc), ("CSC", c_sc), ("BCop", b_cp), ("CCop", c_cp)):
                L.append(rf"\def\Hyb{tag}{name}{{{val}}}")
            L.append(rf"\def\Hyb{tag}PSC{{{fp(p1)}}}")
            L.append(rf"\def\Hyb{tag}PCop{{{fp(p2)}}}")
            share = 100 * sum(x["pairs_h"] for x in r) / sum(x["pairs_c"] for x in r)
            L.append(rf"\def\Hyb{tag}CallShare{{{share:.1f}}}")
            L.append(rf"\def\Hyb{tag}CallsHPerK{{{round(1000 * sum(x['pairs_h'] for x in r) / n):,}}}".replace(",", "{,}"))
            L.append(rf"\def\Hyb{tag}CallsCPerK{{{round(1000 * sum(x['pairs_c'] for x in r) / n):,}}}".replace(",", "{,}"))
            L.append(rf"\def\Hyb{tag}CallSaved{{{100 - share:.1f}}}")
            print(f"   judge comparisons: Rule H uses {share:.1f}% of those Copeland-everywhere needs")
    L.append(r"\def\HybridAuditRows{" + "\n".join(out) + "}")
    DEST.write_text("\n".join(L) + "\n")
    print("wrote", DEST)


if __name__ == "__main__":
    main()
