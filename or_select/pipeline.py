"""End-to-end OR-Select pipeline for a single query.

    python3 -m or_select.pipeline --query "What is the capital of France?" --n 10
    python3 -m or_select.pipeline --query "..." --n 10 --provider openai
    python3 -m or_select.pipeline --query "..." --n 10 --provider openrouter
    python3 -m or_select.pipeline --query "..." --n 10 --provider both   # openai + gemini
"""

from __future__ import annotations

import argparse
import re

from .core import Candidate, SelectionResult, run_dir, write_json
from .generate import generate_candidates, generate_candidates_heterogeneous
from .pairwise import build_pairwise_matrix
from .scoring import score_candidates
from .selection import aggregate_quality, select_best

PROVIDERS = ("placeholder", "openai", "gemini", "openrouter", "both")


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


def _resolve_backends(provider: str):
    """Return (generate_fn, score_fn, judge_fn) for a single-provider run."""
    if provider == "placeholder":
        return _echo_generate_fn, _length_score_fn, _prefix_judge_fn
    from . import providers

    if provider == "openai":
        return providers.openai_generate, providers.openai_score, providers.openai_judge
    if provider == "gemini":
        return providers.gemini_generate, providers.gemini_score, providers.gemini_judge
    if provider == "openrouter":
        return providers.openrouter_generate, providers.openrouter_score, providers.openrouter_judge
    raise ValueError(f"unknown provider: {provider!r} (choose from {PROVIDERS})")


def run_pipeline(
    query: str,
    n: int = 10,
    provider: str = "placeholder",
    generate_fn=None,
    score_fn=None,
    judge_fn=None,
) -> SelectionResult:
    if provider == "both":
        from . import providers

        backends = [("openai", providers.openai_generate), ("gemini", providers.gemini_generate)]
        candidates = generate_candidates_heterogeneous(query, backends, n=n)
        score_fn = score_fn or providers.openai_score
        judge_fn = judge_fn or providers.openai_judge
    else:
        default_generate, default_score, default_judge = _resolve_backends(provider)
        generate_fn = generate_fn or default_generate
        score_fn = score_fn or default_score
        judge_fn = judge_fn or default_judge
        candidates = generate_candidates(query, generate_fn, n=n, source_model=provider)

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
    parser.add_argument("--provider", choices=PROVIDERS, default="placeholder")
    args = parser.parse_args()

    result = run_pipeline(args.query, n=args.n, provider=args.provider)
    out_dir = run_dir(_query_id(args.query))
    write_json(out_dir / "selection.json", result.to_json())
    print(f"winner: {result.winner_text}")
    print(f"scores: {result.scores}")
    print(f"written: {out_dir / 'selection.json'}")


if __name__ == "__main__":
    main()
