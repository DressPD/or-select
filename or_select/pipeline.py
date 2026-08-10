"""End-to-end OR-Select pipeline for a single query.

    python3 -m or_select.pipeline --query "What is the capital of France?" --n 10
"""

from __future__ import annotations

import argparse
import re

from .core import Candidate, SelectionResult, run_dir, write_json
from .generate import generate_candidates
from .pairwise import build_pairwise_matrix
from .scoring import score_candidates
from .selection import aggregate_quality, select_best


def _echo_generate_fn(query: str, seed: int) -> str:
    """Placeholder generator: replace with a real LLM call. Deterministic so the
    scaffold is runnable without API credentials."""
    return f"{query} [seed={seed}]"


def _length_score_fn(query: str, text: str) -> float:
    """Placeholder confidence: replace with real calibrated confidence."""
    return min(1.0, len(text) / 50.0)


def _prefix_judge_fn(query: str, text_a: str, text_b: str) -> float:
    """Placeholder judge: replace with an LLM pairwise-preference prompt."""
    return 1.0 if len(text_a) >= len(text_b) else 0.0


def run_pipeline(
    query: str,
    n: int = 10,
    generate_fn=_echo_generate_fn,
    score_fn=_length_score_fn,
    judge_fn=_prefix_judge_fn,
) -> SelectionResult:
    candidates = generate_candidates(query, generate_fn, n=n)
    candidates = score_candidates(query, candidates, score_fn)
    pairwise = build_pairwise_matrix(query, candidates, judge_fn)
    quality = aggregate_quality(candidates, pairwise)
    winner_id, scores = select_best(candidates, quality)
    winner = next(c for c in candidates if c.id == winner_id)
    return SelectionResult(
        query=query, winner_id=winner_id, winner_text=winner.text, scores=scores, candidates=candidates
    )


def _query_id(query: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    return slug[:60] or "query"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the OR-Select pipeline on one query.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--n", type=int, default=10)
    args = parser.parse_args()

    result = run_pipeline(args.query, n=args.n)
    out_dir = run_dir(_query_id(args.query))
    write_json(out_dir / "selection.json", result.to_json())
    print(f"winner: {result.winner_text}")
    print(f"scores: {result.scores}")
    print(f"written: {out_dir / 'selection.json'}")


if __name__ == "__main__":
    main()
