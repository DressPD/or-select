"""Exact Kemeny-Young rank aggregation via integer programming.

Given a full pairwise preference matrix, find the linear order (permutation)
that maximizes total agreement with the pairwise votes -- the Kemeny
consensus ranking. This is the "linear ordering problem": binary variables
x_ij = 1 if i is ranked above j, defined only for i < j in a fixed candidate
order (x_ji is implied as 1 - x_ij so antisymmetry is automatic); 3-cycle
elimination constraints (x_ij + x_jk + x_ki <= 2 for every ordered triple)
rule out intransitive solutions, which is necessary and sufficient for the
result to be a valid linear order. NP-hard in general, but solved exactly by
CP-SAT at the candidate-pool sizes (single/low-double-digit N) this pipeline
targets.

`aggregate_quality`'s Copeland-style score in selection.py is a cheap
approximation to this; this module answers whether the approximation
actually matters for the final winner (scripts/math_benchmark.py grades a
"kemeny_young" method alongside "or_select" for exactly this comparison,
reusing the same pairwise judge matrix at zero extra API cost).

## A measured limitation

The linear ordering problem is NP-hard, and CP-SAT's branch-and-bound search
can take a long time to *prove* optimality once candidate preferences are
close to a coin flip (pairwise weights clustered near 0.5) -- exactly the
case where an LLM judge is genuinely unsure. Measured directly: with a real
quality gradient among candidates, N=20 solves in ~41ms; with near-uniform
noisy weights, N=20 did not finish in 60+ seconds of wall-clock search.
`select_best` in selection.py never has this problem -- picking 1-of-N by a
linear score is a trivial LP-integral case regardless of N, so the
production selection path was never at risk.

Bounding the search with a wall-clock `max_time_in_seconds` would silently
break this repo's central determinism claim: the same inputs could yield a
different (truncated-search) ranking depending on which machine or how
loaded it was when the query ran. Instead this solves within a budget of
CP-SAT *conflicts* -- a machine-independent, exactly reproducible resource
count, not a duration -- so "same inputs -> same output" still holds even
when the budget is exhausted before optimality is proven. When that
happens, the best feasible ranking found is returned along with
`is_optimal=False`, so a truncated search is never silently reported as the
verified Kemeny consensus.
"""

from __future__ import annotations

from ortools.sat.python import cp_model

from .core import Candidate

SCALE = 10_000
DEFAULT_MAX_CONFLICTS = 200_000


def solve_kemeny_ranking(
    candidates: list[Candidate],
    pairwise: dict[tuple[str, str], float],
    max_conflicts: int = DEFAULT_MAX_CONFLICTS,
) -> tuple[list[str], bool]:
    """Return (candidate ids ranked best-first, is_optimal).

    is_optimal is False if the max_conflicts budget was exhausted before the
    solver could prove the returned ranking is the true Kemeny consensus --
    it is then the best ranking found, not a verified one. The search is
    bounded by conflict count rather than wall-clock time so the result
    stays exactly reproducible regardless of machine speed or load (see
    module docstring).
    """
    if not candidates:
        raise ValueError("no candidates to rank")
    ids = [c.id for c in candidates]
    n = len(ids)
    if n == 1:
        return ids, True

    model = cp_model.CpModel()
    x = {(i, j): model.new_bool_var(f"x_{i}_{j}") for i in range(n) for j in range(i + 1, n)}

    def above(u: int, v: int):
        """Model expression for 'u ranked above v', u != v."""
        return x[(u, v)] if u < v else 1 - x[(v, u)]

    for i in range(n):
        for j in range(n):
            for k in range(n):
                if i != j and j != k and i != k:
                    model.add(above(i, j) + above(j, k) + above(k, i) <= 2)

    objective_terms = []
    for i in range(n):
        for j in range(i + 1, n):
            w_ij = pairwise[(ids[i], ids[j])]
            w_ji = pairwise[(ids[j], ids[i])]
            objective_terms.append(int(round((w_ij - w_ji) * SCALE)) * x[(i, j)])
    model.maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1  # keep the solve path deterministic
    solver.parameters.max_number_of_conflicts = max_conflicts
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"Kemeny ranking MIP infeasible (status={solver.status_name(status)})")

    solved_x = {key: solver.value(var) for key, var in x.items()}

    def above_val(u: int, v: int) -> int:
        return solved_x[(u, v)] if u < v else 1 - solved_x[(v, u)]

    wins = [sum(above_val(i, j) for j in range(n) if j != i) for i in range(n)]
    order = sorted(range(n), key=lambda i: (-wins[i], i))  # index tiebreak keeps ties deterministic
    return [ids[i] for i in order], status == cp_model.OPTIMAL
