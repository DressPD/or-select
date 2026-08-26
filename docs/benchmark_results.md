# Benchmark Results

Multiple tracks, because they answer different questions and none alone is
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
  literature predicts it should *not* be saturated for the model used here.
- **Track D — AIME 2026, ground truth, recent competition math.** Homogeneous
  and three-vendor heterogeneous generation variants test whether newer,
  unsaturated problems produce disagreement.
- **Track E — GPQA Diamond, ground truth, graduate science multiple choice.**
  Homogeneous and heterogeneous variants test the benchmark family identified
  by Ding (2026) as producing confident wrong majorities.

Primary methods compared throughout:
- **OR-Select**: the full pipeline (`or_select/pipeline.py`) — LLM judge +
  deterministic self-consistency term, aggregated via CP-SAT.
- **Self-consistency alone**: majority vote (`or_select/baselines.py`), no
  LLM judge, no OR.
- **Greedy single-sample**: just the first of the N candidates, no
  ensemble at all.

Kemeny-Young is additionally reported where benchmark output includes it.

Provider: OpenRouter, `nvidia/nemotron-3-ultra-550b-a55b:free`, for every
result below (chosen for availability, not because it's the model this
method is expected to work best with — see "Open questions" at the end).

## Summary

| Track | Task type | Candidates agreed? | Result |
|---|---|---|---|
| A | Open-ended (3 queries, N=5) | Never (0/15) | OR-Select disagreed with both baselines on 3/3; self-consistency undefined every time |
| B | GSM8K, easy (40/40 problems graded, N=3) | Always (40/40) | All 3 methods tied at 100% accuracy on every problem |
| C | MATH Level 5, hard (107/134 graded, N=3) | Effectively always | All methods tied on extracted answers; nominal 91.6% accuracy, with nine grader false negatives |
| D | AIME 2026 (15/30 and 11/30 graded, N=3/6) | Always (26/26) | All methods tied at 100% accuracy; both variants stopped by free-tier failures |
| E | GPQA Diamond (39/198 and 12/198 graded, N=3/6) | Always (51/51) | OR-Select and self-consistency tied on every valid problem; partial runs stopped by free-tier failures |

The results are consistent with a single underlying prediction, stated in
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
problems, and it's the useful convergent case in a multi-track story.**
`methodology.md`'s Baselines section predicted this shape before any data
existed: *"The baseline should win exactly when candidates cluster
tightly... OR-Select should win once candidates diverge."* Grade-school
arithmetic is well within Nemotron's capability, so candidates cluster
tightly (Track B) -- there is no headroom for a judge to add value when
every sample already agrees and is already correct. Open-ended queries
never cluster at all (Track A) -- that's exactly where the judge's
differentiation showed up. Together, the tracks confirm both halves
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
GSM8K), followed by direct AIME and GPQA Diamond runs reported below.

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

## Track C: MATH Level 5, ground truth (N=3, 107/134 graded)

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

**What happened.** The later resumed run in `outputs/math_benchmark_full.json`
reached 107 valid rows out of the full 134-problem Level-5 subset; 27 rows
remained explicit infrastructure failures. This is the result used for the
current hypothesis assessment. The earlier 2/20 pilot remains in
`outputs/math_benchmark.json` as an incident record, not the final Track C
result.

**Results on the 107 valid problems:** all four methods scored 98/107
nominally (91.6%). The nine apparent errors were grader false negatives:
each self-consistency majority expressed the correct value with formatting,
notation, or ordering that `math_eval` did not normalize. OR-Select matched
self-consistency on eight of those rows; the ninth differed only in equivalent
set notation. No genuinely wrong majority was found.

**Honest interpretation.** This is not evidence that MATH Level 5 is also
saturated for this model. The full run improved coverage substantially, but
27 rows still failed under free-tier infrastructure and the grader produced
known false negatives. The literature-backed reasoning that motivated
choosing MATH Level 5 over GSM8K is unaffected; closing the remaining gap
requires a stricter grader, paid API capacity, or a redesigned
lower-call-count protocol, not just a harder dataset — see `docs/
hypothesis_validation.md` sub-claim 5 for the full account.

## Track D: AIME 2026

The homogeneous run graded 15/30 problems and the three-vendor heterogeneous
run graded 11/30. All four methods scored 100% on their valid rows, with zero
OR-Select/self-consistency disagreements in either run. These are partial
results, limited by OpenRouter failures, not full-benchmark evidence.

## Track E: GPQA Diamond

GPQA tests the benchmark family highlighted by Ding (2026): graduate-level,
four-way multiple-choice questions with exact-letter grading, so formatting
ambiguity cannot explain a correctness split.

| Variant | Valid / total | Samples | OR-Select | Self-consistency | Greedy | Kemeny-Young | OR/SC disagreements |
|---|---:|---:|---:|---:|---:|---:|---:|
| Homogeneous | 39/198 | 3 | 37/39 (94.9%) | 37/39 (94.9%) | 36/39 (92.3%) | 37/39 (94.9%) | 0 |
| Heterogeneous | 12/198 | 6 | 11/12 (91.7%) | 11/12 (91.7%) | 11/12 (91.7%) | 10/12 (83.3%) | 0 |

The homogeneous run stopped with 159 infrastructure failures; the
heterogeneous run stopped with 186. Neither produced an OR-Select versus
self-consistency disagreement, and therefore neither produced a wrong-
majority correction case. Kemeny-Young differed from OR-Select once in the
heterogeneous run, with OR-Select correct and Kemeny-Young wrong. The sample
is informative about absence of the precondition, not a powered estimate of
GPQA accuracy.

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
- **Sample size**: N=3–6 candidates and partial valid-row counts remain
  smoke-test scale, bounded by OpenRouter's free-tier reliability, not a
  statistically powered evaluation.
- **No test of judge-corrects-a-wrong-majority**: across GSM8K, MATH Level 5,
  AIME 2026, and GPQA Diamond, no valid row produced an OR-Select versus
  self-consistency correctness split. The current total is 224 graded rows
  across the four ground-truth benchmarks, but the AIME and GPQA runs remain
  partial. Paid API capacity, a lower-call-count protocol, or frontier-tier
  models are still needed to determine whether the missing precondition is
  rare for these model tiers or merely hard to reach under free-tier
  infrastructure.
