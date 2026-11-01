"""Replay the post-generation half of the pipeline on stored candidates.

Two reasons a stored row has to be replayed:

* Rows graded before commit dafc89b used a reasoning-on judge that was cut off
  in ~60% of calls, so their OR-Select / Kemeny-Young picks came from judge
  fragments. Generation and the judge-independent baselines (self-consistency,
  greedy) are unaffected, so only confidence scores, pairwise judging,
  selection and the exact Kemeny ranking are replayed (`rejudge_row`).
* A heterogeneous row holds candidates from a model that has since left the
  mixed pool. Only that model's slots are regenerated, by the model that now
  fills the slot; the other candidates are kept, and the whole selection (and
  both baselines, which see every candidate) is replayed (`reslot_row`).

Every row records the `judge_version` that produced its judge-dependent
fields; `needs_rejudge` is true for anything not on JUDGE_VERSION.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .baselines import greedy_single_sample, self_consistency_winner
from .core import Candidate
from .kemeny import solve_kemeny_ranking
from .pipeline import canonical_model, resolve_score_judge, select_from_candidates

JUDGE_VERSION = "short-answer"
LEGACY_JUDGE_VERSION = "reasoning-on"


def judgments_of(result: Any) -> dict:
    """The judge-model verdicts behind a row's winner, compact enough to store.

    `confidence` is each candidate's score from the scoring call, `pairwise`
    the pairwise-judge weight for every ordered candidate pair ("a|b" is the
    weight of a over b), `selection_scores` the final per-candidate score the
    winner was picked from. With these stored a pick can be audited or
    re-derived without calling the judge again.
    """
    return {
        "confidence": {c.id: c.confidence for c in result.candidates},
        "pairwise": {f"{a}|{b}": w for (a, b), w in result.pairwise.items()},
        "selection_scores": dict(result.scores),
    }


def needs_rejudge(row: dict) -> bool:
    return "error" not in row and bool(row.get("candidates")) and row.get("judge_version") != JUDGE_VERSION


def stale_slots(row: dict, pool: list[str]) -> list[int]:
    """Indices of stored candidates whose model is no longer in `pool`."""
    return [i for i, c in enumerate(row.get("candidates") or []) if canonical_model(c["source_model"]) not in pool]


def needs_reslot(row: dict, pool: list[str]) -> bool:
    return "error" not in row and bool(stale_slots(row, pool))


def _replay(
    row: dict,
    candidates: list[Candidate],
    query: str,
    provider: str,
    answer_fn: Callable[[str], Any],
    correct_fn: Callable[[Any, Any], bool],
    validity_fn: Callable[[str], bool],
    refresh_baselines: bool,
) -> dict:
    score_fn, judge_fn = resolve_score_judge(provider)
    result = select_from_candidates(query, candidates, score_fn, judge_fn, validity_fn)
    ground_truth = row["ground_truth"]

    new = dict(row)
    or_select_answer = answer_fn(result.winner_text)
    new["or_select"] = {"answer": or_select_answer, "correct": correct_fn(or_select_answer, ground_truth)}
    winner_texts = dict(row["winner_texts"]) if row.get("winner_texts") is not None else None
    if winner_texts is not None:
        winner_texts["or_select"] = result.winner_text

    if "kemeny_young" in row:
        ranking, kemeny_is_optimal = solve_kemeny_ranking(result.candidates, result.pairwise)
        kemeny_winner = next(c for c in result.candidates if c.id == ranking[0])
        kemeny_answer = answer_fn(kemeny_winner.text)
        new["kemeny_young"] = {
            "answer": kemeny_answer,
            "correct": correct_fn(kemeny_answer, ground_truth),
            "is_optimal": kemeny_is_optimal,
        }
        if winner_texts is not None:
            winner_texts["kemeny_young"] = kemeny_winner.text

    if refresh_baselines:
        sc_winner, had_majority = self_consistency_winner(result.candidates, key=lambda c: answer_fn(c.text))
        sc_answer = answer_fn(sc_winner.text)
        new["self_consistency"] = {
            "answer": sc_answer,
            "correct": correct_fn(sc_answer, ground_truth),
            "had_majority": had_majority,
        }
        greedy_winner = greedy_single_sample(result.candidates)
        greedy_answer = answer_fn(greedy_winner.text)
        new["greedy"] = {"answer": greedy_answer, "correct": correct_fn(greedy_answer, ground_truth)}
        if winner_texts is not None:
            winner_texts["self_consistency"] = sc_winner.text
            winner_texts["greedy"] = greedy_winner.text
        new["candidates"] = [
            {"seed": c.metadata.get("seed"), "source_model": c.source_model, "text": c.text} for c in result.candidates
        ]

    if winner_texts is not None:
        new["winner_texts"] = winner_texts
    new["judgments"] = judgments_of(result)
    new["judge_version"] = JUDGE_VERSION
    new.pop("rejudge_error", None)
    return new


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
    return _replay(row, candidates, query, provider, answer_fn, correct_fn, validity_fn, refresh_baselines=False)


def reslot_row(
    row: dict,
    query: str,
    provider: str,
    answer_fn: Callable[[str], Any],
    correct_fn: Callable[[Any, Any], bool],
    validity_fn: Callable[[str], bool],
    pool: list[str],
) -> dict:
    """Return a copy of `row` whose candidates from models outside `pool` were
    regenerated by the pool model that now fills the same round-robin slot.

    Same slot index and seed as a fresh run would use, so the result is what a
    full re-run on the new pool would have produced for those slots; the kept
    candidates are the pool models' own draws. Raises (leaving `row` untouched)
    if a regeneration or any judge/score call fails.
    """
    from . import providers
    from .generate import _generate_valid

    backends = providers.openrouter_heterogeneous_backends(pool)
    candidates = []
    for i, c in enumerate(row["candidates"]):
        if canonical_model(c["source_model"]) in pool:
            candidates.append(
                Candidate(
                    id=f"c{i}", text=c["text"], source_model=canonical_model(c["source_model"]), metadata={"seed": c["seed"]}
                )
            )
        else:
            name, fn = backends[i % len(backends)]
            text = _generate_valid(fn, query, i, validity_fn)
            candidates.append(Candidate(id=f"c{i}", text=text, source_model=name, metadata={"seed": i}))
    return _replay(row, candidates, query, provider, answer_fn, correct_fn, validity_fn, refresh_baselines=True)
