# MATH Level 5 (Track C) — preregistered analysis plan

> **Historical record.** Written before the run's results were seen and kept unchanged apart from errata notes (where present). Final results and interpretation: `manuscript/main.tex`, Results section. Sub-claim numbering refers to the project's earlier hypothesis document, now superseded by the manuscript.

Written before this run's results were seen, so the analysis can't be
adjusted after the fact. Follows the same honesty norm as
the manuscript (`manuscript/main.tex`): report what the plan says even if the
answer is inconclusive or negative.

## Why this run exists

Track A (open-ended queries) and Track B (GSM8K) are documented in
`docs/benchmark_results.md`. GSM8K is saturated for the model in use — 100%
tie across all methods on every sample tried — so it cannot test hypothesis
sub-claim 5 (can OR-Select correct a wrong self-consistency majority?): if
nothing ever disagrees, there's nothing to correct. MATH Level 5 (Lightman
et al. 2023, MATH-500's hardest tier) was chosen because it is unsaturated
for this model, per Ding (2026) and Wang et al. (2023)'s own MATH-vs-GSM8K
comparison.

A first attempt (see git history, commit `a8d268f`) reached only N=2 before
hitting OpenRouter free-tier rate limits — inconclusive by construction. A
second attempt reached the full planned N=20 and surfaced a real finding:
OR-Select's IP has no completeness/validity check on candidate output, so it
selected a candidate with no `\boxed{}` answer over ones with a correct,
complete answer in the same pool, in 2/20 cases. That gap is now closed (a
`valid` gate in `selection.py`, wired to `extract_boxed(text) is not None`
in `scripts/math_benchmark.py`) — see commit history for the fix and its
tests (`tests/test_selection.py`).

This run is the first one intended to actually answer sub-claim 5, on a
sample size chosen for a defensible reason rather than an arbitrary round
number.

**Mid-run addendum**: this run itself hit the exact "no result, no error"
stall described in the first Track C attempt — a request hung for 28+
minutes with an established TCP connection and no exception, which the
previous attempt could only handle by a human noticing and killing the
process (its `StallTimeout` rows were recorded by hand, not automatically —
no such mechanism existed in the code despite the name). `or_select/
providers.py` now enforces a real 120s wall-clock deadline per API call
(`StallTimeout`, `_call_with_stall_timeout`) via a worker thread rather than
trusting the SDK's own read-timeout, which a trickle of keep-alive bytes can
apparently reset indefinitely without the request ever actually completing.
`StallTimeout` is treated as retryable like a rate limit. See
`tests/test_providers_offline.py::StallTimeoutTest` for the offline tests
(fast-path passthrough, deadline enforcement without blocking on the
orphaned call, exception passthrough). The run was killed and restarted
after this fix landed; `--retry-failures` picked the stalled problem back
up automatically.

## Methods compared

Four, all computed from the *same* generated candidate pool and the *same*
pairwise judge matrix per problem — only the aggregation step differs, so
comparisons are apples-to-apples and no method gets extra API calls:

1. **or_select** — the current pipeline: multi-objective IP over Copeland-
   approximate quality, confidence, self-consistency, and cost
   (`or_select/selection.py`).
2. **self_consistency** — majority vote over `extract_boxed()`, zero API
   cost (`or_select/baselines.py`).
3. **greedy** — single sample, no ensemble (`or_select/baselines.py`).
4. **kemeny_young** — exact Kemeny-Young rank aggregation over the same
   pairwise matrix (`or_select/kemeny.py`, new). Added specifically to test
   whether `aggregate_quality`'s Copeland approximation (methodology.md
   already flags it as "a Kemeny-Young approximation") actually costs
   anything versus solving the real thing. At this run's N=3 candidates per
   problem, the solve is trivially fast and always reaches a *proven*
   optimum (`is_optimal=True`, recorded per-row) -- the NP-hardness of this
   step only bites at larger candidate pools with a near-indifferent judge
   (see methodology.md's "A measured limitation" section), which does not
   apply here.

## Sample size: N=134 (the full Level-5 subset), and why

`data/math_level5_sample.jsonl` contains the complete Level-5 tier of
MATH-500 (134 problems) — this is not a subsample, it's the whole available,
literature-grounded pool for this benchmark. Two reasons this is the right
number rather than picking something else:

1. **No arbitrary N.** Using the complete standard subset avoids the
   appearance (or reality) of picking a sample size after peeking at partial
   results, or one convenient for a paper's stated budget. This is the
   largest N obtainable without leaving the literature-standard evaluation
   set entirely.
2. **Formal power check, done honestly up front.** The comparison that
   matters (or_select vs. self_consistency, paired by problem) is a McNemar
   test on discordant pairs. Using the normal approximation
   `n_disc = (z_{a/2} + z_b)^2 / (2p - 1)^2` for 80% power at alpha=0.05
   (`z_{a/2}=1.96`, `z_b=0.84`), and the pilot N=20 run's observed
   disagreement rate of ~10-15%:

   | effect (split among disagreements) | discordant pairs needed | total N needed (at 12.5% discordance) |
   |---|---|---|
   | 70/30 | 50 | ~400 |
   | 80/20 | 22 | ~176 |
   | 90/10 | 13 | ~104 |
   | 95/5  | 10 | ~80 |

   **N=134 is adequately powered only for a strong effect** (roughly a
   90/10-or-sharper split among the cases where methods disagree), **not**
   for a moderate one (70/30). This is stated as a limitation *before*
   running, not discovered after a null result. A true moderate effect could
   be missed by this sample size, and that would show up as "inconclusive,"
   not "no effect" — the two are not the same and will not be conflated in
   the writeup.

## Primary analysis (to run once results are in)

1. **McNemar's exact test** (binomial test on discordant pairs, since N may
   be small in the discordant subset even at N=134 total) comparing
   or_select vs. self_consistency paired correctness. This is the direct
   test of sub-claim 5.
2. Same test for or_select vs. kemeny_young — tests whether the Copeland
   approximation matters in practice, independent of sub-claim 5.
3. Per-method accuracy with an exact (Clopper-Pearson) 95% CI, not just a
   point estimate — N=134 point estimates alone invite over-reading small
   differences.
4. Report the *direction* of any disagreement-driven correction
   (`n_or_select_corrects_self_consistency` vs.
   `n_self_consistency_corrects_or_select`, already computed by
   `scripts/math_benchmark.py`), not just the count.

## What would change the conclusion from "inconclusive"

- A statistically significant McNemar result in either direction, sized
  consistently with the power table above (i.e. don't over-interpret a
  significant result from a discordant-pair count near the minimum-detect
  threshold without noting the wide CI that implies).
- If disagreements turn out to be dominated by extraction/formatting
  artifacts again (as 2 of 20 in the pilot were, on `x=5` vs `5` and
  `1,-2` vs `-2, 1`), that would need a grader fix before the McNemar result
  means anything — grading errors that hit all methods identically don't
  bias the *paired* comparison, but ones that hit methods differently would.

## Known scope limits, stated up front

- One model, one provider (OpenRouter free tier) — not a claim about the
  hypothesis in general, only about this configuration.
- N=134 exhausts MATH-500's Level-5 tier; a larger N would require a
  different/larger benchmark, out of scope for this run.
- Wall-clock cost: the N=20 pilot took on the order of hours under
  OpenRouter free-tier saturation; N=134 is expected to take substantially
  longer and may itself hit the same rate-limit wall the first Track C
  attempt did, in which case this document's job is to make clear in
  advance what "we didn't get there" would mean (a repeat of the N=2
  inconclusive outcome, not evidence against the hypothesis).
