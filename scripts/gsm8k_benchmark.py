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
from or_select.gsm8k import GSM8K_SUFFIX, extract_answer, is_correct  # noqa: E402
from or_select.pipeline import PROVIDERS, run_pipeline  # noqa: E402

METHODS = ("or_select", "self_consistency", "greedy")


def _load_problems(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _grade_one(problem: dict, n: int, provider: str) -> dict:
    query = problem["query"] + GSM8K_SUFFIX
    ground_truth = problem["ground_truth"]

    result = run_pipeline(query, n=n, provider=provider)

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
    }


def _failed_row(problem: dict, exc: Exception) -> dict:
    """Explicit failure record: one problem's persistent API failure must not
    silently drop it or kill the rest of the batch (README's design boundary:
    failed candidates remain explicit failures, never silently dropped)."""
    return {
        "query": problem["query"],
        "ground_truth": problem["ground_truth"],
        "error": f"{type(exc).__name__}: {exc}"[:300],
        "or_select": {"answer": None, "correct": False},
        "self_consistency": {"answer": None, "correct": False, "had_majority": False},
        "greedy": {"answer": None, "correct": False},
    }


def _write_output(output: Path, results: list[dict], n: int, provider: str) -> None:
    n_total = len(results)
    accuracy = {m: sum(1 for r in results if r[m]["correct"]) / n_total for m in METHODS} if n_total else {}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {"n_problems": n_total, "n_samples": n, "provider": provider, "accuracy": accuracy, "results": results},
            indent=2,
        )
    )


def run_benchmark(
    problems: list[dict], n: int, provider: str, output: Path, resume: bool
) -> list[dict]:
    results: list[dict] = []
    done_queries: set[str] = set()
    if resume and output.exists():
        existing = json.loads(output.read_text())
        results = existing.get("results", [])
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
    args = parser.parse_args()

    problems = _load_problems(args.input)
    if args.limit is not None:
        problems = problems[: args.limit]
    results = run_benchmark(problems, args.n, args.provider, args.output, args.resume)
    _write_output(args.output, results, args.n, args.provider)

    n_total = len(results)
    accuracy = {m: sum(1 for r in results if r[m]["correct"]) / n_total for m in METHODS} if n_total else {}

    print()
    print(f"N problems = {n_total}, samples per problem = {args.n}, provider = {args.provider}")
    for m in METHODS:
        correct = sum(1 for r in results if r[m]["correct"])
        print(f"  {m}: {correct}/{n_total} = {accuracy[m]:.1%}")
    print(f"written: {args.output}")


if __name__ == "__main__":
    main()
