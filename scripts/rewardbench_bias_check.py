"""Length-bias diagnostic for the RewardBench judge validation: does judge
correctness correlate with which side (chosen/rejected) is the longer
response, independent of which one is actually correct?

    python3 scripts/rewardbench_bias_check.py

Joins data/reward_bench_sample.jsonl (raw chosen/rejected text) with
outputs/reward_bench_benchmark.json (the judge's verdict per row) by id --
zero new API calls, since both files already exist from the RewardBench
run. Backs the length-bias finding reported in the manuscript's judge
validation section (Results, "Judge validation: RewardBench").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from or_select.reward_bench import wilson_interval  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "reward_bench_sample.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "reward_bench_benchmark.json")
    args = parser.parse_args()

    rows_by_id = {}
    for line in args.input.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            rows_by_id[row["id"]] = row

    results = json.loads(args.output.read_text())["results"]
    valid = [r for r in results if "error" not in r]

    buckets = {"chosen_longer": [0, 0], "rejected_longer": [0, 0], "equal_length": [0, 0]}
    for r in valid:
        row = rows_by_id[r["id"]]
        lc, lr = len(row["chosen"]), len(row["rejected"])
        key = "chosen_longer" if lc > lr else "rejected_longer" if lr > lc else "equal_length"
        buckets[key][1] += 1
        buckets[key][0] += r["correct"]

    for key, (k, n) in buckets.items():
        if n == 0:
            print(f"{key}: n/a (0 rows)")
            continue
        lo, hi = wilson_interval(k, n)
        print(f"{key}: accuracy = {100 * k / n:.1f}% ({k}/{n})  95% CI [{100 * lo:.1f}%, {100 * hi:.1f}%]")


if __name__ == "__main__":
    main()
