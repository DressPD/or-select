# GPQA Diamond (Track E) — preregistered analysis plan

> **Historical record.** Written before the run's results were seen and kept unchanged apart from errata notes (where present). Final results and interpretation: `manuscript/main.tex`, Results section. Sub-claim numbering refers to the project's earlier hypothesis document, now superseded by the manuscript.

Written before this run's results were seen (same discipline as
`docs/math_level5_preregistration.md`, `docs/aime_2026_preregistration.md`,
and `docs/reward_bench_preregistration.md`).

## Why this run exists

Tracks C (MATH Level 5) and D/D-het (AIME 2026, homogeneous and 3-vendor
heterogeneous generation) together graded 173 problems and found **zero**
cases of OR-Select and self-consistency disagreeing on a genuinely wrong
majority — hypothesis sub-claim 5 (can OR-Select correct a wrong
self-consistency majority) remains untested, not refuted, because its
precondition never arose.

Interpreting that null result against the literature (`docs/methodology.md`)
surfaced a specific, checkable explanation rather than "just run more
samples": Ding (2026, arXiv:2607.08065) documents the "wrong majority,
confident agreement" phenomenon specifically on GPQA Diamond, for frontier
models — for the most consistent frontier model in that study, ≥0.8
agreement occurred on 77% of GPQA case-result entries, and 48% of *those*
were wrong. That is a much higher base rate than AIME/MATH produced here.
Two explanations are live and this run cannot fully separate them (see
"What would count as a meaningful result" below):

1. This project's free-tier candidate generators (Nemotron-3-Ultra,
   LFM-2.5, and the openrouter_mixed third slot) are not "frontier" in the
   sense Ding's finding is about, so the phenomenon may not transfer.
2. AIME/MATH Level 5 are the wrong benchmark family for this — GPQA
   Diamond, not competition math, is where Ding's own strongest signal was.

Running GPQA Diamond on the *same* model tiers as Tracks D/D-het isolates
explanation (2) from (1): if disagreement still doesn't appear here, the
benchmark-family hypothesis is weakened and the model-tier hypothesis
strengthens; if it does appear, GPQA Diamond specifically (not just "harder
benchmarks" generally) is the missing ingredient, independent of model
tier.

## Dataset: GPQA Diamond, full N=198

Rein et al., *GPQA: A Graduate-Level Google-Proof Q&A Benchmark* (COLM
2024, arXiv:2311.12022) — graduate-level, PhD-written multiple-choice
questions in biology, physics, and chemistry. Diamond is the
highest-quality 198-question subset: questions where a non-expert
validator with web access got it wrong but an expert validator confirmed
the correct answer, i.e. calibrated to resist both casual guessing and
search-engine lookup. The dataset ships with a canary string and a
password-gated release specifically to deter training-data contamination
(see `scripts/fetch_gpqa_sample.py`'s docstring) — about as close to
"verifiably unseen" as a widely-cited benchmark gets, similar in spirit to
AIME 2026's recency argument but via a different mechanism (contamination
resistance vs. publication date).

`scripts/fetch_gpqa_sample.py` fetches all 198 (no subsampling, matching
the "full available set" precedent set by Tracks C and D) into
`data/gpqa_diamond_sample.jsonl` — **gitignored**, unlike the AIME/MATH
sample files, because committing the plaintext questions to this repo's
git history would work against the benchmark's own contamination-resistance
design even though its CC-BY 4.0 license permits redistribution. Re-run the
fetch script to regenerate it locally.

**Format differs from MATH/AIME in a way that removes a known confound.**
GPQA is 4-way multiple choice (1 correct + 3 incorrect answers, shuffled
once per problem into a fixed A/B/C/D order by the fetch script). Grading
is exact-letter-match (`or_select/gpqa.py`) — there is no LaTeX-formatting
ambiguity to introduce grader false negatives, unlike MATH Level 5's
`\dfrac` vs `\frac` / reordered-set-notation artifacts
(manuscript, Results section). Any disagreement or accuracy gap found
here cannot be dismissed as a grading artifact the way several of Track C's
were.

## Model tiers: same as Tracks D/D-het, deliberately unchanged

Two variants, both on the free OpenRouter tier, run separately:

- **Homogeneous** (`--provider openrouter`, `outputs/gpqa_benchmark.json`):
  single model (Nemotron-3-Ultra, RewardBench-validated as judge) resampled
  N=3 times per problem, mirroring Track D exactly.
- **Heterogeneous** (`--provider openrouter_mixed`,
  `outputs/gpqa_heterogeneous.json`): `OPENROUTER_MIXED_MODELS` (Nemotron +
  poolside/laguna-s-2.1 + LFM-2.5, judge fixed on Nemotron), N=6 per
  problem, mirroring Track D-het exactly, including its 2025-08-22 model
  swap for the delisted `openai/gpt-oss-20b:free`.

This is a deliberate choice, not an oversight: the point of this run is to
test the *benchmark* variable while holding the *model-tier* variable fixed
at exactly what Tracks D/D-het used, so a difference in outcome is
attributable to GPQA Diamond itself rather than a confounded model upgrade.

## Power, honestly

Same structure as `docs/aime_2026_preregistration.md`: at N=198 (vs. AIME's
30), this run has meaningfully more power if disagreement occurs at all,
but free-tier infrastructure has been the binding constraint in every prior
track, not sample size — Tracks D/D-het plateaued at 15/30 and 11/30 valid
despite the full 30-problem set being attempted. **This run is not expected
to reach full completion on the free tier**, based directly on that
precedent (Track D-het alone took the better part of a day of wall-clock
time to attempt 30 problems under heavy `StallTimeout`/Nvidia-502
congestion). Whatever partial N it reaches before plateauing is still
informative by the same logic as Tracks C and D: a plateau at N=40-60 with
zero disagreement would already exceed Track D's combined AIME sample size
and be a meaningfully stronger negative result if it holds.

## What would count as a meaningful result

- **Any real disagreement with a correctness split** would be the first
  actual test case for sub-claim 5 across five tracks (A, B, C, D, E) — and
  because GPQA's grading has no formatting-ambiguity confound, a disagreement
  found here is unambiguous, unlike Track C's two notational near-misses.
- **Still zero disagreement**, even at partial completion, would meaningfully
  narrow the explanation space: it would suggest the "wrong majority,
  confident agreement" phenomenon Ding (2026) documents is specific to
  frontier-tier models, not a property of GPQA Diamond as a benchmark family
  — strengthening explanation (1) over (2) above, and pointing toward paid
  frontier-tier models (not further benchmark swaps) as the next lever if
  sub-claim 5 is to be resolved.
- **A lower absolute accuracy than AIME/MATH** would be expected (GPQA
  Diamond is calibrated to be hard for non-experts and is a different
  domain — science reasoning, not competition math) and is not itself a
  finding; the disagreement rate and its correctness pattern are what this
  run is actually testing.

## Cost and sequencing

Run separately from every prior track (`outputs/gpqa_benchmark.json`,
`outputs/gpqa_heterogeneous.json`) for clean per-benchmark provenance, same
principle as every earlier track. Launched via the same `--resume
--retry-failures` loop used for Tracks D/D-het, expected to run across
multiple sessions/checks given the precedent above.
