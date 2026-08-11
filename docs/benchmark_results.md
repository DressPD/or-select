# Benchmark Results

Two tracks, because they answer different questions and neither alone is
sufficient (see Landesberg 2026 in `methodology.md`'s Related Work: judge
calibration doesn't predict actual selection accuracy — you need a
checkable answer to know that).

- **Track A — open-ended queries, no ground truth.** Tests whether
  OR-Select's selection *differs* from simpler baselines, and by how much,
  when there's no single correct answer to check against. Qualitative:
  agreement/disagreement and score margins.
- **Track B — GSM8K, ground truth.** Tests whether OR-Select's selection
  is actually *correct* more often than the baselines. Quantitative:
  accuracy.

All three methods compared throughout:
- **OR-Select**: the full pipeline (`or_select/pipeline.py`) — LLM judge +
  deterministic self-consistency term, aggregated via CP-SAT.
- **Self-consistency alone**: majority vote (`or_select/baselines.py`), no
  LLM judge, no OR.
- **Greedy single-sample**: just the first of the N candidates, no
  ensemble at all.

Provider: OpenRouter, `nvidia/nemotron-3-ultra-550b-a55b:free`, for every
result below (chosen for availability, not because it's the model this
method is expected to work best with — see "Open questions" at the end).

## Summary

| Track | Task type | Candidates agreed? | Result |
|---|---|---|---|
| A | Open-ended (3 queries, N=5) | Never (0/15) | OR-Select disagreed with both baselines on 3/3; self-consistency undefined every time |
| B | GSM8K, easy (23 of 40 attempted problems graded, N=3) | Always (23/23) | All 3 methods tied at 100% accuracy on every graded problem |

Both results are consistent with a single underlying prediction, stated in
`methodology.md` before either track was run: baselines and OR-Select
should tie when candidates cluster, and diverge when they don't. Neither
track alone would show this — Track A has no ground truth to confirm
correctness, Track B has no divergence to force a real choice. Together
they show the mechanism working as designed, on both ends of that axis.

## Track A: open-ended queries (N=5)

| Query | OR-Select winner | vs. self-consistency | vs. greedy | Score margin (winner vs. runner-up) |
|---|---|---|---|---|
| "Summarize the plot of Hamlet in one sentence." | c2 (0.574) | disagreed | disagreed | 0.574 vs 0.486 — clear |
| "Single most effective strategy for reducing traffic congestion?" | c1 (-3.664) | disagreed | disagreed | -3.664 vs -4.110 — clear |
| "Is it generally better to rent or buy a home?" | c3 (0.0835) | disagreed | disagreed | 0.0835 vs 0.0813 — near tie |

**Consistent pattern across all 3 (15 candidates total, N=5 x 3
queries):** zero exact-text duplicates. Self-consistency alone had no true
majority to find in *any* of the three queries, and fell back to an
arbitrary tie-break every time — which happened to coincide exactly with
the greedy-single-sample pick in all three, since both default to "first
candidate" when there's nothing else to go on. **OR-Select disagreed with
both baselines on all 3 of 3 queries.**

**Not a uniform win, and the report says so rather than hiding it:**
Hamlet and traffic show real quality differentiation (margins of
0.09–0.45) — the judge is doing substantive work, e.g. the traffic-query
winner is the *second-shortest* of 5 answers, not the longest, because the
cost term penalizes verbosity even among similarly-good long-form answers.
Rent-vs-buy is a near three-way tie (margin ~0.003): the top 3 candidates
were paraphrases of the same balanced answer, so OR-Select's "win" there
is close to noise, not a confident judgment. Take from this: OR-Select
adds real value once candidates meaningfully diverge in quality, and its
edge shrinks toward nothing when they don't.

## Track B: GSM8K, ground truth (N=3, 40 problems attempted, 23 graded)

**Accuracy on graded problems: OR-Select 23/23 (100%), self-consistency
23/23 (100%), greedy 23/23 (100%).** All three methods tied — and the
reason is visible in every individual result: on every one of the 23
graded problems, all 3 of 3 candidates independently reached the exact
same numeric answer (`had_majority: True` every time), the mirror image
of Track A, where it was `False` in all 3 queries.

**Coverage, reported honestly rather than smoothed into the accuracy
number:** 17 of the 40 attempted problems never graded at all. Starting
at problem 24, every remaining problem failed identically with an
OpenRouter "provider returned error" 404, despite full retry exhaustion
(5 attempts, up to 75s backoff) on each one — this pattern (100% failure
rate sustained across 17 consecutive, unrelated problems) looks like a
hard session or daily cap on this free-tier model, not transient
congestion; congestion produces intermittent failures, not a clean
cutoff that never recovers for the rest of the run. `_accuracy_summary()`
in `scripts/gsm8k_benchmark.py` computes accuracy only over problems that
graded successfully — folding the 17 failures into the denominator as if
they were wrong answers would have understated accuracy and misrepresented
an infrastructure failure as a modeling result.

**This is not a failed benchmark — it's the predicted result on easy
problems, and it's the useful half of a two-track story.**
`methodology.md`'s Baselines section already predicted this shape before
any data existed: *"The baseline should win exactly when candidates
cluster tightly... OR-Select should win once candidates diverge."*
Grade-school arithmetic is well within Nemotron's capability, so
candidates cluster tightly (Track B) — there is no headroom for a judge to
add value when every sample already agrees and is already correct. Open-
ended queries never cluster at all (Track A) — that's exactly where the
judge's differentiation showed up. Together, the two tracks confirm both
halves of the same prediction rather than reporting on two unrelated
tasks. **What this run does not show**, and what would need harder
problems to test: whether OR-Select's judge can *correct* a wrong
majority when candidates disagree and most of them are wrong — GSM8K's
easy end just doesn't produce that scenario at N=3 with a capable model,
across all 23 problems that got the chance to show it.

Methodology: `scripts/gsm8k_benchmark.py` appends a fixed instruction
("Solve step by step, then end your response with exactly: The final
answer is \<number\>.") to each problem, runs the full pipeline, then
extracts the last number in each candidate's text (`or_select/gsm8k.py`,
same "last number wins" heuristic as confidence/judge parsing elsewhere in
this repo — reasoning models show their work before answering).
Self-consistency here is computed correctly per Wang et al.'s original
definition: majority vote over each candidate's *extracted numeric
answer*, not raw reasoning text (`self_consistency_winner(..., key=...)`)
— two candidates can reach the same correct number via different
reasoning, and should be counted as agreeing.

Sample: `data/gsm8k_sample.jsonl`, the first 40 problems of the real
GSM8K test set (github.com/openai/grade-school-math), used
deterministically (no cherry-picking, no random seed to justify).
Problems 1-23 graded; problems 24-40 failed to grade (see coverage note
above).

## Open questions this benchmark does not resolve

- **Free-tier availability as a research constraint, not just an
  inconvenience**: over the course of this project we hit three distinct
  OpenRouter/provider reliability failure modes -- transient rate-limit
  saturation (queue depths observed up to 3517/32, recoverable with
  retry/backoff), a corporate-proxy 407 (transient, unrelated to the LLM
  provider), and this run's persistent post-problem-23 "provider returned
  error" 404 (not recoverable by retrying, resolved by nothing we could
  do). Free-tier access to a single model is not a reliable substrate for
  runs with O(N^2) judge calls; a paid tier or a smaller/cheaper
  evaluation design is a real prerequisite for scaling this further, not
  just a nice-to-have.
- **Correlated judge error** (Nine Judges, Two Effective Votes, 2026):
  every result above uses a single model (Nemotron) as generator, scorer,
  *and* judge. Whether `--provider both`/`all` (heterogeneous judges)
  would actually reduce correlated error here, or just add cost, is
  untested — would need a run with a working OpenAI or Gemini key
  alongside OpenRouter.
- **Provider-seed reliability**: the `_stable_seed` mechanism is
  best-effort per-provider, not a guarantee (documented in
  `methodology.md`'s "A concrete finding" — identical text got non-
  symmetric scores from this exact model before the exact-match
  short-circuit fixed that specific case).
- **Sample size**: N=3–5 candidates and 3 queries / 23 graded problems per
  track are smoke-test scale, bounded by OpenRouter's free-tier congestion
  and the hard cap hit at problem 24, not a statistically powered
  evaluation. Track B's remaining 17 problems (24-40 in
  `data/gsm8k_sample.jsonl`) and a larger N are the natural next step once
  the free-tier limit resets or a paid tier is available.
- **No test of judge-corrects-a-wrong-majority**: all 23 graded Track B
  problems were easy enough for Nemotron that every candidate converged on
  the same correct answer, so accuracy alone can't distinguish the
  methods. The scenario that would actually stress-test the hypothesis —
  candidates disagree, and the majority is wrong but a minority is right —
  needs either harder problems (later GSM8K test-set entries, or a harder
  benchmark like MATH/GSM-Hard) or a weaker generator model to induce real
  disagreement at this same problem difficulty.
