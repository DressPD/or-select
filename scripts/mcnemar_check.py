"""McNemar exact test (sign test on discordant pairs) for or_select vs.
self_consistency and vice versa against kemeny_young, on one or more
ground-truth track output files.

    python3 scripts/mcnemar_check.py outputs/gpqa_benchmark.json
    python3 scripts/mcnemar_check.py outputs/*.json

Backs the disclosure in the manuscript's Limitations section (Scale): we
pre-registered this test as the direct test of whether OR-Select corrects
self-consistency, and report here -- rather than assume -- how many
discordant pairs currently exist per track, which determines whether the
test is informative at all.
"""

from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path


def mcnemar_exact_p(b: int, c: int) -> float | None:
    """Exact two-sided binomial McNemar test on discordant counts b, c.

    Returns None if there are no discordant pairs (undefined -- there is
    nothing to test), rather than a fabricated p-value.
    """
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    p_tail = sum(comb(n, i) for i in range(0, k + 1)) * (0.5**n)
    return min(1.0, 2 * p_tail)


def discordant_counts(valid: list[dict], method_a: str, method_b: str) -> tuple[int, int]:
    b = sum(1 for r in valid if r[method_a]["correct"] and not r[method_b]["correct"])
    c = sum(1 for r in valid if not r[method_a]["correct"] and r[method_b]["correct"])
    return b, c


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Benchmark output JSON file(s).")
    args = parser.parse_args()

    for path in args.paths:
        data = json.loads(path.read_text())
        valid = [r for r in data["results"] if "error" not in r]
        b, c = discordant_counts(valid, "or_select", "self_consistency")
        p = mcnemar_exact_p(b, c)
        print(
            f"{path}: n_valid={len(valid)}  "
            f"or_select-correct/self_consistency-wrong={b}  "
            f"or_select-wrong/self_consistency-correct={c}  "
            f"exact McNemar p={p}"
        )
        if valid and "kemeny_young" in valid[0]:
            b_ky, c_ky = discordant_counts(valid, "or_select", "kemeny_young")
            p_ky = mcnemar_exact_p(b_ky, c_ky)
            print(
                f"    vs kemeny_young: or_select-correct/ky-wrong={b_ky}  "
                f"or_select-wrong/ky-correct={c_ky}  exact McNemar p={p_ky}"
            )


if __name__ == "__main__":
    main()
