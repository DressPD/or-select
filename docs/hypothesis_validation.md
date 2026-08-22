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

**CONFIRMED, strongly.** Track B (GSM8K, ground truth, full run): on all
40 of 40 graded problems, all three methods — OR-Select, self-consistency,
greedy — tied at 100% accuracy, because every candidate independently
converged on the identical correct answer every time (0/40 disagreement).
This is the predicted complement to sub-claim 3, confirmed independently:
a judge cannot differentiate candidates that do not differ.

## Sub-claim 5: OR-Select can correct a wrong self-consistency majority

**STILL UNTESTED, but now on strong grounds rather than a stalled small
sample.** Across 170 graded problems in four independent runs, the
precondition this sub-claim needs — a self-consistency majority that is
*genuinely* wrong — essentially never arose. This is the strongest and
most practically relevant form of the hypothesis: candidates disagree,
the majority converges on a *wrong* answer, and OR-Select's judge selects
a *correct* minority answer instead. The literature-motivated plan below
predicted this precondition should appear on unsaturated,
harder-than-GSM8K benchmarks; four separate runs were built and executed
specifically to find it.

**Track C — MATH Level 5** (Lightman et al. 2023's MATH-500, Level-5
subset, 134 problems, `outputs/math_benchmark_full.json`): ran to
completion, N=107/134 valid (27 failed to grade on free-tier infra, not
incorrect answers). All four methods (OR-Select, self-consistency, greedy,
Kemeny-Young) tied at a nominal **91.6% accuracy**, with 9 rows graded
"wrong." Checking those 9 directly (`self_consistency.had_majority` plus
manual inspection of `ground_truth` vs. the extracted answer) found that
**all 9 have a self-consistency majority, and all 9 are grader false
negatives, not genuinely wrong answers** — `\$32,\!348` vs `32348`,
`5.4 \text{ cents}` vs `5.4`, `-2, 1` vs `1,-2` (reordered set), `1/5,
-18/5` vs `\frac{1}{5}, -\frac{18}{5}` (notation), and so on: every one is
the same value in a format `math_eval`'s heuristic grader doesn't
normalize, confirming the limitation that module's own docstring already
flags. So Track C's real tie rate is closer to 107/107 than 98/107, and —
more importantly for this sub-claim — in 8 of those 9 rows OR-Select's
answer was identical to self-consistency's, meaning OR-Select reproduced
the (apparent) wrong majority rather than correcting it; in the 9th,
OR-Select's answer differed from self-consistency's only in the same kind
of formatting (`\{-2, 1+\sqrt5, 1-\sqrt5\}` vs `\{-2,\ 1+\sqrt5,\
1-\sqrt5\}`), not a different value. Because per-candidate extracted
answers are not persisted (`_grade_one` only stores the four winners'
texts), it is not recoverable from this output whether any *individual*
candidate in those 9 rows held a differently-formatted-but-correct answer
that OR-Select had a chance to select and passed over — so this cannot be
strengthened into "OR-Select failed to correct," only "no case of a
genuinely wrong majority was found for OR-Select to correct." (A separate,
smaller N=20 pilot at `outputs/math_benchmark.json`, run earlier at n=3
samples/problem before the full run, surfaced a different, already-
understood failure mode: OR-Select twice selected a winner whose text had
no `\boxed{}` answer at all, losing to self-consistency's majority on an
extraction technicality rather than a judgment call — documented in
`scripts/math_benchmark.py`'s "anomaly" comment, not a new finding.)

**Track D — AIME 2026** (`outputs/aime_2026_benchmark.json`, homogeneous
generation): N=14/30 valid (16 failed to grade — free-tier `StallTimeout`,
Nvidia-provider 502 overload, and `APITimeoutError`/`APIConnectionError`,
plus a transient daily-quota exhaustion, all infra, not model failures;
this track plateaued at 14/30 across 3 consecutive `--retry-failures`
passes with zero net gain, indicating a genuine free-tier ceiling rather
than remaining transient flakiness). All four methods tied at **100%**
accuracy on the 14 graded. 0 disagreements.

**Track D-heterogeneous — AIME 2026, 3-vendor generation**
(`outputs/aime_2026_heterogeneous.json`, `OPENROUTER_MIXED_MODELS` =
Nemotron + gpt-oss-20b + LFM-2.5, judge held fixed on Nemotron per
`pipeline.py`'s variable-isolation design): specifically built to break
the "same model → correlated errors" explanation (Kim et al. 2025, below)
by forcing genuinely different model families to generate candidates for
the same problem. N=9/30 valid (21 failed to grade, same infra causes as
Track D, also plateaued after 3 zero-gain retry passes). All four methods
tied at **100%** accuracy on the 9 graded. 0 disagreements — cross-vendor
generation did not surface disagreement either.

**Combined across Tracks B, C, D, D-het: 170 graded problems, 0 confirmed
cases of a genuinely wrong self-consistency majority, and therefore 0
opportunities for OR-Select to demonstrate a correction in either
direction.** This is now a repeated result across four independently-run
tracks spanning three benchmarks (GSM8K, MATH Level 5, AIME 2026) and two
generation regimes (single-model, 3-vendor heterogeneous), not a single
underpowered attempt — but it is a repeated *absence of the test
condition*, not a repeated pass/fail of the mechanism itself.

The literature reasoning that motivated these attempts is not contradicted
by this result, but its predicted effect size did not materialize at the
scale we could reach on free-tier infrastructure: Kim, Garg, Peng, and
Garg, *Correlated Errors in Large Language Models* (ICML 2025,
arXiv:2506.07962), find that stronger models produce *more* correlated
outputs across 350+ models, not less — convergence is a structural
property of capable models on saturated benchmarks, and Track D-het's
result (0 disagreement even with 3 distinct vendors) is consistent with
this: correlated *correctness*, not shared weights, may be driving
agreement. Ding, *When LLMs Agree, Are They Right?* (2026,
arXiv:2607.08065), deliberately used GPQA Diamond and AIME (not GSM8K) to
study agreement precisely because those benchmarks are not saturated for
frontier models, and found agreement is a weak correctness signal that
gets *weaker* for stronger models — AIME 2026 was chosen here for exactly
this reason, and still tied 100%, though only on N=14 and N=9 valid
samples respectively, both well short of the benchmark's 30-problem full
set. Even Wang et al.'s original self-consistency paper (already cited in
this repo) reports weaker vote-share/correctness correlation on MATH
(0.68) than GSM8K (0.80) — consistent with Track C's nominal 91.6% sitting
below GSM8K's 100%, but the corrected reading above (real tie rate close
to 100% once grader artifacts are set aside) means even MATH Level 5 did
not surface a genuinely wrong majority for this model class.

**What would still move this forward:** a paid API tier to clear the
free-tier infrastructure ceiling and reach the full N=134/30/30 samples
per track (currently at 107/134, 14/30, 9/30 — roughly 1.5x more graded
problems available at full completion), a stricter math grader (to stop
undercounting ties as disagreements, as found above), and/or a benchmark
harder still than AIME 2026 for this model class. All three remain
untried; this document reports the honest current state on available
data, not a final word on the hypothesis.

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
aggregation adds real value over naive baselines — is confirmed in the
one regime tested for it (sub-claim 3: 3/3 divergence on open-ended
queries) and, symmetrically, its complement is now strongly confirmed
across four independent ground-truth benchmarks (sub-claim 4: 40/40 tied
on GSM8K, 107 graded and tied on MATH Level 5, 14/14 tied on AIME 2026,
9/9 tied on AIME 2026 heterogeneous — 170 total graded problems, every
method agreeing on every one). Sub-claim 5, the hardest and most
practically important case — OR-Select correcting a wrong
self-consistency majority — was pursued directly, in four separate runs
spanning three benchmarks and two generation regimes (homogeneous and
3-vendor heterogeneous), and **still found no case of a genuinely wrong
majority** across all 170 graded problems: Track C's apparent 9
counterexamples turned out, on inspection, to be grader false negatives
(formatting variants of the correct answer), not real errors. This is no
longer an underpowered attempt — it is a repeated, well-checked absence
of the precondition the sub-claim needs, not a repeated pass/fail of the
mechanism. It does not prove sub-claim 5 is false, nor does it confirm it;
the precondition (candidates disagree AND the majority is genuinely
wrong) may simply be rare enough, for this model class on these
benchmarks, that even AIME 2026 didn't surface it at the ~9-14
samples/track free-tier infrastructure allowed, or a harder benchmark or
larger sample may be needed to find it. What this result does establish
is that OR-Select's determinism (sub-claim 1) and its value on divergent,
no-majority open-ended queries (sub-claim 3) are on solid footing, while
its value as a *corrector* of wrong majorities on convergent, gradeable
problems remains an open question — not because the mechanism failed a
test, but because no test case has yet presented itself despite genuine,
repeated attempts to find one. One of its two internal components has not
yet demonstrated value on real data (sub-claim 6, self-consistency term)
for the same underlying reason: the uneven-clustering middle case it
targets has not appeared in any ground-truth run either. This is reported
as the honest current state, not rounded up toward a cleaner story.
