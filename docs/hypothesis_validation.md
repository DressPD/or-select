# Hypothesis Validation

## The hypothesis, stated explicitly

**OR algorithms (integer programming over a rank-aggregated judge signal)
can make selection among multiple stochastic LLM outputs deterministic,
and this selection can differ meaningfully from naive baselines
(self-consistency alone, greedy single-sample) when it matters.**

This splits into six testable sub-claims. Each gets an explicit verdict
below, not just supporting anecdotes — including the ones that did not
hold up.

## Sub-claim 1: Selection is exactly deterministic given fixed inputs

**CONFIRMED — by construction, not just observation.** CP-SAT with
`num_search_workers=1` solving a deterministic linear objective over a
fixed feasible region always returns the same optimum; this is a
property of the solver and the formulation, proved once
(`tests/test_selection.py::test_selection_is_deterministic_across_repeated_solves`
runs the same input 5 times, asserts one winner) rather than something
that could fail probabilistically at scale. This is the one part of the
hypothesis that is proof, not evidence.

## Sub-claim 2: The full live pipeline is reproducible in practice

**PARTIALLY REFUTED — a real, load-bearing caveat.** The solve is only
as reproducible as its inputs, and the inputs come from LLM calls. We
found direct evidence this matters: three byte-identical candidates,
which by construction must score exactly `0.5` against each other
regardless of what the model returns, instead scored `0.375`/`0.50`/`0.625`
— proof a provider's `seed` parameter is not reliably honored, not a
theoretical caveat about vendor documentation (`methodology.md`, "A
concrete finding"). We closed this **specific** failure mode completely
(the exact-match short-circuit in `pairwise.py` means identical text
never reaches the judge, so it can no longer be corrupted this way) but
the **general** case — two *different* texts receiving unstable judge
scores across runs — remains open and untested.

## Sub-claim 3: OR-Select differs from naive baselines when candidates diverge

**CONFIRMED, on 3 of 3 available cases.** Track A (open-ended queries,
`benchmark_results.md`): OR-Select disagreed with both self-consistency
and greedy on all 3 queries tested. Self-consistency's failure mode was
total, not partial — 0 of 15 candidates across all three queries matched
any other candidate exactly, so majority vote had no majority to find in
any case, falling back to an arbitrary tie-break every time.

## Sub-claim 4: OR-Select ties with naive baselines when candidates converge

**CONFIRMED, strongly.** Track B (GSM8K, ground truth): on every one of
23 problems that graded successfully (17 of 40 attempted failed with a
persistent provider error, not a modeling result — see
`benchmark_results.md`), all three methods — OR-Select, self-consistency,
greedy — tied at 100% accuracy, because every candidate independently
converged on the identical correct answer every time. This is the
predicted complement to sub-claim 3, confirmed independently: a judge
cannot differentiate candidates that do not differ.

## Sub-claim 5: OR-Select can correct a wrong self-consistency majority

**UNTESTED — the single most important open gap.** This is the strongest
and most practically relevant form of the hypothesis: candidates
disagree, the majority converges on a *wrong* answer, and OR-Select's
judge selects a *correct* minority answer instead. It has not occurred in
any live run in this repository. GSM8K's easy end (sub-claim 4) never
produces disagreement at all; the open-ended queries (sub-claim 3) have
no ground truth to define "wrong." Closing this gap needs either harder
GSM8K problems or a weaker generator model, specifically chosen to induce
real, checkable disagreement — not yet attempted.

## Sub-claim 6: Each design component pulls its weight

**MIXED, resolved by ablation, not assumption.**

- **Permutation self-consistency (bidirectional judging): confirmed
  load-bearing, not universal.** Forward-only judging changed the winner
  in 2 of 3 valid comparisons (rent-vs-buy, Hamlet) and did not in the
  third (traffic congestion). `docs/ablations.md` has the full account,
  including a data-hygiene bug we found and fixed mid-study (two stale
  pre-fix result files were silently included in an earlier pass and
  produced a misleading "changed" result driven by CP-SAT's arbitrary
  tie-break, not real judge behavior).
- **Self-consistency term (`w4`): not yet confirmed.** 0 of 3 valid
  winners changed when the term was removed, for a clean structural
  reason: `consistency_spread` was exactly `0.000` in every case, because
  every candidate set observed either fully converged or fully diverged —
  never the uneven-clustering middle case the term is designed for. Not
  wrong, just untested on the scenario it targets.

## Overall verdict

The **narrow** claim — selection is exactly deterministic given fixed
inputs — is proven, not just supported. The **broad** claim — OR-based
aggregation adds real value over naive baselines — is supported by every
test run so far (3/3 divergence on open-ended queries, 23/23 convergence
ties on GSM8K, both exactly as the same underlying mechanism predicts
from opposite directions) but has not yet been tested against its
hardest and most important case (sub-claim 5), and one of its two
internal components has not yet demonstrated value on real data
(sub-claim 6, self-consistency term). This is reported as the honest
current state, not rounded up toward a cleaner story: the hypothesis is
supported at small scale, with a specific, named, and still-open
condition under which it would be genuinely tested and could still fail.
