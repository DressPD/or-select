# Methodology

## Problem

LLM generation is inherently probabilistic — sampling from a token
distribution, plus GPU batch-invariance and floating-point effects, means
even `temperature=0` does not guarantee reproducible output. OR-Select does
not attempt to make generation deterministic. It accepts N probabilistic
candidate answers and makes the *choice* among them deterministic and
auditable.

## Related work

**Aggregating multiple LLM judgments via OR/social-choice methods, not a
single LLM call:**

- Tang et al., *Found in the Middle: Permutation Self-Consistency Improves
  Listwise Ranking in LLMs* (NAACL 2024) — the permutation self-consistency
  technique used in `pairwise.py` is directly from this paper. Its own
  "central ranking" aggregation step is itself a Kemeny-style consensus
  operation, i.e. this citation already rests on OR/social-choice ground,
  not just position-bias correction.
- Liu et al., *Aligning with Human Judgement: The Role of Pairwise
  Preference in LLM Evaluators (PAIRS)* (COLM 2024) — pairwise comparison
  + rank aggregation outperforms asking an LLM to pick directly, on
  long-form generation.
- *LLM-PeerReview: Scoring, Reasoning, and Selecting the Best!* (2025) —
  the closest prior art: multiple LLM judges score N candidates, aggregated
  via a Dawid-Skene-style graphical truth-inference model. OR-Select
  differs by aggregating via an integer program over a pairwise matrix plus
  a deterministic self-consistency term, rather than an EM-based score
  model.
- *LLMs Judge Themselves: A Game-Theoretic Framework for Human-Aligned
  Evaluation* (2025) — compares Borda, Copeland, and Kemeny-Young
  aggregation of multiple LLM judges; Kemeny-Young best aligns with human
  preference. `selection.py`'s Copeland-style `quality_i` is a Kemeny-Young
  approximation, consistent with this finding.
- Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*
  (NeurIPS 2023) — foundational LLM-as-judge paper; documents position bias
  as a first-class judge failure mode, motivating the permutation
  self-consistency step.

**Cautions that materially bear on this design, not just background:**

- *Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM
  Evaluation Panels* (2026) — a 9-judge panel carries roughly the
  independent signal of 2 votes because models make correlated errors, and
  better aggregation math closes at most 11% of that gap. This bears
  directly on `--provider both`/`all`: whether OpenAI/Gemini/OpenRouter
  judges are architecturally/training-data diverse enough to actually
  reduce correlated error, versus just adding compute cost, is untested
  here and should be treated as an open question, not an assumption.
- Landesberg, *When LLM Judge Scores Look Good but Best-of-N Decisions
  Fail* (2026) — judge calibration/agreement metrics do not predict actual
  best-of-N selection accuracy. This is why the Hamlet/traffic/rent-vs-buy
  runs earlier in this project, while illustrative of the pipeline
  mechanics, do not constitute evidence of selection quality: there is no
  ground truth to check the selection against. See the GSM8K benchmark
  below for a design that does have ground truth.

## Pipeline

1. **Generate** — sample N candidate answers (`or_select/generate.py`), same
   model with different seeds or heterogeneous models for diversity.
   `or_select/providers.py` wires this to real OpenAI and Gemini calls;
   `--provider both` splits the N candidates across both, which is the
   configuration used to validate that determinism holds independent of
   which vendor produced a given candidate.
2. **Score** — calibrated per-candidate confidence (`or_select/scoring.py`).
3. **Compare** — build a pairwise win matrix `W[i, j]` via an LLM judge,
   using permutation self-consistency: judge each pair in both orders and
   average the two votes, to cancel positional bias (`or_select/pairwise.py`).
   Each unordered pair is judged exactly once (2 calls: forward + backward);
   the reverse entry `W[j, i]` is derived as `1 - W[i, j]` rather than
   re-judged, since the two are exact complements by construction — this
   halves the judge call count for a given N compared to judging every
   ordered pair independently. Pairs with byte-identical (normalized) text
   skip the judge call entirely and are assigned the exact `0.5/0.5` their
   symmetry demands, rather than risking a live LLM call returning a
   non-symmetric result for a comparison that isn't actually in question
   (see "A concrete finding" below).
3b. **Self-consistency** — compute a purely deterministic agreement score,
   `consistency_i = (# candidates matching i's text) / N`
   (`or_select/consistency.py`), with zero LLM calls.
4. **Select** — solve a multi-objective integer program that picks exactly
   one winner from quality, confidence, consistency, and cost
   (`or_select/selection.py`).

## Formal model

Decision variable: `x_i in {0, 1}` for each candidate `i`, `1` if selected.

```text
maximize   sum_i x_i * (w1*quality_i + w2*confidence_i
                         + w4*consistency_i - w3*cost_i)
subject to sum_i x_i = 1
           quality_i >= min_quality        (optional gate)
           x_i in {0, 1}
```

`quality_i` is the Copeland-style aggregate of the pairwise matrix: the mean
weight by which candidate `i` beats every other candidate,
`mean_j W[i, j]`. `consistency_i` is the deterministic self-consistency
signal (`or_select/consistency.py`) — the fraction of candidates whose text
matches `i`'s exactly, i.e. classic self-consistency voting expressed as an
IP objective term rather than a standalone decision rule. It is optional
(defaults to 0 contribution) and additive alongside the LLM-judged quality,
not a replacement for it: consistency alone only captures agreement
frequency, and degenerates to a flat `1/N` once candidates stop repeating
(e.g. open-ended queries where every sample differs). Solved exactly with
CP-SAT (`or_select/selection.py`), which is deterministic given fixed
inputs: the same candidate set, pairwise matrix, and consistency scores
always yield the same winner, regardless of solve order or machine.

## Determinism guarantee

```text
Same N candidates + same judge outputs -> same pairwise matrix
                                        -> same quality scores
                                        -> same IP solution
                                        -> same winner
```

The only non-deterministic stage is generation (Phase 1). Everything after
it is reproducible *given fixed inputs* — but "given fixed inputs" is doing
real work here, since scoring and judging are themselves LLM calls:

- **OpenAI, OpenRouter**: `or_select/providers.py` sends a `seed` derived
  deterministically from the prompt content (`_stable_seed`) for every
  score/judge call, so re-running the pipeline over an *unchanged* candidate
  set requests the same seed each time. This is provider best-effort, not a
  hard guarantee — vendors document `seed` as reducing, not eliminating,
  run-to-run variance.
- **Gemini**: the SDK path used here has no seed parameter, so
  `gemini_score`/`gemini_judge` are not seeded at all. Re-running the
  pipeline over the same candidates can get different confidence/judge
  values from Gemini, which can change the winner even though the *solve*
  itself is exact given whatever scores it receives.

So the precise claim is: the selection step (Phase 4) is exactly
reproducible given a fixed pairwise matrix and fixed scores. Whether the
matrix and scores themselves are stable across runs depends on the
provider.

### A concrete finding

A live run against OpenRouter (`nvidia/nemotron-3-ultra-550b-a55b:free`)
produced 3 candidates with byte-identical text, which by construction
should force every pairwise weight among them to exactly 0.5 (forward and
backward calls are the literal same prompt, so `(v + (1-v))/2 = 0.5`
regardless of what the model returns). The observed quality scores were
0.375, 0.50, and 0.625 instead — direct empirical proof that `seed` is not
reliably enforced by this provider/model in practice, not just a
theoretical caveat. The exact-match short-circuit above closes this
specific case entirely (identical text never reaches the judge, so it
can't be corrupted by this failure mode) but does not address the general
case: two candidates with *different* text can still get non-reproducible
judge scores across runs, since a real semantic comparison still requires
an LLM call.

## Extensions (not yet implemented in the scaffold)

- **Full ranking (Kemeny-Young)**: instead of selecting one winner, produce
  a full deterministic ranking over all N candidates by adding transitivity
  constraints (`x_ij + x_jk + x_ki <= 2`) to the IP. Useful when downstream
  consumers need a ranked list, not just a top-1 pick.
- **Space reduction**: pre-solve pairs with near-unanimous votes
  (`W[i,j] > 0.95`) before running the IP, to scale beyond N=10-20
  candidates.
- **Multi-objective terms**: diversity (penalize near-duplicate winners),
  safety gating (hard constraint on a safety classifier score), uncertainty
  weighting (down-weight judge votes with low confidence).
- **Adaptive refinement**: use Bayesian optimization to propose a targeted
  refinement of the current winner instead of stopping at top-1.

## Baselines and benchmarks

- **Majority/self-consistency voting alone** (no OR, no LLM judge — just
  pick the mode of N samples), per Wang et al., *Self-Consistency Improves
  Chain of Thought Reasoning in Language Models* (ICLR 2023). Distinct from
  the `consistency_i` term in the formal model above: the baseline uses
  agreement frequency as the *entire* decision rule, while OR-Select uses
  it as one additive term in an IP alongside LLM-judged quality.
- Single-sample greedy decoding (no ensemble at all).
- Reranking with a single learned reward model (no pairwise judge) — see
  PairRM / LLM-Blender (Jiang et al., ACL 2023) as a candidate `judge_fn`
  replacement: a small, local, fixed-weight pairwise reward model that
  sidesteps the provider-seed non-determinism documented above entirely.
- Full Kemeny-Young ranking without permutation self-consistency (tests
  whether position-bias correction matters).

**Benchmarks with ground truth (`scripts/gsm8k_benchmark.py`):**

- **GSM8K** (Wang et al., ICLR 2023's evaluation protocol) — grade-school
  math word problems with a single correct numeric answer. This is the one
  benchmark here where "OR-Select's winner is correct" is a checkable fact,
  not a subjective judgment call, directly addressing the Landesberg
  caution above. Small-N runs (5-10 problems, N=5) are cheap enough to run
  against a free-tier provider.
- **RewardBench** (Allen Institute for AI, NAACL 2025 Findings) — proposed
  but not yet run: human-labeled pairwise preferences, usable to validate
  `judge_fn` in isolation against ground truth, independent of the full
  selection pipeline.
