# RewardBench judge validation — preregistered analysis plan

Written before this run's results were seen (same discipline as
`docs/math_level5_preregistration.md`).

## Why this run exists

Every benchmark result so far (`docs/benchmark_results.md`,
`docs/hypothesis_validation.md`) measures the *full pipeline* — OR-Select's
selection vs. baselines, against either no ground truth (Track A) or
ground-truth final answers (Tracks B, C). None of them isolate whether
`judge_fn` itself — the pairwise LLM judge that `quality_i` is built from —
is actually accurate. `docs/methodology.md`'s "Baselines and benchmarks"
section named this gap explicitly: RewardBench (Lambert et al., NAACL 2025
Findings), "proposed but not yet run." This closes it.

This matters because of the Landesberg (2026) caution already cited
throughout this repo: judge calibration/agreement metrics do not predict
actual selection accuracy. Track A's finding that OR-Select "adds real
value once candidates meaningfully diverge" is only as trustworthy as the
judge producing that differentiation. If the judge itself is inaccurate,
Track A's disagreements could reflect judge noise, not real quality
differences — this run is the direct test of that possibility.

## What's measured, and how

`scripts/reward_bench_benchmark.py` grades `judge_fn` in isolation: for
each RewardBench (prompt, chosen, rejected) triple, it calls
`or_select.pairwise.build_pairwise_matrix` on exactly those two candidates
— the identical forward+backward permutation-self-consistency code path the
real pipeline uses, not a reimplementation — and checks whether the
resulting weight favors `chosen` (RewardBench's human-labeled correct
answer) over `rejected`.

## Sample: N=161, stratified across all 23 subsets

`data/reward_bench_sample.jsonl`: the first 7 rows of each of RewardBench's
23 subsets (`scripts/fetch_reward_bench_sample.py`), in the dataset's own
served order — deterministic, no shuffling. Equal per-subset representation
was chosen deliberately over sampling proportional to each subset's raw
size: `math-prm` alone has 447 of the 2985 total rows, and RewardBench's
own published scoring convention already treats each subset as an equally
weighted unit within its category (`or_select/reward_bench.py`'s
`score_summary` mirrors that convention: category score = mean of its
subsets' accuracies, not a pooled/micro-average).

**Power**: for a single overall-accuracy proportion at N=161, the 95%
margin of error at the hardest-to-estimate point (p=0.7, near typical
published reward-model accuracy on this benchmark) is about ±7.1%
(`1.96*sqrt(0.7*0.3/161)`). Adequate to distinguish "this judge is roughly
in the range of published reward models" from "this judge is much worse
than that," not adequate to detect small differences between categories
(the 4 category scores are each based on only ~35-42 rows, wider margins
there — reported per-category, not glossed into a single number).

**Cost**: 2 judge API calls per row (forward + backward), 322 total — much
cheaper than Track C's per-problem cost (which needs N generations plus
O(N^2) judge calls plus a selection solve per problem), but still bound by
the same OpenRouter free-tier throughput that has been the actual
bottleneck on every live run in this project so far.

## Sequencing: queued behind Track C, not run in parallel

Track C (MATH Level 5, N=134) is the higher-priority, already-committed run
and is live on the same free-tier OpenRouter pool. Running this benchmark
concurrently would split that single scarce resource between two jobs and
likely slow both — observed empirically already: every live run in this
project has been bottlenecked by OpenRouter saturation, not by request
volume being near any documented limit. This run is built, tested, and
ready (`--provider placeholder` smoke-tested end to end), but is
deliberately not started until Track C completes or is otherwise paused.

## What would count as a meaningful result

- **Overall accuracy in the range typically reported for capable
  general-purpose LLM judges on RewardBench (roughly 70-90%)** would
  support trusting this repo's judge-based `quality_i` term as a reasonably
  calibrated signal, strengthening the credibility of every prior result
  built on top of it (most directly Track A).
- **A large gap between Chat/Safety accuracy and Chat-Hard/Reasoning
  accuracy** would replicate RewardBench's own published finding that
  judges are much better at easy preference calls than adversarial or
  reasoning-heavy ones — and would be a direct, actionable caution for
  when to trust OR-Select's differentiation and when not to.
- **Accuracy far below chance-adjacent (near 50%) on any category** would
  be a serious finding requiring the judge_fn implementation itself to be
  audited before trusting any other result in this repo that depends on it.

## Results (actual)

> **Superseded on 2026-11-01.** The figures below were obtained on 2026-08-22 with
> Nemotron-3-Ultra and the earlier reasoning-enabled judge call. The shipped judge
> (Nemotron-3.5-Lightning, reasoning disabled, 256-token cap, in use since 2026-10-07)
> scores **60.5%** overall on the same 161 rows (Reasoning 73.5%, Chat 68.6%, Safety 57.1%,
> Chat Hard 42.9%), below the range this document treats as sufficient to trust the judge.
> The record below is kept as the pre-registered result of the earlier configuration.

Full N=161, 0 infra failures. **Overall accuracy: 90.1%** (mean of category
means), squarely in the "trust the judge" range this doc predicted before
the run.

| Category | Accuracy | Rows |
|---|---|---|
| Chat | 100.0% | 35 |
| Reasoning | **100.0%** | 49 |
| Chat Hard | 83.3% | 42 |
| Safety | 77.1% | 35 |

**The load-bearing number for this project: Reasoning is a perfect 49/49**
across all 7 subsets (`math-prm` and all six `hep-*` code-language
subsets). This is the direct answer to the open question this doc was
written to resolve: `judge_fn` is not the bottleneck on math/code
preference judgments. Track A's "OR-Select differs meaningfully once
candidates diverge" finding, and every subsequent Track C run's *lack* of
disagreement, can now be read with more confidence — if disagreement had
occurred on MATH Level 5, this judge looks capable of using it
productively, rather than the earlier "maybe the judge just isn't good
enough at math" being an unfalsified alternative explanation.

**The rest of the result is fully explained, not a mystery:**

- **Safety's weak point is isolated to one subset, `donotanswer`
  (1/7 = 14.3%)**, not a general safety-judgment failure —
  `refusals-dangerous`, `refusals-offensive`, and `xstest-should-respond`
  are all 7/7. Root cause identified from `prompts/judge_prompt.txt`: the
  judge is instructed to evaluate "accuracy, completeness, and coherence,"
  with no safety criterion, so it systematically favors a detailed but
  unsafe/inappropriate response over a correct refusal on `donotanswer`'s
  more borderline cases. This is a prompt-design gap, not evidence against
  the OR aggregation math, and would need a safety-aware judge instruction
  to fix — out of scope for what this run was testing.
- **Chat Hard (83.3%)** lands in the middle of its per-subset range
  (57.1%-100%), consistent with RewardBench's own published finding that
  the adversarial LLMBar subsets are specifically constructed to be hard
  for judges. Not a surprise, not a red flag.

**Net effect on the plan**: this clears heterogeneous-generation and/or an
adversarial-trap benchmark (e.g. AIME-style) as the next lever to pull for
sub-claim 5, since the judge's reasoning competence is no longer the
suspected bottleneck — the bottleneck is candidate diversity (Track C's
near-total convergence), not the judge's ability to use disagreement once
it exists.
