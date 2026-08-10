# Methodology

## Problem

LLM generation is inherently probabilistic — sampling from a token
distribution, plus GPU batch-invariance and floating-point effects, means
even `temperature=0` does not guarantee reproducible output. OR-Select does
not attempt to make generation deterministic. It accepts N probabilistic
candidate answers and makes the *choice* among them deterministic and
auditable.

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
4. **Select** — solve a multi-objective integer program that picks exactly
   one winner (`or_select/selection.py`).

## Formal model

Decision variable: `x_i in {0, 1}` for each candidate `i`, `1` if selected.

```text
maximize   sum_i x_i * (w1 * quality_i + w2 * confidence_i - w3 * cost_i)
subject to sum_i x_i = 1
           quality_i >= min_quality        (optional gate)
           x_i in {0, 1}
```

`quality_i` is the Copeland-style aggregate of the pairwise matrix: the mean
weight by which candidate `i` beats every other candidate,
`mean_j W[i, j]`. Solved exactly with CP-SAT (`or_select/selection.py`),
which is deterministic given fixed inputs: the same candidate set and the
same pairwise matrix always yield the same winner, regardless of solve
order or machine.

## Determinism guarantee

```text
Same N candidates + same judge outputs -> same pairwise matrix
                                        -> same quality scores
                                        -> same IP solution
                                        -> same winner
```

The only non-deterministic stage is generation (Phase 1). Everything after
it is reproducible.

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

## Baselines to compare against

- Majority/self-consistency voting (no OR, just mode of N samples).
- Single-sample greedy decoding (no ensemble at all).
- Reranking with a single learned reward model (no pairwise judge).
- Full Kemeny-Young ranking without permutation self-consistency (tests
  whether position-bias correction matters).
