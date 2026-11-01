"""MATH Level 5 benchmark: OR-Select vs. self-consistency vs. greedy, against ground truth.

    python3 scripts/math_benchmark.py --provider placeholder --n 5   # dry run, no API calls
    python3 scripts/math_benchmark.py --provider openrouter --n 5 --limit 20

Uses data/math_level5_sample.jsonl, the full Level-5 subset (134 problems)
of MATH-500 (Lightman et al. 2023), fetched via the Hugging Face
datasets-server API. Unlike data/gsm8k_sample.jsonl -- saturated for the
model used in this repo, see the manuscript's headroom analysis --
Level-5 MATH problems are harder competition-style problems, chosen
specifically because the literature (Ding 2026; Wang et al. 2023's own
MATH-vs-GSM8K comparison) predicts weaker candidate agreement here, which
is the precondition for actually testing whether OR-Select can correct a
wrong self-consistency majority.

For each problem: generate N candidates, run the full OR-Select pipeline,
and separately compute the self-consistency (majority vote over each
candidate's *extracted \\boxed{} answer*, not raw text) and
greedy-single-sample baselines from the same candidate set. All three
methods' answers are graded against ground truth using
or_select.math_eval's heuristic LaTeX-expression grader (see that
module's docstring for its known limitations).
"""

from __future__ import annotations

import argparse
import atexit
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from or_select.baselines import greedy_single_sample, self_consistency_winner  # noqa: E402
from or_select.kemeny import solve_kemeny_ranking  # noqa: E402
from or_select.generate import is_settled_truncation, truncation_attempts_so_far  # noqa: E402
from or_select.math_eval import MATH_SUFFIX, extract_boxed, is_correct  # noqa: E402
from or_select.providers import MAX_OUTPUT_TOKENS, SCORE_PARSE_STATS, score_parse_summary  # noqa: E402
from or_select.rejudge import JUDGE_VERSION, judgments_of, needs_rejudge, needs_reslot, rejudge_row, reslot_row  # noqa: E402
from or_select.pipeline import OPENROUTER_MIXED_MODELS, PROVIDERS, run_pipeline  # noqa: E402
from or_select import extended as _extended, providers as _providers  # noqa: E402

METHODS = ("or_select", "self_consistency", "greedy", "kemeny_young")


def _load_problems(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _grade_one(problem: dict, n: int, provider: str) -> dict:
    query = problem["query"] + MATH_SUFFIX
    ground_truth = problem["ground_truth"]

    result = run_pipeline(
        query, n=n, provider=provider, validity_fn=lambda text: extract_boxed(text) is not None
    )

    or_select_answer = extract_boxed(result.winner_text)

    sc_winner, had_majority = self_consistency_winner(
        result.candidates, key=lambda c: extract_boxed(c.text)
    )
    sc_answer = extract_boxed(sc_winner.text)

    greedy_winner = greedy_single_sample(result.candidates)
    greedy_answer = extract_boxed(greedy_winner.text)

    kemeny_ranking, kemeny_is_optimal = solve_kemeny_ranking(result.candidates, result.pairwise)
    kemeny_winner = next(c for c in result.candidates if c.id == kemeny_ranking[0])
    kemeny_answer = extract_boxed(kemeny_winner.text)

    return {
        "query": problem["query"],
        "ground_truth": ground_truth,
        "judge_version": JUDGE_VERSION,
        "judgments": judgments_of(result),
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
        # Raw texts, not just extracted answers: so an anomaly (e.g. a winner
        # with no \boxed{} answer, as seen in the N=20 pilot) can be
        # inspected from this file alone, without re-running the pipeline.
        "winner_texts": {
            "or_select": result.winner_text,
            "self_consistency": sc_winner.text,
            "greedy": greedy_winner.text,
            "kemeny_young": kemeny_winner.text,
        },
        # Full candidate pool, not just the 4 winners: previously it was
        # impossible to tell whether a differently-formatted-but-correct
        # candidate existed among the ones no method selected (this
        # makes grader false negatives checkable offline).
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
    # A ValidityExhausted failure means real candidates were generated and
    # discarded -- capture the last one's full text (not just its length,
    # which is all the error message carries) so it's possible to see why
    # extraction kept failing without burning another API call to find out.
    last_response = getattr(exc, "last_response", None)
    if last_response is not None:
        row["failed_last_response"] = last_response[:4000]
    if getattr(exc, "truncated", False):
        row["truncated"] = True
        # The cap the failing call actually ran with (a model's own limit can
        # sit below the global one in the extended pass).
        row["truncated_at_tokens"] = getattr(exc, "cap", None) or _providers.MAX_OUTPUT_TOKENS
    return row


def _accuracy_summary(results: list[dict]) -> dict:
    """Accuracy over VALID (successfully graded) problems only -- see
    scripts/gsm8k_benchmark.py's identical function for why."""
    valid = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    accuracy = {m: (sum(1 for r in valid if r[m]["correct"]) / len(valid)) for m in METHODS} if valid else {}
    # Rows rescued by the opt-in extended-cap second pass (or_select/extended.py)
    # are flagged; the main-protocol accuracy leaves them out.
    main_valid = [r for r in valid if not r.get("extended_cap_pass")]
    accuracy_main = (
        {m: (sum(1 for r in main_valid if r[m]["correct"]) / len(main_valid)) for m in METHODS} if main_valid else {}
    )
    return {
        "n_total": len(results),
        "n_valid": len(valid),
        "n_failed": len(failed),
        "n_valid_current_judge": sum(1 for r in valid if r.get("judge_version") == JUDGE_VERSION),
        "accuracy_of_valid": accuracy,
        "n_extended_rescued": len(valid) - len(main_valid),
        "accuracy_of_valid_main_protocol": accuracy_main,
    }


def _disagreement_summary(results: list[dict]) -> dict:
    """Count problems where OR-Select's winner differs from self-consistency's
    winner (by extracted answer), and separately where that divergence
    changes correctness -- this is the direct test of hypothesis sub-claim 5
    (can OR-Select correct a wrong self-consistency majority)."""
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
    """Count problems where OR-Select's Copeland-approximate top pick differs
    from the exact Kemeny-Young winner over the same pairwise matrix -- the
    direct test of whether selection.py's approximation (see its docstring)
    actually costs anything in practice."""
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
                "score_parse_this_run": dict(SCORE_PARSE_STATS),
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
            if rejudge and provider == "openrouter_mixed" and needs_reslot(existing, OPENROUTER_MIXED_MODELS):
                print(f"[{i}/{len(problems)}] replacing retired-model candidates: {problem['query'][:60]!r}", flush=True)
                try:
                    results[idx] = reslot_row(
                        existing,
                        problem["query"] + MATH_SUFFIX,
                        provider,
                        extract_boxed,
                        is_correct,
                        lambda text: extract_boxed(text) is not None,
                        OPENROUTER_MIXED_MODELS,
                    )
                except Exception as exc:  # noqa: BLE001 -- keep the old row, flag it, move on
                    existing["rejudge_error"] = f"{type(exc).__name__}: {exc}"[:300]
                    print(f"    RESLOT FAILED: {existing['rejudge_error']}", flush=True)
                else:
                    print("    retired-model candidates replaced, selection replayed", flush=True)
                _write_output(output, results, n, provider)
            elif rejudge and needs_rejudge(existing):
                print(f"[{i}/{len(problems)}] re-judging stored candidates: {problem['query'][:60]!r}", flush=True)
                try:
                    results[idx] = rejudge_row(
                        existing,
                        problem["query"] + MATH_SUFFIX,
                        provider,
                        extract_boxed,
                        is_correct,
                        lambda text: extract_boxed(text) is not None,
                    )
                except Exception as exc:  # noqa: BLE001 -- keep the old row, flag it, move on
                    existing["rejudge_error"] = f"{type(exc).__name__}: {exc}"[:300]
                    print(f"    REJUDGE FAILED: {existing['rejudge_error']}", flush=True)
                else:
                    print(f"    judge {existing.get('judge_version', 'reasoning-on')} -> {JUDGE_VERSION}", flush=True)
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


def run_extended_benchmark(problems: list[dict], n: int, provider: str, output: Path, cap: int) -> list[dict]:
    """Second pass at a higher output cap over the rows the main pass stored as
    truncated (see or_select/extended.py). Never touches any other row."""
    if not output.exists():
        raise SystemExit(f"--extended-cap needs an existing --output to extend: {output}")
    results = json.loads(output.read_text()).get("results", [])
    try:
        return _extended.run_extended_pass(
            results,
            problems,
            provider,
            OPENROUTER_MIXED_MODELS,
            cap,
            grade_one=lambda problem: _grade_one(problem, n, provider),
            failed_row=_failed_row,
            persist=lambda rows: _write_output(output, rows, n, provider),
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def main() -> None:
    atexit.register(lambda: print(score_parse_summary(), flush=True))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "math_level5_sample.jsonl")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--provider", choices=PROVIDERS, default="placeholder")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "math_benchmark.json")
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
    parser.add_argument(
        "--extended-cap",
        type=int,
        default=None,
        metavar="TOKENS",
        help="Second pass: re-run ONLY rows stored as truncated at the main cap, with this higher output cap "
        "(clamped per model), and flag them. Needs an existing --output with no untried problems; "
        "ignores --resume/--retry-failures.",
    )
    args = parser.parse_args()

    problems = _load_problems(args.input)
    if args.limit is not None:
        problems = problems[: args.limit]
    if args.extended_cap:
        results = run_extended_benchmark(problems, args.n, args.provider, args.output, args.extended_cap)
    else:
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
