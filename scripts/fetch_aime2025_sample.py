"""Fetch AIME 2025 into data/aime_2025_sample.jsonl.

    python3 scripts/fetch_aime2025_sample.py

MathArena/aime_2025 (Hugging Face datasets-server API): the 30 problems of AIME I and II 2025.
Same schema as data/aime_2026_sample.jsonl, so scripts/math_benchmark.py runs it unmodified via
`--input data/aime_2025_sample.jsonl`. It is a second competition-math sitting with integer answers
in [0, 999]; unlike AIME 2026 it predates the model used here, so contamination is possible and the
track is reported as a robustness check, not as an uncontaminated one.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = "MathArena/aime_2025"


def main() -> None:
    url = (
        "https://datasets-server.huggingface.co/rows"
        f"?dataset={DATASET.replace('/', '%2F')}&config=default&split=train&offset=0&length=100"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        rows = [r["row"] for r in json.load(resp)["rows"]]
    out = ROOT / "data" / "aime_2025_sample.jsonl"
    with out.open("w") as f:
        for row in rows:
            f.write(
                json.dumps(
                    {
                        "query": row["problem"],
                        "ground_truth": str(row["answer"]),
                        "subject": "AIME 2025",
                        "unique_id": f"aime_2025_{row['problem_idx']}",
                    }
                )
                + "\n"
            )
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
