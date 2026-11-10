# Methodology

The authoritative analysis is `manuscript/main.tex` and its online supplement.
This page describes the implemented pipeline, not a second set of results.

## Two distinct questions

1. Which ranking best fits the judge's preferences?
2. Which returned answer is correct?

Kemeny optimization addresses the first question. Ground-truth grading addresses
the second. An optimal ranking need not improve answer accuracy. Established
ranking machinery is not itself the paper's proposed theoretical distinction;
see [the dated prior-art comparison](novelty_audit.md).

## Pipeline

1. **Generate:** sample candidates, homogeneously or from a heterogeneous pool.
   Distinct requested seeds do not establish independent model draws.
2. **Score:** obtain per-candidate confidence from model calls. These scores
   are not demonstrated to be calibrated probabilities. Cost is word count.
3. **Compare:** for each unordered pair, request both text orders and average
   consistently oriented soft preference weights. Define the reverse entry
   by complement, so `W[i,j] + W[j,i] = 1`. Order averaging mitigates sensitivity;
   it cancels equal additive position effects, not arbitrary judge bias.
   Identical `text.strip()` values bypass live judging and receive 0.5 each.
4. **Text consistency:** use the fraction of candidates with identical complete
   answer text. This differs from the baseline's extracted-final-answer plurality.
5. **Select:** maximize the composite score over eligible candidates.

Generation, scoring and live judging can all vary between runs. Stored outputs
allow the subsequent decision to be re-evaluated without new model calls.

## Composite selector

```text
quality_i = mean_{j != i} W[i,j]                 # singleton convention: 1
score_i   = w_quality*quality_i + w_confidence*confidence_i
            + w_consistency*consistency_i - w_cost*word_count_i

maximize   sum_i x_i * round(10000 * score_i)
subject to sum_i x_i = 1
           x_i in {0,1}
           x_i = 0 if quality_i < min_quality  # optional gate
           x_i = 0 if invalid and at least one valid candidate exists
```

The one-hot formulation is an argmax, not a new optimization algorithm.
The implementation uses a single CP-SAT worker. Coefficient rounding can
create ties or change the optimum relative to unrounded scores. Neither a
canonical candidate tie-break across solver versions nor a cross-platform
identity guarantee is implemented. Replay requires the stored inputs, order,
weights and solver environment.

## Kemeny reference

`or_select/kemeny.py` separately fits a full ranking to the same matrix. One
binary variable per unordered pair, antisymmetry and three-cycle constraints
encode a linear order. CP-SAT maximizes agreement with coefficients
`round(10000 * (W[i,j] - W[j,i]))`.

The search uses one worker and a 200,000-conflict default budget rather than a
wall-clock limit. It returns `(ranking, is_optimal)`; a feasible result without
an optimality certificate is not an exact optimum. The 854 current stored
benchmark rankings all carry `is_optimal=True` for this integerized objective.
That does not certify the unrounded objective or a unique optimal ranking.

The known weighted-win 5-approximation applies to disagreement of the **full
quality-only ranking**, not top-answer correctness or the composite selector.

## Binary theorem versus stored soft weights

The finite-pool theory assumes independent candidate correctness with rate
`p`, conditionally independent binary pairwise outcomes, common mixed-pair
accuracy `q`, fair same-class comparisons and uniform independent tie-breaking.
For three candidates with distinct wrong answers, its exact gain over plurality is

```text
Delta(p,q) = p*(1-p)*[(1-p)*(2*q-1)*(q+1) - p*(3-2*q)*(1-q)]
```

At `p=0.8`, break-even accuracy is `q*=0.8035152756999545`. The formula also
quantifies gain, not just its sign. The correlated-wrong-answer extension models
a specific collision mechanism; it is not a general model of dependent errors.

The actual pipeline averages soft preferences and adds confidence, consistency
and cost. Its mean correct-directed weight is **not** the theorem's Bernoulli
accuracy `q`. Neither RewardBench accuracy nor a mean soft score certifies the
binary threshold for this composite selector. The supplement reports those
score/collision values as separate descriptive sensitivity diagnostics.

## Audit and baselines

Ground-truth tracks compare selectors on the same saved pools. Plurality uses
extracted final answers and candidate-order tie-breaking. The legacy method
key `greedy` means **first sampled answer**, not temperature-zero decoding.
Additional offline baselines and weight ablations use the stored-judgment
subset; not every benchmark row contains the inputs for a full replay.

Weight-ablation fidelity checks equality of extracted final answers, not
candidate identity or full text. The three open-ended pilot examples have no
ground truth and illustrate mechanics only. Varying judge outputs on identical
text demonstrate run variation, but do not alone isolate whether a provider
ignored its seed. A change between forward-only and bidirectional runs also
does not isolate positional bias from live-call variation.

Track inputs and regeneration commands: [benchmark results index](benchmark_results.md).
Build prerequisites and release boundaries: [submission files](submission_files.md).
Preregistration files preserve historical plans rather than current results.
