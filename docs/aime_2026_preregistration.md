# AIME 2026 (Track D) — preregistered analysis plan

> **Historical record.** Written before the run's results were seen and kept unchanged apart from errata notes (where present). Final results and interpretation: `manuscript/main.tex`, Results section. Sub-claim numbering refers to the project's earlier hypothesis document, now superseded by the manuscript.

Written before this run's results were seen (same discipline as
`docs/math_level5_preregistration.md` and `docs/reward_bench_preregistration.md`).

## Why this run exists

Track C (MATH Level 5, `docs/math_level5_preregistration.md`) was chosen
because the literature predicted it would be *unsaturated* -- that
candidates would meaningfully diverge, giving OR-Select real material to
correct a wrong self-consistency majority (hypothesis sub-claim 5). At
N=105 graded problems, it wasn't: 91.4% accuracy, all four methods tied,
only 2 disagreements total and both notational, zero correctness-changing
splits. RewardBench (`docs/reward_bench_preregistration.md`) then ruled out
"the judge just isn't good at math" as the explanation -- it scored a
perfect 49/49 on Reasoning-category preference pairs (earlier
Nemotron-3-Ultra configuration; superseded, see `docs/reward_bench_preregistration.md`). So the bottleneck
isn't judge competence; it's that MATH Level 5 doesn't reliably produce the
"wrong majority, right minority" structure sub-claim 5 needs, even on
problems chosen for difficulty.

AIME is a different kind of hard: MATH Level 5 problems are difficult but
not adversarially designed, while AIME problems (American Invitational
Mathematics Examination) are specifically constructed by competition
setters to have tempting-but-wrong shortcuts -- the exact mechanism by
which a self-consistency majority can converge on a *wrong* answer while a
minority reasoning path gets it right. This is the same reasoning Ding
(2026, already cited throughout this repo) used to justify AIME/GPQA
Diamond over MATH for studying agreement-as-correctness-signal.

## Dataset: MathArena/aime_2026, full N=30

Verified via the Hugging Face datasets-server API (not assumed):
`MathArena/aime_2026`, schema `{problem_idx, answer, problem}`, 30 rows --
AIME I and AIME II 2026 (15 problems each), the two most recent sittings of
the competition as of this writing. `scripts/fetch_aime_sample.py` fetches
all 30 (no subsampling; this is the complete available set) into
`data/aime_2026_sample.jsonl` with the same schema as
`data/math_level5_sample.jsonl`, so `scripts/math_benchmark.py` runs
against it unmodified via `--input data/aime_2026_sample.jsonl`.

**Two properties make this a better test than MATH Level 5, not just a
different one:**

1. **Answers are always integers in [0, 999]**, not LaTeX expressions. Track
   C's grader had known false-negative noise from formatting variance
   (`\frac` vs `\dfrac`, `x=5` vs `5`, differently-spaced set notation) --
   several of the "incorrect" rows in that run were arguably correct
   answers marked wrong by the heuristic string grader. Integer-exact-match
   grading has no such ambiguity: `or_select.math_eval`'s normalization
   trivially handles this case correctly.
2. **These are 2026 problems.** Being from the current year, they're about
   as close to "verifiably not in this model's training data" as a
   competition-math benchmark can get, unlike MATH-500 (published 2023,
   near-certainly seen during training by a large model).

## Power, honestly

N=30 is small. Using the same McNemar-based approach as
`docs/math_level5_preregistration.md`: at 80% power, alpha=0.05, detecting
even a strong 90/10 split among disagreements needs ~13 discordant pairs
(`(z_{a/2}+z_b)^2/(2*0.8)^2`). At N=30, that would require essentially
every problem to produce a disagreement -- not realistic. **This run is not
adequately powered to statistically confirm or refute sub-claim 5 on its
own.** Its actual job is diagnostic: does a genuinely trap-prone,
unsaturated benchmark produce *any* meaningful rate of disagreement at all,
after MATH Level 5 produced almost none? A qualitative answer (some
disagreement vs. none) is informative even without statistical power to
quantify it precisely; a full statistical test would need pooling this
result with further runs (more AIME years, or the heterogeneous-generation
pilot planned alongside this).

## Cost and sequencing

Full run: 30 problems, same per-problem cost structure as Track C (N
generations + O(N^2) judge calls + selection). At N=3 candidates/problem,
roughly 30/134 = ~22% of Track C's total call volume -- cheap and fast to
run to completion, including on the free tier. Run separately from Track C
(different output file, `outputs/aime_2026_benchmark.json`) to keep
per-benchmark provenance clean, same principle as RewardBench's own file.

## What would count as a meaningful result

- **Any real disagreement with a correctness split** (`n_or_select_corrects
  self_consistency` or the reverse nonzero) would be the first actual test
  case for sub-claim 5 across four tracks (A, B, C, D) -- meaningful
  regardless of which direction it goes.
- **Still near-zero disagreement** would be a stronger negative result than
  Track C's: it would mean even adversarially-designed, out-of-training-data
  problems don't reliably produce disagreement for this model, which
  narrows the explanation toward "this specific model is unusually
  self-consistent" rather than "MATH Level 5 specifically wasn't hard
  enough" -- informative either way, and would strengthen the case for
  trying heterogeneous generation next rather than yet another benchmark
  swap.
- **Lower absolute accuracy than Track C** would be expected and is not
  itself a finding -- AIME is a harder competition tier than MATH-500's
  Level 5 by design; the disagreement rate and its correctness pattern are
  what matters here, not the raw accuracy number.

## Addendum: heterogeneous-generation variant (same dataset, second lever)

RewardBench ruled out judge accuracy as the bottleneck; this doc's own
`--provider openrouter` run isolates the benchmark-difficulty lever. A
second, independent lever -- candidate diversity itself -- is tested by
`--provider openrouter_mixed` on the *same* `data/aime_2026_sample.jsonl`,
written to a separate file (`outputs/aime_2026_heterogeneous.json`) so the
two variables (harder benchmark vs. more diverse candidates) aren't
conflated in one dataset.

`or_select/providers.py::openrouter_heterogeneous_backends` round-robins
generation across three free OpenRouter models spanning distinct vendors
(`nvidia/nemotron-3-ultra-550b-a55b:free`, `google/gemma-4-31b-it:free`,
`z-ai/glm-5.2:free`) instead of resampling one model N times -- directly
targeting Kim et al. (2025)'s finding that capable models produce highly
correlated outputs, by construction giving the candidate pool architectural
diversity that same-model resampling cannot. The judge stays fixed on the
RewardBench-validated model (Nemotron) so only the generation-diversity
variable changes, not two things at once.

Validated at N=1 and N=2 with live calls before committing to a full run
(`n=1`: single backend, no judge call needed, correct baseline behavior;
`n=2`: one Nemotron + one Gemma candidate, real cross-vendor pairwise judge
call, deterministic winner) -- offline tests
(`tests/test_providers_offline.py::OpenrouterHeterogeneousBackendsTest`)
separately confirm each backend closure is bound to its own model, not
victim to the classic late-binding-in-a-loop bug.

Full run: N=6 (2 candidates per model) across all 30 AIME 2026 problems.
