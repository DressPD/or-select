"""GPQA Diamond benchmark: OR-Select vs. self-consistency vs. greedy, against ground truth.

    python3 scripts/gpqa_benchmark.py --provider placeholder --n 5   # dry run, no API calls
    python3 scripts/gpqa_benchmark.py --provider openrouter --n 3 --limit 20

Uses data/gpqa_diamond_sample.jsonl (run scripts/fetch_gpqa_sample.py first
-- gitignored, see that script's docstring for why), the full 198-question
Diamond subset of GPQA (Rein et al., COLM 2024). Chosen alongside AIME 2026
as a second unsaturated-benchmark test of hypothesis sub-claim 5
(docs/gpqa_diamond_preregistration.md): Ding (2026, cited throughout this
repo) specifically used GPQA Diamond because it is where the literature
documents frontier models converging confidently on *wrong* answers -- the
"wrong majority, right minority" precondition sub-claim 5 needs, and that
neither MATH Level 5 nor AIME 2026 produced.

Mirrors scripts/math_benchmark.py's structure exactly, swapping
or_select.math_eval's \\boxed{}-extraction/LaTeX-normalizing grader for
or_select.gpqa's exact-letter-match grader (4-way multiple choice has no
formatting ambiguity to introduce grader false negatives, unlike MATH).

For each problem: generate N candidates, run the full OR-Select pipeline,
and separately compute the self-consistency (majority vote over each
candidate's extracted answer letter) and greedy-single-sample baselines
from the same candidate set, plus the exact Kemeny-Young ranking. All
methods are graded against ground truth via or_select.gpqa.is_correct.
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
from or_select.gpqa import GPQA_SUFFIX, extract_choice, is_correct  # noqa: E402
from or_select.providers import MAX_OUTPUT_TOKENS  # noqa: E402
from or_select.rejudge import JUDGE_VERSION, needs_rejudge, rejudge_row  # noqa: E402
from or_select.kemeny import solve_kemeny_ranking  # noqa: E402
from or_select.pipeline import PROVIDERS, run_pipeline  # noqa: E402

METHODS = ("or_select", "self_consistency", "greedy", "kemeny_young")


def _load_problems(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _grade_one(problem: dict, n: int, provider: str) -> dict:
    query = problem["query"] + GPQA_SUFFIX
    ground_truth = problem["ground_truth"]

    result = run_pipeline(
        query, n=n, provider=provider, validity_fn=lambda text: extract_choice(text) is not None
    )

    or_select_answer = extract_choice(result.winner_text)

    sc_winner, had_majority = self_consistency_winner(
        result.candidates, key=lambda c: extract_choice(c.text)
    )
    sc_answer = extract_choice(sc_winner.text)

    greedy_winner = greedy_single_sample(result.candidates)
    greedy_answer = extract_choice(greedy_winner.text)

    kemeny_ranking, kemeny_is_optimal = solve_kemeny_ranking(result.candidates, result.pairwise)
    kemeny_winner = next(c for c in result.candidates if c.id == kemeny_ranking[0])
    kemeny_answer = extract_choice(kemeny_winner.text)

    return {
        "query": problem["query"],
        "ground_truth": ground_truth,
        "judge_version": JUDGE_VERSION,
        "subject": problem.get("subject"),
        "or_select": {"answer": or_select_answer, "correct": is_correct(or_select_answer, ground_truth)},
        "self_consistency": {
            "answer": sc_answer,
            "correct": is_correct(sc_answer, ground_truth),
            "had_majority": had_majority,
        },
        "greedy": {"answer": greedy_answer, "correct": is_correct(greedy_answer, ground_truth)},
        "kemeny_young": {
            "answer": kemeny_answer,
            "correct": is_correct(kemeny_answer, ground_truth),
            "is_optimal": kemeny_is_optimal,
        },
        "winner_texts": {
            "or_select": result.winner_text,
            "self_consistency": sc_winner.text,
            "greedy": greedy_winner.text,
            "kemeny_young": kemeny_winner.text,
        },
        # Full candidate pool, not just the 4 winners -- see
        # scripts/math_benchmark.py's identical field for why.
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
        "subject": problem.get("subject"),
        "error": f"{type(exc).__name__}: {exc}"[:300],
        "or_select": {"answer": None, "correct": False},
        "self_consistency": {"answer": None, "correct": False, "had_majority": False},
        "greedy": {"answer": None, "correct": False},
        "kemeny_young": {"answer": None, "correct": False, "is_optimal": None},
        "winner_texts": None,
        "candidates": None,
    }
    # See scripts/math_benchmark.py's identical block for why.
    last_response = getattr(exc, "last_response", None)
    if last_response is not None:
        row["failed_last_response"] = last_response[:4000]
    if getattr(exc, "truncated", False):
        row["truncated"] = True
        row["truncated_at_tokens"] = MAX_OUTPUT_TOKENS
    return row


def _accuracy_summary(results: list[dict]) -> dict:
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


def _disagreement_summary(results: list[dict]) -> dict:
    """Count problems where OR-Select's winner differs from self-consistency's
    winner, and separately where that divergence changes correctness -- this
    is the direct test of hypothesis sub-claim 5 (can OR-Select correct a
    wrong self-consistency majority)."""
    valid = [r for r in results if "error" not in r]
    disagreements = [r for r in valid if r["or_select"]["answer"] != r["self_consistency"]["answer"]]
    or_select_corrects_sc = [
        r for r in disagreements if r["or_select"]["correct"] and not r["self_consistency"]["correct"]
    ]
    sc_corrects_or_select = [
        r for r in disagreements if r["self_consistency"]["correct"] and not r["or_select"]["correct"]
    ]
    return {
        "n_disagreements": len(disagreements),
        "n_or_select_corrects_self_consistency": len(or_select_corrects_sc),
        "n_self_consistency_corrects_or_select": len(sc_corrects_or_select),
        "disagreement_queries": [r["query"][:80] for r in disagreements],
    }


def _copeland_vs_kemeny_summary(results: list[dict]) -> dict:
    valid = [r for r in results if "error" not in r]
    disagreements = [r for r in valid if r["or_select"]["answer"] != r["kemeny_young"]["answer"]]
    or_select_corrects_kemeny = [
        r for r in disagreements if r["or_select"]["correct"] and not r["kemeny_young"]["correct"]
    ]
    kemeny_corrects_or_select = [
        r for r in disagreements if r["kemeny_young"]["correct"] and not r["or_select"]["correct"]
    ]
    return {
        "n_disagreements": len(disagreements),
        "n_or_select_corrects_kemeny_young": len(or_select_corrects_kemeny),
        "n_kemeny_young_corrects_or_select": len(kemeny_corrects_or_select),
        "disagreement_queries": [r["query"][:80] for r in disagreements],
    }


def _write_output(output: Path, results: list[dict], n: int, provider: str) -> None:
    summary = _accuracy_summary(results)
    disagreement = _disagreement_summary(results)
    copeland_vs_kemeny = _copeland_vs_kemeny_summary(results)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "n_samples": n,
                "provider": provider,
                **summary,
                "disagreement": disagreement,
                "copeland_vs_kemeny": copeland_vs_kemeny,
                "results": results,
            },
            indent=2,
        )
    )


def run_benchmark(
    problems: list[dict],
    n: int,
    provider: str,
    output: Path,
    resume: bool,
    retry_failures: bool = False,
    rejudge: bool = True,
) -> list[dict]:
    results: list[dict] = []
    previous: list[dict] = []
    done_queries: set[str] = set()
    if resume and output.exists():
        existing = json.loads(output.read_text())
        results = existing.get("results", [])
        previous = list(results)
        if retry_failures:
            results = [r for r in results if "error" not in r or is_settled_truncation(r, MAX_OUTPUT_TOKENS)]
        done_queries = {r["query"] for r in results}

    for i, problem in enumerate(problems, start=1):
        if problem["query"] in done_queries:
            idx = next(j for j, r in enumerate(results) if r["query"] == problem["query"])
            existing = results[idx]
            if rejudge and needs_rejudge(existing):
                print(f"[{i}/{len(problems)}] re-judging stored candidates: {problem['query'][:60]!r}", flush=True)
                try:
                    results[idx] = rejudge_row(
                        existing,
                        problem["query"] + GPQA_SUFFIX,
                        provider,
                        extract_choice,
                        is_correct,
                        lambda text: extract_choice(text) is not None,
                    )
                except Exception as exc:  # noqa: BLE001 -- keep the old row, flag it, move on
                    existing["rejudge_error"] = f"{type(exc).__name__}: {exc}"[:300]
                    print(f"    REJUDGE FAILED: {existing['rejudge_error']}", flush=True)
                else:
                    print(f"    judge {existing.get('judge_version', 'v1-reasoning-on')} -> {JUDGE_VERSION}", flush=True)
                _write_output(output, results, n, provider)
            else:
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
                f"    ground_truth={row['ground_truth']!r}  "
                f"OR-Select={marks['or_select']}({row['or_select']['answer']!r})  "
                f"self-consistency={marks['self_consistency']}({row['self_consistency']['answer']!r})  "
                f"greedy={marks['greedy']}({row['greedy']['answer']!r})",
                flush=True,
            )
        results.append(row)
        _write_output(output, results, n, provider)  # incremental: survives a kill mid-run
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "gpqa_diamond_sample.jsonl")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--provider", choices=PROVIDERS, default="placeholder")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "gpqa_benchmark.json")
    parser.add_argument("--limit", type=int, default=None, help="Only run the first LIMIT problems.")
    parser.add_argument("--resume", action="store_true", help="Skip problems already graded in --output.")
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        help="With --resume, re-attempt problems that previously failed to grade instead of skipping them.",
    )
    parser.add_argument(
        "--no-rejudge",
        action="store_true",
        help="With --resume, do not re-judge stored candidates graded by an outdated judge.",
    )
    args = parser.parse_args()

    problems = _load_problems(args.input)
    if args.limit is not None:
        problems = problems[: args.limit]
    results = run_benchmark(
        problems, args.n, args.provider, args.output, args.resume, args.retry_failures, not args.no_rejudge
    )
    _write_output(args.output, results, args.n, args.provider)

    summary = _accuracy_summary(results)
    disagreement = _disagreement_summary(results)
    copeland_vs_kemeny = _copeland_vs_kemeny_summary(results)

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
    print(
        f"  disagreements (OR-Select != self-consistency): {disagreement['n_disagreements']}/{summary['n_valid']}"
    )
    print(f"    OR-Select corrected a wrong SC majority: {disagreement['n_or_select_corrects_self_consistency']}")
    print(f"    SC was right where OR-Select was wrong:  {disagreement['n_self_consistency_corrects_or_select']}")
    print(
        f"  Copeland-approx (OR-Select) vs exact Kemeny-Young: "
        f"{copeland_vs_kemeny['n_disagreements']}/{summary['n_valid']} disagreements"
    )
    print(f"    OR-Select right, Kemeny-Young wrong: {copeland_vs_kemeny['n_or_select_corrects_kemeny_young']}")
    print(f"    Kemeny-Young right, OR-Select wrong: {copeland_vs_kemeny['n_kemeny_young_corrects_or_select']}")
    print(f"written: {args.output}")


if __name__ == "__main__":
    main()
