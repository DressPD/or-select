"""End-to-end OR-Select pipeline for a single query.

    python3 -m or_select.pipeline --query "What is the capital of France?" --n 10
    python3 -m or_select.pipeline --query "..." --n 10 --provider openai
    python3 -m or_select.pipeline --query "..." --n 10 --provider openrouter
    python3 -m or_select.pipeline --query "..." --n 10 --provider both   # openai + gemini
"""

from __future__ import annotations

import argparse
import re

from .consistency import compute_consistency
from .core import SelectionResult, run_dir, write_json
from .generate import generate_candidates, generate_candidates_heterogeneous
from .pairwise import build_pairwise_matrix
from .scoring import score_candidates
from .selection import aggregate_quality, select_best

PROVIDERS = ("placeholder", "openai", "gemini", "openrouter", "both", "openrouter_mixed")

# Free OpenRouter models spanning distinct vendors/architectures, used by
# --provider openrouter_mixed to test whether candidate diversity -- not
# judge accuracy (ruled out, see docs/reward_bench_preregistration.md: a
# perfect 49/49 on Reasoning-category preference pairs) -- is why every
# same-model benchmark run so far (Tracks A-C) saw almost no disagreement.
# Confirmed to exist via the live OpenRouter /models endpoint, not assumed.
OPENROUTER_MIXED_MODELS = [
    "nvidia/nemotron-3.5-lightning-20260807:free",
    "poolside/laguna-s-2.1:free",
    "liquid/lfm-2.5-2.6b:free",
]
# nvidia/nemotron-3-ultra-550b-a55b:free was delisted from OpenRouter's live
# /models endpoint (confirmed 2026-09-17, surfaced as 404 "Function id ...
# not found" on every call) and replaced with nvidia/nemotron-3.5-lightning
# -20260807:free above, its current free-tier successor.
# google/gemma-4-31b-it:free was tried first but dropped: live testing (Track
# D-heterogeneous, docs/aime_2026_preregistration.md) showed it failing with
# "temporarily rate-limited upstream" on ~4 of 6 consecutive attempts, badly
# enough to sink whole problems even though the other two backends were
# healthy. liquid/lfm-2.5-2.6b:free responded successfully (if slowly) in
# manual smoke testing and was substituted.
#
# z-ai/glm-5.2:free was substituted in next but degraded the same way on
# 2026-08-20 (11/11 calls hit "temporarily rate-limited upstream" across the
# first two problems of the retry-failures resume run) -- confirmed via
# /Users/Q549207/.claude/jobs/efba5254/tmp/aime_2026_hetero_run_resume2.log.
# openai/gpt-oss-20b:free was smoke-tested live (single-call, real API) and
# responded correctly in 4.3s; substituted in as the third distinct-vendor
# backend.
#
# openai/gpt-oss-20b:free was itself dropped on 2026-08-22: OpenRouter
# delisted its free tier entirely -- confirmed both by a live 404
# ("This model is unavailable for free... use this slug instead:
# openai/gpt-oss-20b") on row 7/30 of the retry-failures resume run, and by
# its absence from a fresh /api/v1/models listing (18 free models, this one
# no longer among them). This is a permanent, not transient, failure -- no
# amount of retrying would recover it. poolside/laguna-s-2.1:free was
# smoke-tested live (single-call, real API) same day, responded correctly
# in 5.5s, and substituted in as the third distinct-vendor backend.


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


def resolve_score_judge(provider: str):
    """(score_fn, judge_fn) a provider's pipeline uses; mixed-model generation
    keeps the judge on the single default OpenRouter model."""
    from . import providers

    if provider == "both":
        return providers.openai_score, providers.openai_judge
    if provider == "openrouter_mixed":
        return providers.openrouter_score, providers.openrouter_judge
    _, score_fn, judge_fn = _resolve_backends(provider)
    return score_fn, judge_fn


def select_from_candidates(query: str, candidates, score_fn, judge_fn, validity_fn=None) -> SelectionResult:
    """Everything after generation: confidence scoring, pairwise judging and
    the gated selection MIP. Shared by the live pipeline and by re-judging
    stored candidates, so both paths pick winners identically."""
    candidates = score_candidates(query, candidates, score_fn)
    pairwise = build_pairwise_matrix(query, candidates, judge_fn)
    quality = aggregate_quality(candidates, pairwise)
    consistency = compute_consistency(candidates)
    valid = {c.id: validity_fn(c.text) for c in candidates} if validity_fn is not None else None
    winner_id, scores = select_best(candidates, quality, consistency, valid=valid)
    winner = next(c for c in candidates if c.id == winner_id)
    return SelectionResult(
        query=query,
        winner_id=winner_id,
        winner_text=winner.text,
        scores=scores,
        candidates=candidates,
        pairwise=pairwise,
    )


def run_pipeline(
    query: str,
    n: int = 10,
    provider: str = "placeholder",
    generate_fn=None,
    score_fn=None,
    judge_fn=None,
    validity_fn=None,
) -> SelectionResult:
    if provider == "both":
        from . import providers

        backends = [("openai", providers.openai_generate), ("gemini", providers.gemini_generate)]
        candidates = generate_candidates_heterogeneous(query, backends, n=n, validity_fn=validity_fn)
        score_fn = score_fn or providers.openai_score
        judge_fn = judge_fn or providers.openai_judge
    elif provider == "openrouter_mixed":
        from . import providers

        backends = providers.openrouter_heterogeneous_backends(OPENROUTER_MIXED_MODELS)
        candidates = generate_candidates_heterogeneous(query, backends, n=n, validity_fn=validity_fn)
        # Judge stays on the single model RewardBench validated -- varying
        # generation and judging at once would conflate two different
        # experiments (see docs/aime_2026_preregistration.md's sibling
        # reasoning for why sub-claim 5 needs one variable isolated at a time).
        score_fn = score_fn or providers.openrouter_score
        judge_fn = judge_fn or providers.openrouter_judge
    else:
        default_generate, default_score, default_judge = _resolve_backends(provider)
        generate_fn = generate_fn or default_generate
        score_fn = score_fn or default_score
        judge_fn = judge_fn or default_judge
        candidates = generate_candidates(query, generate_fn, n=n, source_model=provider, validity_fn=validity_fn)

    return select_from_candidates(query, candidates, score_fn, judge_fn, validity_fn)


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
