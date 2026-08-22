"""Fetch GPQA Diamond into data/gpqa_diamond_sample.jsonl.

    python3 scripts/fetch_gpqa_sample.py

GPQA (Rein et al., COLM 2024, arXiv:2311.12022) is released as a
password-protected zip on GitHub specifically to deter scraping and
training-data contamination -- the password is published openly in the
repo's own README as the intended access path for legitimate research use,
not a real access control (see README excerpt below); this is not a
credential to keep secret, it is the documented distribution mechanism.
Deliberately fetched from the GitHub zip rather than the Hugging Face
mirror, which additionally requires a gated/authenticated HF account.

Because of that same contamination-prevention intent, this script's OUTPUT
(data/gpqa_diamond_sample.jsonl) is .gitignore'd, unlike
data/aime_2026_sample.jsonl and data/math_level5_sample.jsonl -- re-run
this script to regenerate it locally rather than expecting it in git.

Diamond is the 198-question highest-quality subset (of the larger "main"
set): questions where both a non-expert validator got it wrong and an
expert validator confirmed correctness, i.e. hard enough that Google search
plus a non-expert doesn't solve it, but an expert agrees on the right
answer. Format is 4-way multiple choice (1 correct + 3 incorrect answers,
not pre-labeled A-D). This script shuffles each question's 4 options once,
deterministically (seeded by that question's own Record ID, so re-running
this script reproduces byte-identical output), into a fixed A/B/C/D order
and writes the resulting lettered question directly into the `query`
field -- so all N candidates or_select generates for a given problem see
the identical option mapping (the shuffle must not vary per-candidate,
only per-problem).

Output schema matches data/math_level5_sample.jsonl (query, ground_truth,
subject, unique_id) so scripts/gpqa_benchmark.py's shape mirrors
scripts/math_benchmark.py.
"""

from __future__ import annotations

import csv
import io
import json
import random
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_URL = "https://raw.githubusercontent.com/idavidrein/gpqa/main/dataset.zip"
# Published in the GPQA repo's own README.md under "Dataset Download" --
# the intended, documented access path, not a secret being bypassed.
ZIP_PASSWORD = b"deserted-untie-orchid"
CSV_MEMBER = "dataset/gpqa_diamond.csv"

LETTERS = ["A", "B", "C", "D"]


def fetch_rows() -> list[dict]:
    with urllib.request.urlopen(ZIP_URL, timeout=60) as resp:
        zip_bytes = resp.read()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open(CSV_MEMBER, pwd=ZIP_PASSWORD) as f:
            text = io.TextIOWrapper(f, encoding="utf-8")
            return list(csv.DictReader(text))


def _shuffled_options(row: dict) -> tuple[list[str], str]:
    """Return (4 option texts in A/B/C/D order, correct letter).

    Seeded by Record ID so the shuffle is deterministic across re-runs --
    load-bearing: or_select generates N candidates against the same `query`
    text, so every candidate for a given problem must see the same lettering.
    """
    options = [
        row["Correct Answer"].strip(),
        row["Incorrect Answer 1"].strip(),
        row["Incorrect Answer 2"].strip(),
        row["Incorrect Answer 3"].strip(),
    ]
    rng = random.Random(row["Record ID"])
    order = list(range(4))
    rng.shuffle(order)
    shuffled = [options[i] for i in order]
    correct_letter = LETTERS[order.index(0)]
    return shuffled, correct_letter


def main() -> None:
    rows = fetch_rows()
    output = ROOT / "data" / "gpqa_diamond_sample.jsonl"
    with output.open("w") as f:
        for row in rows:
            options, correct_letter = _shuffled_options(row)
            options_block = "\n".join(f"({letter}) {text}" for letter, text in zip(LETTERS, options))
            query = f"{row['Question'].strip()}\n\n{options_block}"
            f.write(
                json.dumps(
                    {
                        "query": query,
                        "ground_truth": correct_letter,
                        "subject": row["High-level domain"],
                        "unique_id": f"gpqa_diamond_{row['Record ID']}",
                    }
                )
                + "\n"
            )
    print(f"wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
