"""Margin-gated judging under colliding wrong answers (result C): exact accuracy and judge cost.

    python3 scripts/collision_model.py

Zero API calls. Extends the finite-pool model: each of N candidates is correct with probability p; a wrong candidate
repeats one shared "attractor" distractor with probability s and otherwise gives an answer nobody else gives. With s = 0
this is the earlier model. A binary judge compares one representative of each of two answer classes: it prefers the
correct one with probability q >= 1/2 when exactly one class is correct, and a fair coin otherwise.

Rule G_t (margin-gated duel): let m1 >= m2 be the sizes of the two largest answer classes (ties broken uniformly). If
m1 - m2 > t return the largest class; otherwise run ONE judge comparison between the two largest classes. G_0 judges only
on exact ties for first place, G_inf always judges the top two classes. Plurality never judges. Exact enumeration over
the multinomial counts (k correct, a attractor, u unique wrong). Writes manuscript/Collision_data.tex.
"""

from __future__ import annotations

import random
import sys
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "manuscript" / "Collision_data.tex"


def _classes(k: int, a: int, u: int):
    out = [("C", k)] if k else []
    out += [("A", a)] if a else []
    out += [("U", 1)] * u
    return out


def _pick(classes):
    """Uniform choice among the classes of maximal size: list of (index, probability)."""
    top = max(size for _, size in classes)
    idx = [i for i, (_, size) in enumerate(classes) if size == top]
    return [(i, 1 / len(idx)) for i in idx]


def outcome(k: int, a: int, u: int, t, q: float):
    """(P(correct), expected judge calls) for rule G_t on one count vector; t=None is plurality."""
    classes = _classes(k, a, u)
    if len(classes) == 1:
        return (1.0 if classes[0][0] == "C" else 0.0), 0.0
    pc = calls = 0.0
    for i, pi in _pick(classes):
        rest = [c for j, c in enumerate(classes) if j != i]
        for j, pj in _pick(rest):
            w = pi * pj
            m1, m2 = classes[i][1], rest[j][1]
            if t is None or m1 - m2 > t:
                pc += w * (1.0 if classes[i][0] == "C" else 0.0)
            else:
                calls += w
                one_correct = (classes[i][0] == "C") != (rest[j][0] == "C")
                correct_wins = q if one_correct else 0.5
                pc += w * (correct_wins if one_correct else (1.0 if classes[i][0] == "C" or rest[j][0] == "C" else 0.0))
    return pc, calls


def evaluate(n: int, p: float, s: float, q: float, t):
    """Exact (accuracy, expected judge calls per problem) of G_t."""
    acc = cost = 0.0
    for k in range(n + 1):
        for a in range(n - k + 1):
            u = n - k - a
            pr = factorial(n) / (factorial(k) * factorial(a) * factorial(u)) * p**k * ((1 - p) * s) ** a * ((1 - p) * (1 - s)) ** u
            if pr == 0:
                continue
            pc, calls = outcome(k, a, u, t, q)
            acc += pr * pc
            cost += pr * calls
    return acc, cost


def monte_carlo(n, p, s, q, t, reps=200000, seed=7):
    rng = random.Random(seed)
    hit = calls = 0
    for _ in range(reps):
        k = a = 0
        for _ in range(n):
            if rng.random() < p:
                k += 1
            elif rng.random() < s:
                a += 1
        u = n - k - a
        # simulate the rule directly with random tie-breaks
        classes = _classes(k, a, u)
        rng.shuffle(classes)
        classes.sort(key=lambda c: -c[1])
        if len(classes) == 1:
            hit += classes[0][0] == "C"
            continue
        m1, m2 = classes[0][1], classes[1][1]
        if t is None or m1 - m2 > t:
            hit += classes[0][0] == "C"
        else:
            calls += 1
            one = (classes[0][0] == "C") != (classes[1][0] == "C")
            if one:
                hit += rng.random() < q
            else:
                hit += 0 if (classes[0][0] != "C" and classes[1][0] != "C") else 1
    return hit / reps, calls / reps


def check() -> None:
    for (n, p, s, q, t) in [(5, 0.4, 0.5, 0.8, 0), (6, 0.3, 0.8, 0.7, 1), (7, 0.5, 0.3, 0.9, 10**6), (5, 0.4, 0.5, 0.8, None)]:
        ex = evaluate(n, p, s, q, t)
        mc = monte_carlo(n, p, s, q, t)
        assert abs(ex[0] - mc[0]) < 0.006 and abs(ex[1] - mc[1]) < 0.006, (n, p, s, q, t, ex, mc)
    # q = 1/2: judging only on exact ties for first place equals plurality with uniform tie-breaks
    for n in (4, 5, 6):
        for p in (0.2, 0.5):
            for s in (0.0, 0.6):
                assert abs(evaluate(n, p, s, 0.5, 0)[0] - evaluate(n, p, s, 0.5, None)[0]) < 1e-12
    # q = 1 and always-duel can lose to plurality only through a wrong top-two pair (never judge with a missing class)
    print("checks passed: exact enumeration matches Monte Carlo; q=1/2 equals plurality")


def breakeven_q(n: int, p: float, s: float, t, tol=1e-5):
    """Smallest q in [1/2, 1] with G_t accuracy >= plurality accuracy; None if no q in the interval achieves it."""
    base = evaluate(n, p, s, 0.5, None)[0]
    if evaluate(n, p, s, 1.0, t)[0] < base - 1e-12:
        return None
    lo, hi = 0.5, 1.0
    if evaluate(n, p, s, lo, t)[0] >= base - 1e-12:
        return 0.5
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if evaluate(n, p, s, mid, t)[0] >= base - 1e-12:
            hi = mid
        else:
            lo = mid
    return hi


def main() -> None:
    check()
    n = 5
    q = 0.8
    rows = []
    print(f"N={n}, q={q}: accuracy (%) and expected judge calls per problem")
    print("p | s | plurality | G0 acc (calls) | G1 acc (calls) | Ginf acc (calls)")
    for p in (0.3, 0.5, 0.7):
        for s in (0.0, 0.5, 0.9):
            pl = evaluate(n, p, s, q, None)[0]
            g0, c0 = evaluate(n, p, s, q, 0)
            g1, c1 = evaluate(n, p, s, q, 1)
            gi, ci = evaluate(n, p, s, q, 10**6)
            print(f"{p} | {s} | {100 * pl:.1f} | {100 * g0:.1f} ({c0:.2f}) | {100 * g1:.1f} ({c1:.2f}) | {100 * gi:.1f} ({ci:.2f})")
            rows.append(
                f"{p:.1f} & {s:.1f} & {100 * pl:.1f} & {100 * g0:.1f} ({c0:.2f}) & {100 * g1:.1f} ({c1:.2f}) & {100 * gi:.1f} ({ci:.2f}) \\\\"
            )
    print("break-even q of G_inf against plurality (N=5)")
    be_rows = []
    for p in (0.3, 0.5, 0.7):
        cells = []
        for s in (0.0, 0.5, 0.9):
            b = breakeven_q(n, p, s, 10**6)
            cells.append("none" if b is None else f"{b:.2f}")
        print(p, cells)
        be_rows.append(f"{p:.1f} & " + " & ".join(cells) + " \\\\")
    macros = replay()
    DEST.write_text(
        "% generated by scripts/collision_model.py\n" + "\n".join(macros) + "\n"
        f"\\newcommand{{\\CollN}}{{{n}}}\\newcommand{{\\CollQ}}{{{q}}}\n"
        "\\newcommand{\\CollRows}{%\n" + "\n".join(rows) + "}\n"
        "\\newcommand{\\CollBERows}{%\n" + "\n".join(be_rows) + "}\n"
    )
    print("wrote", DEST)


def replay():
    """Per-track replay of plurality (first-index ties), G_0, G_1 and G_inf on stored judgments, plus s-hat and q-hat."""
    import json

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    import judge_threshold_theory as th
    from hybrid_rule import TRACKS, mcnemar_p

    groups: dict = {}
    macros: list[str] = []
    for label, fname, kind, het in TRACKS:
        path = th.OUT / fname
        if not path.exists():
            continue
        for row in json.loads(path.read_text())["results"]:
            if "error" in row or row.get("judge_version") != "short-answer" or not row.get("judgments"):
                continue
            cands = row["candidates"]
            n = len(cands)
            ans = [th.EXTRACT[kind](c["text"]) for c in cands]
            ok = [bool(th.CORRECT[kind](a, row["ground_truth"])) for a in ans]
            valid = [i for i in range(n) if ans[i] is not None] or list(range(n))
            pair = row["judgments"]["pairwise"]

            def win(i, j, pair=pair):
                v = pair[f"c{i}|c{j}"]
                return 1.0 if v > 0.5 else (0.5 if v == 0.5 else 0.0)

            classes: dict = {}
            for i in valid:
                classes.setdefault(str(ans[i]), []).append(i)
            cl = sorted(classes.values(), key=lambda m: (-len(m), min(m)))
            wrong = [i for i in valid if not ok[i]]
            wrong_shared = [i for i in wrong if sum(1 for j in wrong if str(ans[j]) == str(ans[i])) >= 2]

            def duel(a, b, win=win):
                sa = sum(win(i, j) for i in a for j in b) / (len(a) * len(b))
                return a if sa >= 0.5 else b

            def pick(t, cl=cl, duel=duel):
                if len(cl) == 1:
                    return cl[0]
                if t is None or len(cl[0]) - len(cl[1]) > t:
                    return cl[0]
                return duel(cl[0], cl[1])

            rec = {"n": len(valid), "w": len(wrong), "ws": len(wrong_shared), "rows": {}}
            for name, t in (("pl", None), ("g0", 0), ("g1", 1), ("gi", 10**6)):
                rec["rows"][name] = ok[pick(t)[0]]
            hit = tot = 0
            for ai in range(len(cl)):
                for bi in range(ai + 1, len(cl)):
                    ca, cb = ok[cl[ai][0]], ok[cl[bi][0]]
                    if ca != cb:
                        for i in cl[ai]:
                            for j in cl[bi]:
                                w = win(i, j)
                                hit += w if ca else 1 - w
                                tot += 1
            rec["hit"], rec["tot"] = hit, tot
            for key in ((het, label), (het, "All")):
                groups.setdefault(key, []).append(rec)
    print("\nstored-run replay (class duels use the mean stored judgment across member pairs)")
    for (het, label), r in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] == "All", kv[0][1])):
        n = len(r)
        acc = {k: 100 * sum(x["rows"][k] for x in r) / n for k in ("pl", "g0", "g1", "gi")}
        s_hat = sum(x["ws"] for x in r) / max(1, sum(x["w"] for x in r))
        p_hat = 1 - sum(x["w"] for x in r) / sum(x["n"] for x in r)
        q_hat = sum(x["hit"] for x in r) / max(1, sum(x["tot"] for x in r))
        b = sum(1 for x in r if x["rows"]["g1"] and not x["rows"]["pl"])
        c = sum(1 for x in r if x["rows"]["pl"] and not x["rows"]["g1"])
        p = mcnemar_p(b, c)
        print(f"{'het' if het else 'hom'} {label:10} n={n:3} p^={p_hat:.2f} s^={s_hat:.2f} q^={q_hat:.2f} "
              f"PL={acc['pl']:.1f} G0={acc['g0']:.1f} G1={acc['g1']:.1f} Ginf={acc['gi']:.1f} | G1 vs PL {b}/{c} p={p}")
        if label == "All":
            tag = "Het" if het else "Hom"
            pool = 6 if het else 3  # stored pool sizes: heterogeneous N=6, homogeneous N=3
            need = breakeven_q(pool, p_hat, s_hat, 10**6)
            need1 = breakeven_q(pool, p_hat, s_hat, 1)
            fp = "--" if p is None else ("$<$0.001" if p < 0.001 else f"{p:.2f}")
            fmt = lambda v: "none" if v is None else f"{v:.2f}"  # noqa: E731
            macros.extend([
                rf"\def\Coll{tag}N{{{n}}}", rf"\def\Coll{tag}P{{{p_hat:.2f}}}", rf"\def\Coll{tag}S{{{s_hat:.2f}}}",
                rf"\def\Coll{tag}Q{{{q_hat:.2f}}}", rf"\def\Coll{tag}Pl{{{acc['pl']:.1f}}}", rf"\def\Coll{tag}Gone{{{acc['g1']:.1f}}}",
                rf"\def\Coll{tag}Ginf{{{acc['gi']:.1f}}}", rf"\def\Coll{tag}B{{{b}}}", rf"\def\Coll{tag}C{{{c}}}",
                rf"\def\Coll{tag}PV{{{fp}}}", rf"\def\Coll{tag}NeedInf{{{fmt(need)}}}", rf"\def\Coll{tag}NeedOne{{{fmt(need1)}}}",
            ])
            print(f"   required judge accuracy at (p^, s^), N={pool}: always-duel {fmt(need)}, margin-1 {fmt(need1)}")
    return macros


if __name__ == "__main__":
    if "--replay" in sys.argv:
        replay()
    else:
        sys.exit(main())
