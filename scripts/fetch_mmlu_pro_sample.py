"""Fetch a deterministic 100-question MMLU-Pro sample into data/mmlu_pro_sample.jsonl.

    python3 scripts/fetch_mmlu_pro_sample.py

TIGER-Lab/MMLU-Pro (test split, 12,032 questions, up to 10 options) via the Hugging Face
datasets-server API. The split is stored in subject blocks, so the sample takes 5 consecutive
questions at each of 20 evenly spaced offsets: 12 of the 14 subjects are represented, and the choice does
not depend on any model output. Options are rendered as a lettered list inside `query`, so
all N candidates for a question see the identical option mapping (same convention as GPQA).
Output schema matches data/gpqa_diamond_sample.jsonl: query, ground_truth (letter), subject, unique_id.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from or_select.mmlu_pro import format_question  # noqa: E402

DATASET = "TIGER-Lab/MMLU-Pro"
TOTAL = 12032
N_OFFSETS = 20
PER_OFFSET = 5


def fetch(offset: int, length: int) -> list[dict]:
    url = (
        "https://datasets-server.huggingface.co/rows"
        f"?dataset={DATASET.replace('/', '%2F')}&config=default&split=test&offset={offset}&length={length}"
    )
    with urllib.request.urlopen(url, timeout=60) as resp:
        return [r["row"] for r in json.load(resp)["rows"]]


def main() -> None:
    step = TOTAL // N_OFFSETS
    rows: list[dict] = []
    for k in range(N_OFFSETS):
        rows.extend(fetch(k * step + step // 2, PER_OFFSET))
    out = ROOT / "data" / "mmlu_pro_sample.jsonl"
    with out.open("w") as f:
        for r in rows:
            f.write(
                json.dumps(
                    {
                        "query": format_question(r["question"], r["options"]),
                        "ground_truth": r["answer"],
                        "subject": r["category"],
                        "unique_id": f"mmlu_pro_{r['question_id']}",
                    }
                )
                + "\n"
            )
    cats = {}
    for r in rows:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print(f"wrote {len(rows)} rows to {out}; subjects: {cats}")


if __name__ == "__main__":
    main()
