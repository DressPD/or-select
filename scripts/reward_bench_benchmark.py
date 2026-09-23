"""Validate judge_fn against RewardBench's human-labeled preferences.

    python3 scripts/reward_bench_benchmark.py --provider placeholder   # dry run
    python3 scripts/reward_bench_benchmark.py --provider openrouter --resume

Answers a question none of the other benchmark scripts can: is the judge
itself accurate, independent of the OR-Select selection pipeline built on
top of it? gsm8k_benchmark.py and math_benchmark.py test the full pipeline
against ground-truth *answers*; this script tests judge_fn in isolation
against ground-truth *preferences* (RewardBench's human-labeled
chosen/rejected pairs), per docs/methodology.md's "Baselines and
benchmarks" section.

Each row reuses or_select.pairwise.build_pairwise_matrix on exactly two
candidates (chosen, rejected) -- the identical permutation-self-consistency
code path (forward + backward judge calls, averaged) used by the real
pipeline, not a reimplementation, so this measures the actual judge_fn
production code exercises, including its byte-identical-text short-circuit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from or_select.core import Candidate  # noqa: E402
from or_select.pairwise import build_pairwise_matrix  # noqa: E402
from or_select.pipeline import PROVIDERS  # noqa: E402
from or_select.reward_bench import score_summary  # noqa: E402


def _judge_fn_for(provider: str, model: str | None = None):
    if provider == "placeholder":
        return lambda query, a, b: 1.0 if len(a) >= len(b) else 0.0
    from or_select import providers

    if provider == "openrouter_mixed":
        return lambda query, a, b: providers.openrouter_judge(query, a, b, model=model)
    return {
        "openai": providers.openai_judge,
        "gemini": providers.gemini_judge,
        "openrouter": providers.openrouter_judge,
    }[provider]


def _load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _grade_one(row: dict, judge_fn, judge_model: str | None = None) -> dict:
    candidates = [
        Candidate(id="chosen", text=row["chosen"], source_model="ground_truth"),
        Candidate(id="rejected", text=row["rejected"], source_model="ground_truth"),
    ]
    pairwise = build_pairwise_matrix(row["prompt"], candidates, judge_fn)
    weight_chosen = pairwise[("chosen", "rejected")]
    result = {
        "id": row["id"],
        "subset": row["subset"],
        "weight_chosen": weight_chosen,
        "correct": weight_chosen > 0.5,
        "tied": weight_chosen == 0.5,
    }
    if judge_model is not None:
        result["judge_model"] = judge_model
    return result


def _failed_row(row: dict, exc: Exception) -> dict:
    return {
        "id": row["id"],
        "subset": row["subset"],
        "error": f"{type(exc).__name__}: {exc}"[:300],
        "correct": False,
        "tied": False,
    }


def run_benchmark(rows: list[dict], provider: str, output: Path, resume: bool, retry_failures: bool) -> list[dict]:
    # openrouter_mixed round-robins the judge model by row index, one real
    # OpenRouter model per row rather than one model for the whole run --
    # the same "distinct vendor per slot" heterogeneous pattern the other
    # scripts use for candidate generation (pipeline.py's
    # openrouter_heterogeneous_backends), applied here to judging: does the
    # judge_fn accuracy measured against RewardBench's human labels hold up
    # across different judge models, or is it an artifact of the one model
    # used everywhere else in this repo?
    heterogeneous = provider == "openrouter_mixed"
    judge_models: list[str] = []
    if heterogeneous:
        from or_select.pipeline import OPENROUTER_MIXED_MODELS

        judge_models = OPENROUTER_MIXED_MODELS
    else:
        judge_fn = _judge_fn_for(provider)

    results: list[dict] = []
    done_ids: set[int] = set()
    if resume and output.exists():
        existing = json.loads(output.read_text())
        results = existing.get("results", [])
        if retry_failures:
            results = [r for r in results if "error" not in r]
        done_ids = {r["id"] for r in results}

    for i, row in enumerate(rows, start=1):
        if row["id"] in done_ids:
            print(f"[{i}/{len(rows)}] skipped (already graded): id={row['id']}", flush=True)
            continue
        judge_model = judge_models[(i - 1) % len(judge_models)] if heterogeneous else None
        if heterogeneous:
            judge_fn = _judge_fn_for(provider, model=judge_model)
        print(
            f"[{i}/{len(rows)}] subset={row['subset']!r} id={row['id']}"
            f"{f' judge={judge_model}' if judge_model else ''}...",
            flush=True,
        )
        try:
            result = _grade_one(row, judge_fn, judge_model=judge_model)
        except Exception as exc:  # noqa: BLE001 -- one row's failure must not kill the batch
            result = _failed_row(row, exc)
            print(f"    FAILED: {result['error']}", flush=True)
        else:
            mark = "OK" if result["correct"] else ("TIE" if result["tied"] else "X")
            print(f"    weight(chosen)={result['weight_chosen']:.3f}  {mark}", flush=True)
        results.append(result)
        _write_output(output, results)  # incremental: survives a kill mid-run
    return results


def _write_output(output: Path, results: list[dict]) -> None:
    valid = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    summary = score_summary(valid) if valid else {}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {"n_total": len(results), "n_valid": len(valid), "n_failed": len(failed), **summary, "results": results},
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "reward_bench_sample.jsonl")
    parser.add_argument("--provider", choices=PROVIDERS, default="placeholder")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "reward_bench_benchmark.json")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failures", action="store_true")
    args = parser.parse_args()

    rows = _load_rows(args.input)
    if args.limit is not None:
        rows = rows[: args.limit]
    results = run_benchmark(rows, args.provider, args.output, args.resume, args.retry_failures)
    _write_output(args.output, results)

    valid = [r for r in results if "error" not in r]
    summary = score_summary(valid) if valid else {}
    print()
    print(f"N rows = {len(results)} ({len(valid)} graded, {len(results) - len(valid)} failed)")
    if valid:
        lo, hi = summary["overall_ci95_micro"]
        print(f"Overall accuracy (mean of category means): {summary['overall_accuracy']:.1%}")
        print(f"  (micro-average 95% CI, for reference: [{lo:.1%}, {hi:.1%}])")
        for category, scores in summary["category_scores"].items():
            print(f"  {category}: {scores['accuracy']:.1%} over {scores['n_subsets']} subsets, {scores['n_rows']} rows")
    print(f"written: {args.output}")


if __name__ == "__main__":
    main()
