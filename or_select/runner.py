"""Batch runner: OR-Select pipeline over a JSONL file of queries.

    python3 -m or_select.runner --input data/example_queries.jsonl --workers 3
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .core import run_dir, write_json
from .pipeline import _query_id, run_pipeline


def _load_queries(path: Path) -> list[str]:
    queries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        queries.append(json.loads(line)["query"])
    return queries


def _run_one(query: str, n: int) -> None:
    result = run_pipeline(query, n=n)
    out_dir = run_dir(_query_id(query))
    write_json(out_dir / "selection.json", result.to_json())


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-run the OR-Select pipeline.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    queries = _load_queries(args.input)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda q: _run_one(q, args.n), queries))
    print(f"ran {len(queries)} queries -> outputs/runs/")


if __name__ == "__main__":
    main()
