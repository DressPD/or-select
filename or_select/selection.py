"""Deterministic winner selection via integer programming.

    maximize   sum_i x_i * (w1*quality_i + w2*confidence_i
                             + w4*consistency_i - w3*cost_i)
    subject to sum_i x_i = 1
               x_i in {0, 1}
               quality_i >= min_quality   (optional gate)

quality_i is the Copeland-style aggregate of the pairwise win matrix: the
average weight by which candidate i beats every other candidate.
consistency_i is the deterministic self-consistency signal from
or_select/consistency.py (fraction of candidates matching i's text) --
optional, defaults to 0 contribution if not supplied. Solved with CP-SAT,
which is exact and deterministic given fixed inputs — same candidates +
same pairwise matrix + same consistency scores always yields the same
winner.

See docs/methodology.md for the ranking (Kemeny-Young) extension.
"""

from __future__ import annotations

from ortools.sat.python import cp_model

from .core import Candidate

SCALE = 10_000


def aggregate_quality(candidates: list[Candidate], pairwise: dict[tuple[str, str], float]) -> dict[str, float]:
    """Copeland-style aggregate: mean pairwise win weight per candidate."""
    quality: dict[str, float] = {}
    for candidate in candidates:
        opponents = [c for c in candidates if c.id != candidate.id]
        if not opponents:
            quality[candidate.id] = 1.0
            continue
        wins = [pairwise[(candidate.id, o.id)] for o in opponents]
        quality[candidate.id] = sum(wins) / len(wins)
    return quality


def select_best(
    candidates: list[Candidate],
    quality: dict[str, float],
    consistency: dict[str, float] | None = None,
    w_quality: float = 1.0,
    w_confidence: float = 0.2,
    w_consistency: float = 0.3,
    w_cost: float = 0.01,
    min_quality: float | None = None,
    valid: dict[str, bool] | None = None,
) -> tuple[str, dict[str, float]]:
    """Solve the selection MIP. Returns (winner_id, per-candidate final scores).

    `valid` is an optional hard gate (e.g. "does this candidate's text contain
    a parseable final answer?") -- none of quality/confidence/consistency
    measure task-completion, so without this gate the IP can select a
    well-argued but unusable candidate over a complete, correct one in the
    same pool. Falls back to ungated selection if every candidate is invalid,
    so a bad batch never makes the MIP infeasible.
    """
    if not candidates:
        raise ValueError("no candidates to select from")

    gate_invalid = valid is not None and any(valid.values())

    model = cp_model.CpModel()
    x = {c.id: model.new_bool_var(f"x_{c.id}") for c in candidates}
    model.add(sum(x.values()) == 1)

    final_scores: dict[str, float] = {}
    objective_terms = []
    for c in candidates:
        consistency_i = consistency[c.id] if consistency is not None else 0.0
        score = (
            w_quality * quality[c.id]
            + w_confidence * c.confidence
            + w_consistency * consistency_i
            - w_cost * c.cost
        )
        final_scores[c.id] = score
        if min_quality is not None and quality[c.id] < min_quality:
            model.add(x[c.id] == 0)
        if gate_invalid and not valid[c.id]:
            model.add(x[c.id] == 0)
        objective_terms.append(int(round(score * SCALE)) * x[c.id])

    model.maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1  # keep the solve path deterministic
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"selection MIP infeasible (status={solver.status_name(status)})")

    winner_id = next(c.id for c in candidates if solver.value(x[c.id]) == 1)
    return winner_id, final_scores
