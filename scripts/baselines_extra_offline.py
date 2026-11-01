"""Additional selection baselines, computed offline from stored candidates and judge outputs.

    python3 scripts/baselines_extra_offline.py

Zero API calls. Judge-free selectors run on every graded problem; judge-based selectors run on the
problems whose judge outputs were stored (the same subset the offline weight ablation uses).

  shortest, longest   pick the shortest / longest valid candidate (word count)
  MBR (Jaccard)       minimum-Bayes-risk selection with token-set Jaccard similarity between candidates
  confidence argmax   pointwise best-of-N: highest stored scorer confidence, ties to the first candidate
  confidence vote     plurality vote over extracted answers, each candidate weighted by its confidence
  tournament          sequential knockout over candidate order using the pairwise matrix (incumbent keeps ties)
  Bradley-Terry       strength fitted to the pairwise matrix (Zermelo MM iterations), argmax

Borda over the pairwise matrix equals the Copeland-style quality already reported (Section 5.5), so it is
not repeated. Not run (needs a trained model or live calls): reward-model / process-reward best-of-N and
universal self-consistency. Writes manuscript/Baselines_data.tex.
"""

from __future__ import annotations

import json
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from or_select import gpqa, gsm8k, math_eval, mmlu_pro  # noqa: E402

OUT = ROOT / "outputs"
DEST = ROOT / "manuscript" / "Baselines_data.tex"

EXTRACT = {
    "gsm": gsm8k.extract_answer,
    "math": math_eval.extract_boxed,
    "gpqa": gpqa.extract_choice,
    "mmlu": mmlu_pro.extract_choice,
}
CORRECT = {"gsm": gsm8k.is_correct, "math": math_eval.is_correct, "gpqa": gpqa.is_correct, "mmlu": mmlu_pro.is_correct}
# file, kind, heterogeneous?
TRACKS = [
    ("gsm8k_benchmark_initial.json", "gsm", False),
    ("math_benchmark_full.json", "math", False),
    ("aime_2026_benchmark.json", "math", False),
    ("gpqa_benchmark.json", "gpqa", False),
    ("aime_2025_benchmark.json", "math", False),
    ("mmlu_pro_benchmark.json", "mmlu", False),
    ("gsm8k_benchmark_heterogeneous.json", "gsm", True),
    ("math_benchmark_heterogeneous.json", "math", True),
    ("aime_2026_heterogeneous.json", "math", True),
    ("gpqa_heterogeneous.json", "gpqa", True),
]
SELECTORS = [
    ("shortest", "Shortest candidate", False),
    ("longest", "Longest candidate", False),
    ("mbr", "MBR (Jaccard)", False),
    ("conf_argmax", "Confidence argmax", True),
    ("conf_vote", "Confidence-weighted vote", True),
    ("tournament", "Knockout tournament", True),
    ("bt", "Bradley--Terry", True),
]


def mcnemar_p(b: int, c: int):
    n = b + c
    return None if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) * 0.5**n)


def fmt_p(p):
    return "--" if p is None else ("$<$0.001" if p < 0.001 else f"{p:.3f}")


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def bradley_terry(w: dict, n: int, iters: int = 200) -> list[float]:
    s = [1.0] * n
    for _ in range(iters):
        new = []
        for i in range(n):
            wins = sum(w[(i, j)] for j in range(n) if j != i)
            denom = sum(1.0 / (s[i] + s[j]) for j in range(n) if j != i)
            new.append(max(wins, 1e-9) / denom)
        tot = sum(new)
        s = [x * n / tot for x in new]
    return s


def pick(row: dict, kind: str, name: str) -> int | None:
    """Index of the selected candidate, or None if the selector cannot run on this row."""
    cands = row["candidates"]
    ext = EXTRACT[kind]
    valid = [i for i, c in enumerate(cands) if ext(c["text"]) is not None] or list(range(len(cands)))
    words = [len(c["text"].split()) for c in cands]
    if name == "shortest":
        return min(valid, key=lambda i: (words[i], i))
    if name == "longest":
        return max(valid, key=lambda i: (words[i], -i))
    if name == "mbr":
        toks = [set(c["text"].split()) for c in cands]
        return max(valid, key=lambda i: (sum(jaccard(toks[i], toks[j]) for j in valid if j != i), -i))
    j = row.get("judgments")
    if not j or row.get("judge_version") != "short-answer":
        return None
    conf = [j["confidence"][f"c{i}"] for i in range(len(cands))]
    if name == "conf_argmax":
        return max(valid, key=lambda i: (conf[i], -i))
    if name == "conf_vote":
        score: dict[str, float] = {}
        for i in valid:
            key = str(ext(cands[i]["text"]))
            score[key] = score.get(key, 0.0) + conf[i]
        best = max(score, key=lambda k: (score[k], k == str(ext(cands[valid[0]]["text"]))))
        return next(i for i in valid if str(ext(cands[i]["text"])) == best)
    pair = {tuple(int(x[1:]) for x in k.split("|")): v for k, v in j["pairwise"].items()}
    if name == "tournament":
        king = valid[0]
        for i in valid[1:]:
            if pair[(i, king)] > pair[(king, i)]:
                king = i
        return king
    if name == "bt":
        n = len(cands)
        strengths = bradley_terry(pair, n)
        return max(valid, key=lambda i: (strengths[i], -i))
    raise ValueError(name)


def main() -> None:
    acc = {het: {s[0]: [] for s in SELECTORS} for het in (False, True)}  # lists of (selector correct, SC correct)
    for fname, kind, het in TRACKS:
        path = OUT / fname
        if not path.exists():
            continue
        for row in json.loads(path.read_text())["results"]:
            if "error" in row or row.get("judge_version") != "short-answer":
                continue
            for name, _label, _needs in SELECTORS:
                idx = pick(row, kind, name)
                if idx is None:
                    continue
                ok = bool(CORRECT[kind](EXTRACT[kind](row["candidates"][idx]["text"]), row["ground_truth"]))
                acc[het][name].append((ok, bool(row["self_consistency"]["correct"])))
    L = ["% Generated by scripts/baselines_extra_offline.py from outputs/*.json -- do not hand-edit."]
    rows_tex = []
    for name, label, needs in SELECTORS:
        cells = []
        for het in (False, True):
            pairs = acc[het][name]
            n = len(pairs)
            if n == 0:
                cells.append("-- & -- & -- & --")
                continue
            a = 100 * sum(o for o, _ in pairs) / n
            sc = 100 * sum(s for _, s in pairs) / n
            b = sum(1 for o, s in pairs if o and not s)
            c = sum(1 for o, s in pairs if s and not o)
            cells.append(f"{n} & {a:.1f} ({sc:.1f}) & {b}/{c} & {fmt_p(mcnemar_p(b, c))}")
            tag = "Het" if het else "Hom"
            L.append(rf"\def\Base{tag}{name.replace('_', '')}Acc{{{a:.1f}}}")
            L.append(rf"\def\Base{tag}{name.replace('_', '')}N{{{n}}}")
            L.append(rf"\def\Base{tag}{name.replace('_', '')}B{{{b}}}")
            L.append(rf"\def\Base{tag}{name.replace('_', '')}C{{{c}}}")
            print(f"{'hetero' if het else 'homog ':6} {label:26} n={n:4} acc={a:5.1f} (SC {sc:5.1f}) wins {b}/{c} p={fmt_p(mcnemar_p(b, c))}")
        rows_tex.append(f"{label}{'$^\\dagger$' if needs else ''} & " + " & ".join(cells) + " \\\\")
    L.append(r"\def\BaselineTableRows{" + "\n".join(rows_tex) + "}")
    DEST.write_text("\n".join(L) + "\n")
    print("wrote", DEST)


if __name__ == "__main__":
    main()
