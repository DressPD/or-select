"""Fetch AIME 2026 into data/aime_2026_sample.jsonl.

    python3 scripts/fetch_aime_sample.py

MathArena/aime_2026 (verified via Hugging Face datasets-server API): the 30
problems of AIME I and AIME II 2026 (15 each), the most recent American
Invitational Mathematics Examination sittings as of this writing. Chosen as
a harder, more "trap-prone" alternative to MATH Level 5 (see
docs/aime_2026_preregistration.md): AIME problems are specifically
constructed to have tempting-but-wrong shortcuts, which MATH Level 5 turned
out not to reliably have (docs/hypothesis_validation.md sub-claim 5 stayed
untested there despite 105 graded problems). Being from the current year,
these problems are also about as close to "guaranteed not in training data"
as a competition-math benchmark can get.

AIME answers are always integers in [0, 999] -- unlike MATH Level 5's LaTeX
expressions, this sidesteps the formatting-related grader false negatives
documented for Track C (e.g. \\frac vs \\dfrac, "5" vs "x=5"): exact integer
match after or_select.math_eval's normalization is unambiguous.

Output schema matches data/math_level5_sample.jsonl (query, ground_truth,
subject, unique_id) so scripts/math_benchmark.py works unmodified via
`--input data/aime_2026_sample.jsonl`.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = "MathArena/aime_2026"
SPLIT = "train"


def fetch_all_rows() -> list[dict]:
    url = (
        "https://datasets-server.huggingface.co/rows"
        f"?dataset={DATASET.replace('/', '%2F')}&config=default&split={SPLIT}"
        "&offset=0&length=100"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        payload = json.load(resp)
    return [r["row"] for r in payload["rows"]]


def main() -> None:
    rows = fetch_all_rows()
    output = ROOT / "data" / "aime_2026_sample.jsonl"
    with output.open("w") as f:
        for row in rows:
            f.write(
                json.dumps(
                    {
                        "query": row["problem"],
                        "ground_truth": str(row["answer"]),
                        "subject": "AIME 2026",
                        "unique_id": f"aime_2026_{row['problem_idx']}",
                    }
                )
                + "\n"
            )
    print(f"wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
