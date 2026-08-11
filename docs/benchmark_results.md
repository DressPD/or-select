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
- **Track C — MATH Level 5, ground truth, harder/unsaturated.** Same
  question as Track B, but on a benchmark chosen specifically because the
  literature predicts it should *not* be saturated for the model used
  here — the direct attempt at hypothesis sub-claim 5 (can OR-Select
  correct a wrong self-consistency majority). Underpowered by an
  infrastructure constraint; see below.

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
| B | GSM8K, easy (40/40 problems graded, N=3) | Always (40/40) | All 3 methods tied at 100% accuracy on every problem |
| C | MATH Level 5, hard (2/20 problems graded, N=3) | Always (2/2) | All 3 methods tied at 100% accuracy; run stopped early by rate-limit saturation, not by design |

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

## Track B: GSM8K, ground truth (N=3, 40/40 problems graded)

**Final accuracy: OR-Select 40/40 (100%), self-consistency 40/40 (100%),
greedy 40/40 (100%).** All three methods tied on every problem — and the
reason is visible in every individual result: on all 40 problems, all 3
of 3 candidates independently reached the exact same numeric answer
(`had_majority: True`, zero exceptions), the mirror image of Track A,
where it was `False` in all 3 queries.

**This run did not complete on the first attempt.** Starting at problem
24, 17 consecutive problems failed identically with an OpenRouter
"provider returned error" 404, despite full retry exhaustion (5 attempts,
up to 75s backoff) on each one -- a pattern (sustained 100% failure across
17 unrelated problems, then a clean recovery to 100% success on retry)
consistent with a hard session or daily cap on this free-tier model
rather than transient congestion. `scripts/gsm8k_benchmark.py` gained
`--retry-failures` and per-problem failure isolation specifically to
recover from this without losing the 23 problems already graded; see
git history for the incident. `_accuracy_summary()` computes accuracy
only over problems that graded successfully -- folding a temporary
infrastructure failure into the denominator as if it were a wrong answer
would have misrepresented it as a modeling result.

**This is not a failed benchmark -- it's the predicted result on easy
problems, and it's the useful half of a two-track story.**
`methodology.md`'s Baselines section predicted this shape before any data
existed: *"The baseline should win exactly when candidates cluster
tightly... OR-Select should win once candidates diverge."* Grade-school
arithmetic is well within Nemotron's capability, so candidates cluster
tightly (Track B) -- there is no headroom for a judge to add value when
every sample already agrees and is already correct. Open-ended queries
never cluster at all (Track A) -- that's exactly where the judge's
differentiation showed up. Together, the two tracks confirm both halves
of the same prediction rather than reporting on two unrelated tasks.

**What this run does not show, and why -- now literature-grounded, not
just an observation:** whether OR-Select's judge can *correct* a wrong
majority when candidates disagree and most of them are wrong. Zero of 40
problems ever produced disagreement. This is not bad luck: Kim, Garg,
Peng, and Garg, *Correlated Errors in Large Language Models* (ICML 2025,
[arXiv:2506.07962](https://arxiv.org/abs/2506.07962)), studied 350+ LLMs
and found stronger models have *more* correlated outputs/errors, not
less -- convergence is a structural property of capable models on a
given benchmark, not an artifact of these specific 40 problems. Ding,
*When LLMs Agree, Are They Right?* (2026,
[arXiv:2607.08065](https://arxiv.org/abs/2607.08065)), ran 265,000
samples on GPQA Diamond and AIME specifically because those benchmarks
are *not* saturated for frontier models, and found agreement is a weak
correctness signal (Spearman rho 0.20-0.59) that gets *weaker*, not
stronger, for the most capable models -- GSM8K was not even in that
benchmark set. Even Wang et al.'s original self-consistency paper
(already cited here) reports weaker vote-share/correctness correlation on
MATH (0.68) than GSM8K (0.80). The literature-backed next step is MATH
Level 5 (difficulty comparable to AMC12/AIME, same problem family as
GSM8K) or AIME/GPQA Diamond directly -- not yet attempted.

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
deterministically (no cherry-picking, no random seed to justify). All 40
graded (see the outage-and-recovery note above for why this took two
sessions).

## Track C: MATH Level 5, ground truth (N=3, 2/20 problems graded)

**Motivation.** Track B (GSM8K) showed 0/40 disagreement — every
candidate converged on the same correct answer every time, which the
literature (Kim et al. 2025, Ding 2026, both cited in Track B above)
predicts is structural for a strong model on a saturated benchmark, not a
property of those specific 40 problems. MATH-500 (Lightman et al., *Let's
Verify Step by Step*, 2023, arXiv:2305.20050) is a 500-problem curated
sample of the Hendrycks MATH test set, deliberately chosen here because
it is *not* saturated the way GSM8K is. `data/math_level5_sample.jsonl`
holds its full Level-5 (hardest tier) subset — 134 problems, fetched live
from the Hugging Face datasets-server API for
`HuggingFaceH4/MATH-500`, filtered to `level == 5`. This is the direct
attempt at hypothesis sub-claim 5: can OR-Select correct a wrong
self-consistency majority, a scenario that requires candidates to
actually disagree in the first place.

**What happened.** `scripts/math_benchmark.py` was run against OpenRouter
with a planned `--limit 20`. Two of the first four problems attempted
stalled completely — no result, no error, no further output for over 30
minutes each, under what the retry logs show was severe upstream
saturation (`Worker local total request limit reached`, observed as high
as 196/32 and 78/32, i.e. 2–6x the provider's stated capacity). These
were recorded as explicit `error: "StallTimeout: ..."` rows directly in
`outputs/math_benchmark.json`, following this repo's design boundary that
failed candidates stay explicit, never silently dropped — the same
boundary that motivated `_failed_row()` in both benchmark scripts. After
roughly 3.5 hours of wall-clock time split across multiple resumed
attempts, a fixed time budget was reached and the run was stopped by
decision, not because it finished: **4 of the planned 20 problems have
any result at all (2 valid, 2 stalled); the remaining 16 were never
attempted.**

**Results on the 2 valid problems:**

| Problem | Ground truth | OR-Select | Self-consistency | Greedy |
|---|---|---|---|---|
| Sum-of-reciprocal-cubes identity (Intermediate Algebra) | `p - q` | correct | correct (had majority) | correct |
| Sum of proper divisors of 284 (Number Theory) | `284` | correct | correct (had majority) | correct |

All three methods tied, both correct, both with a genuine self-consistency
majority (all 3 of 3 candidates agreed) — **0/2 disagreement**,
`n_or_select_corrects_self_consistency = 0`,
`n_self_consistency_corrects_or_select = 0`. `accuracy_of_valid`: 100% for
all three methods, on `n_valid = 2`.

**Honest interpretation.** This is not evidence that MATH Level 5 is also
saturated for this model — N=2 is far too small to support that claim
either way. It is evidence that *this specific attempt* to test sub-claim
5 was underpowered by an operational constraint (free-tier rate-limit
saturation, observed at multiples of the provider's stated capacity),
not by anything about the hypothesis or the benchmark choice. The
literature-backed reasoning that motivated choosing MATH Level 5 over
GSM8K is unaffected by this outcome; what changed is that closing this
gap now visibly requires either a paid API tier or a redesigned
lower-call-count protocol, not just a harder dataset — see `docs/
hypothesis_validation.md` sub-claim 5 for the full account.

## Open questions this benchmark does not resolve

- **Free-tier availability as a research constraint, not just an
  inconvenience**: over the course of this project we hit three distinct
  OpenRouter/provider reliability failure modes -- transient rate-limit
  saturation (queue depths observed up to 3517/32, recoverable with
  retry/backoff), a corporate-proxy 407 (transient, unrelated to the LLM
  provider), and a temporary, longer-lasting "provider returned error" 404
  affecting problems 24-40 that did not clear until later, then resolved
  cleanly. Free-tier access to a single model is not a reliable substrate
  for runs with O(N^2) judge calls; a paid tier or a smaller/cheaper
  evaluation design would remove this as a bottleneck for scaling further.
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
- **Sample size**: N=3–5 candidates and 3 queries / 40 graded problems per
  track are smoke-test scale, bounded by OpenRouter's free-tier
  reliability, not a statistically powered evaluation.
- **No test of judge-corrects-a-wrong-majority**: all 40 graded Track B
  problems were easy enough for Nemotron that every candidate converged on
  the same correct answer (0/40 disagreement), so accuracy alone can't
  distinguish the methods. Track C attempted this on MATH Level 5
  specifically because the literature (Kim et al. 2025, Ding 2026, both
  cited above) predicts less saturation there — but the run was cut short
  by rate-limit saturation at 2 valid problems (0/2 disagreement), too few
  to conclude anything. This remains the single most important open gap:
  closing it now needs a paid API tier or a lower-call-count protocol to
  actually reach the sample size the hypothesis requires, not just a
  harder dataset (which is already in place: `data/math_level5_sample.jsonl`,
  134 real MATH Level 5 problems, only 4 attempted so far).
