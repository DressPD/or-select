"""Fetch a stratified sample of RewardBench into data/reward_bench_sample.jsonl.

    python3 scripts/fetch_reward_bench_sample.py
    python3 scripts/fetch_reward_bench_sample.py --per-subset 7

RewardBench (Lambert et al., NAACL 2025 Findings) is a 2985-example
human-labeled pairwise-preference benchmark ("filtered" split), spanning 23
subsets grouped into 4 categories (Chat, Chat Hard, Safety, Reasoning --
see or_select/reward_bench.py for the mapping). Used to validate judge_fn in
isolation against real human preferences, independent of the full OR-Select
selection pipeline (docs/methodology.md's "Baselines and benchmarks"
section proposed this; this script and scripts/reward_bench_benchmark.py
are the implementation).

Sampling: the first `--per-subset` rows of each of the 23 subsets, in the
dataset's own served order -- deterministic, no shuffling, no
cherry-picking, same principle as data/gsm8k_sample.jsonl ("first 40,
deterministically"). Every subset gets equal representation regardless of
its size in the source dataset (math-prm alone has 447 of the 2985 rows;
sampling proportionally to raw count would let it dominate what is supposed
to be one-seventh of one of four categories).
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = "allenai/reward-bench"
SPLIT = "filtered"
PAGE_SIZE = 100
TOTAL_ROWS = 2985  # size of the "filtered" split as of this writing


def _fetch_page(offset: int) -> list[dict]:
    url = (
        "https://datasets-server.huggingface.co/rows"
        f"?dataset={DATASET.replace('/', '%2F')}&config=default&split={SPLIT}"
        f"&offset={offset}&length={PAGE_SIZE}"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        payload = json.load(resp)
    return [r["row"] for r in payload["rows"]]


def fetch_stratified_sample(per_subset: int) -> list[dict]:
    by_subset: dict[str, list[dict]] = defaultdict(list)
    offset = 0
    while offset < TOTAL_ROWS:
        for row in _fetch_page(offset):
            by_subset[row["subset"]].append(row)
        offset += PAGE_SIZE

    sample = []
    for subset in sorted(by_subset):
        rows = by_subset[subset][:per_subset]
        sample.extend(rows)
        print(f"{subset}: {len(rows)}/{len(by_subset[subset])} taken")
    return sample


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-subset", type=int, default=7)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "reward_bench_sample.jsonl")
    args = parser.parse_args()

    sample = fetch_stratified_sample(args.per_subset)
    with args.output.open("w") as f:
        for row in sample:
            f.write(json.dumps(row) + "\n")
    print(f"\nwrote {len(sample)} rows to {args.output}")


if __name__ == "__main__":
    main()
