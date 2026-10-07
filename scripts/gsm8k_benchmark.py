"""GSM8K benchmark: OR-Select vs. self-consistency vs. greedy, against ground truth.

    python3 scripts/gsm8k_benchmark.py --provider placeholder --n 5   # dry run, no API calls
    python3 scripts/gsm8k_benchmark.py --provider openrouter --n 5

Uses data/gsm8k_sample.jsonl, a small deterministic sample (first 8
problems) of the real GSM8K test set
(github.com/openai/grade-school-math). Unlike the open-ended queries
used elsewhere in this repo, GSM8K has a single objectively correct
numeric answer per problem, so accuracy here is a checkable fact, not a
judgment call -- see docs/methodology.md's "A concrete finding" section
and the Landesberg (2026) citation on why that distinction matters.

For each problem: generate N candidates, run the full OR-Select
pipeline, and separately compute the self-consistency (majority vote
over each candidate's *extracted numeric answer*, not raw text) and
greedy-single-sample baselines from the same candidate set. All three
methods' answers are graded against ground truth.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from or_select.baselines import greedy_single_sample, self_consistency_winner  # noqa: E402
from or_select.generate import is_settled_truncation, truncation_attempts_so_far  # noqa: E402
from or_select.gsm8k import GSM8K_SUFFIX, extract_answer, is_correct  # noqa: E402
from or_select.providers import MAX_OUTPUT_TOKENS  # noqa: E402
from or_select.rejudge import JUDGE_VERSION  # noqa: E402
from or_select.pipeline import PROVIDERS, run_pipeline  # noqa: E402

METHODS = ("or_select", "self_consistency", "greedy")


def _load_problems(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _grade_one(problem: dict, n: int, provider: str) -> dict:
    query = problem["query"] + GSM8K_SUFFIX
    ground_truth = problem["ground_truth"]

    result = run_pipeline(
        query, n=n, provider=provider, validity_fn=lambda text: extract_answer(text) is not None
    )

    or_select_answer = extract_answer(result.winner_text)

    sc_winner, had_majority = self_consistency_winner(
        result.candidates, key=lambda c: str(extract_answer(c.text))
    )
    sc_answer = extract_answer(sc_winner.text)

    greedy_winner = greedy_single_sample(result.candidates)
    greedy_answer = extract_answer(greedy_winner.text)

    return {
        "query": problem["query"],
        "ground_truth": ground_truth,
        "or_select": {"answer": or_select_answer, "correct": is_correct(or_select_answer, ground_truth)},
        "self_consistency": {
            "answer": sc_answer,
            "correct": is_correct(sc_answer, ground_truth),
            "had_majority": had_majority,
        },
        "greedy": {"answer": greedy_answer, "correct": is_correct(greedy_answer, ground_truth)},
        "judge_version": JUDGE_VERSION,
        # Full candidate pool so the judge-dependent fields can be replayed
        # later without regenerating (see scripts/math_benchmark.py).
        "candidates": [
            {"seed": c.metadata.get("seed"), "source_model": c.source_model, "text": c.text}
            for c in result.candidates
        ],
    }


def _failed_row(problem: dict, exc: Exception) -> dict:
    """Explicit failure record: one problem's persistent API failure must not
    silently drop it or kill the rest of the batch (README's design boundary:
    failed candidates remain explicit failures, never silently dropped)."""
    row = {
        "query": problem["query"],
        "ground_truth": problem["ground_truth"],
        "error": f"{type(exc).__name__}: {exc}"[:300],
        "or_select": {"answer": None, "correct": False},
        "self_consistency": {"answer": None, "correct": False, "had_majority": False},
        "greedy": {"answer": None, "correct": False},
    }
    last_response = getattr(exc, "last_response", None)
    if last_response is not None:
        row["failed_last_response"] = last_response[:4000]
    if getattr(exc, "truncated", False):
        row["truncated"] = True
        row["truncated_at_tokens"] = MAX_OUTPUT_TOKENS
    return row


def _accuracy_summary(results: list[dict]) -> dict:
    """Accuracy over VALID (successfully graded) problems only -- a problem
    that failed to grade at all (API failure) is neither "correct" nor
    "incorrect," and folding it into the denominator as if it were a wrong
    answer would silently understate accuracy and misrepresent an
    infrastructure failure as a modeling result."""
    valid = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    accuracy = {m: (sum(1 for r in valid if r[m]["correct"]) / len(valid)) for m in METHODS} if valid else {}
    return {
        "n_total": len(results),
        "n_valid": len(valid),
        "n_failed": len(failed),
        "n_valid_current_judge": sum(1 for r in valid if r.get("judge_version") == JUDGE_VERSION),
        "accuracy_of_valid": accuracy,
    }


def _write_output(output: Path, results: list[dict], n: int, provider: str) -> None:
    summary = _accuracy_summary(results)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {"n_samples": n, "provider": provider, **summary, "results": results},
            indent=2,
        )
    )


def run_benchmark(
    problems: list[dict], n: int, provider: str, output: Path, resume: bool, retry_failures: bool = False
) -> list[dict]:
    results: list[dict] = []
    previous: list[dict] = []
    done_queries: set[str] = set()
    if resume and output.exists():
        existing = json.loads(output.read_text())
        results = existing.get("results", [])
        previous = list(results)
        if retry_failures:
            # Drop failed rows entirely so they're re-attempted below, rather
            # than being treated as "done" forever just because a row exists.
            results = [r for r in results if "error" not in r or is_settled_truncation(r, MAX_OUTPUT_TOKENS)]
        done_queries = {r["query"] for r in results}

    for i, problem in enumerate(problems, start=1):
        if problem["query"] in done_queries:
            print(f"[{i}/{len(problems)}] skipped (already graded): {problem['query'][:60]!r}", flush=True)
            continue
        print(f"[{i}/{len(problems)}] {problem['query'][:70]!r}...", flush=True)
        try:
            row = _grade_one(problem, n, provider)
        except Exception as exc:  # noqa: BLE001 -- one problem's failure must not kill the batch
            row = _failed_row(problem, exc)
            if row.get("truncated"):
                row["truncation_attempts"] = truncation_attempts_so_far(previous, problem["query"]) + 1
            print(f"    FAILED: {row['error']}", flush=True)
        else:
            marks = {m: ("OK" if row[m]["correct"] else "X") for m in METHODS}
            print(
                f"    ground_truth={row['ground_truth']}  "
                f"OR-Select={marks['or_select']}({row['or_select']['answer']})  "
                f"self-consistency={marks['self_consistency']}({row['self_consistency']['answer']})  "
                f"greedy={marks['greedy']}({row['greedy']['answer']})",
                flush=True,
            )
        results.append(row)
        _write_output(output, results, n, provider)  # incremental: survives a kill mid-run
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "gsm8k_sample.jsonl")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--provider", choices=PROVIDERS, default="placeholder")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "gsm8k_benchmark.json")
    parser.add_argument("--limit", type=int, default=None, help="Only run the first LIMIT problems.")
    parser.add_argument("--resume", action="store_true", help="Skip problems already graded in --output.")
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        help="With --resume, re-attempt problems that previously failed to grade instead of skipping them.",
    )
    args = parser.parse_args()

    problems = _load_problems(args.input)
    if args.limit is not None:
        problems = problems[: args.limit]
    results = run_benchmark(problems, args.n, args.provider, args.output, args.resume, args.retry_failures)
    _write_output(args.output, results, args.n, args.provider)

    summary = _accuracy_summary(results)

    print()
    print(
        f"N problems = {summary['n_total']} "
        f"({summary['n_valid']} graded, {summary['n_failed']} failed to grade -- "
        f"API/infra failures, not incorrect answers), "
        f"samples per problem = {args.n}, provider = {args.provider}"
    )
    for m in METHODS:
        if summary["n_valid"]:
            correct = sum(1 for r in results if "error" not in r and r[m]["correct"])
            print(f"  {m}: {correct}/{summary['n_valid']} = {summary['accuracy_of_valid'][m]:.1%} (of graded problems)")
        else:
            print(f"  {m}: no problems successfully graded")
    print(f"written: {args.output}")


if __name__ == "__main__":
    main()
