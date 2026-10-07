"""Re-judge stored candidates with the current judge/score pipeline.

Rows graded before commit dafc89b used a reasoning-on judge that was cut off
in ~60% of calls, so their OR-Select / Kemeny-Young picks came from judge
fragments. Generation and the judge-independent baselines (self-consistency,
greedy) are unaffected, so a row with stored candidates only needs the
post-generation half of the pipeline replayed: confidence scores, pairwise
judging, selection, exact Kemeny ranking.

Every row records the `judge_version` that produced its judge-dependent
fields; `needs_rejudge` is true for anything not on JUDGE_VERSION.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .core import Candidate
from .kemeny import solve_kemeny_ranking
from .pipeline import resolve_score_judge, select_from_candidates

JUDGE_VERSION = "short-answer"
LEGACY_JUDGE_VERSION = "reasoning-on"


def needs_rejudge(row: dict) -> bool:
    return "error" not in row and bool(row.get("candidates")) and row.get("judge_version") != JUDGE_VERSION


def rejudge_row(
    row: dict,
    query: str,
    provider: str,
    answer_fn: Callable[[str], Any],
    correct_fn: Callable[[Any, Any], bool],
    validity_fn: Callable[[str], bool],
) -> dict:
    """Return a copy of `row` with or_select / kemeny_young recomputed.

    `query` must be the exact prompt the live path judged (problem query plus
    the benchmark's suffix). Raises if any judge/score call fails, leaving the
    caller's row untouched -- the swap is all-or-nothing.
    """
    candidates = [
        Candidate(id=f"c{i}", text=c["text"], source_model=c["source_model"], metadata={"seed": c["seed"]})
        for i, c in enumerate(row["candidates"])
    ]
    score_fn, judge_fn = resolve_score_judge(provider)
    result = select_from_candidates(query, candidates, score_fn, judge_fn, validity_fn)
    ranking, kemeny_is_optimal = solve_kemeny_ranking(result.candidates, result.pairwise)
    kemeny_winner = next(c for c in result.candidates if c.id == ranking[0])

    ground_truth = row["ground_truth"]
    or_select_answer = answer_fn(result.winner_text)
    kemeny_answer = answer_fn(kemeny_winner.text)

    new = dict(row)
    new["or_select"] = {"answer": or_select_answer, "correct": correct_fn(or_select_answer, ground_truth)}
    new["kemeny_young"] = {
        "answer": kemeny_answer,
        "correct": correct_fn(kemeny_answer, ground_truth),
        "is_optimal": kemeny_is_optimal,
    }
    winner_texts = dict(row.get("winner_texts") or {})
    winner_texts["or_select"] = result.winner_text
    winner_texts["kemeny_young"] = kemeny_winner.text
    new["winner_texts"] = winner_texts
    new["judge_version"] = JUDGE_VERSION
    new.pop("rejudge_error", None)
    return new
