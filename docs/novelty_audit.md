# Online novelty and EJOR-strength audit

**Internal author document — not a manuscript attachment.**

Search date: **10 November 2026**. Scope: the current OR-Select manuscript,
closest inference-time answer-selection papers, preference-aggregation theory,
recent negative judge studies, and EJOR's stated editorial requirements.

## Decision

**A specific potentially original result remains; EJOR publication strength is
not established by this search.** No matching derivation of the exact
finite-pool binary-Copeland versus answer-plurality threshold was found in the
sources examined. This is a bounded literature-search finding, not a proof of
priority or a guarantee against uncatalogued, differently named or unpublished work.

The theorem's algebra and the significance of its contribution are different
questions. Exact enumeration supports the former. A short elementary closed
form, established optimization machinery, and an audit of one weak judge do not
automatically meet a major OR journal's methodological-significance requirement.
The manuscript now presents its actual distinction without claiming first judge
failure, a new Kemeny algorithm, a new 5-approximation or a universal judge test.

## Search method and boundaries

Searches combined `pairwise judge`, `Copeland`, `plurality`, `majority voting`,
`finite sample`, `finite N`, `three candidates`, `correctness`, `accuracy
threshold`, noisy tournaments and the titles of closest recent studies.
Publisher/proceedings pages checked publication metadata; arXiv primary texts
were used for methodological comparisons. A numerical-string search was not
treated as novelty evidence.

Primary full-text comparisons cover the closest Best-of-Majority,
Best-of-Infinity, Beyond Majority Voting, Minority Sentinel and PGED work;
PGED's model, recovery theorem and response-selection results were inspected.
The recent Agreement Overstates Evidence entry below is an abstract-level
scope check, not a full independent review. Classical work supplies model
context, not an exhaustive historical survey of every tournament probability.
No plagiarism or exhaustive citation-index clearance is claimed.

## Closest prior art

| Source | What already exists | Specific distinction in this manuscript |
|---|---|---|
| Di et al., **Best-of-Majority**, ICLR 2026 | Frequency-filtered reward selection; pass-at-budget minimax regret bounds and matching lower bound | Fixed binary pairwise tournament; exact finite-pool correctness difference from answer plurality, not a new minimax selection algorithm |
| Komiyama et al., **Best-of-Infinity**, ICLR 2026 | Asymptotic ensemble analysis, optimized model mixtures/MILP, adaptive budgeting, and voting outperforming practical judges | Exact comparison-reliability threshold at fixed candidate accuracy and finite pool size; neither judge failure nor IP alone is new |
| Ai et al., **Beyond Majority Voting**, ICML 2026 | Reliability weighting and higher-order information for heterogeneous, correlated predictions | Mixed-pair comparison accuracy for a specified Copeland rule, not a general solution to correlated aggregation |
| Hu et al., **PGED**, arXiv v5, January 2026 | Multiple-evaluator preference graphs, denoising, preference-DAG recovery guarantee, response selection | Correct-answer probability relative to answer plurality under two correctness classes; not the first graph/ranking aggregation guarantee |
| He et al., **Minority Sentinel**, June 2026 | Three-agent debate majority overrides, a learned selective rule, a break-even override criterion, and a negative GPT-4o judge result | Full Copeland tournament under an explicit candidate/comparison model; mixed-pair `q` is not override precision |
| Coppersmith et al., **Ordering by Weighted Number of Wins**, 2010 | Weighted-win ranking's 5-approximation for tournament disagreement | Borrowed result only; it is not an answer-accuracy guarantee |
| Young; Caragiannis et al., noisy voting/ranking | Truth/rank recovery under noisy preference or voting models | Fair within-correctness-class comparisons and repeated correct answers versus distinct/colliding wrong answers; not a claim that noisy-vote analysis itself is new |
| Hossain et al., **Agreement Overstates Evidence**, September 2026 | Dependence can invalidate naive judge-consensus interpretation; correlation structure matters | Collision sensitivity is a specific extension, not a general dependence correction |

### Why the negative result is not the novelty

Best-of-Infinity already reports AIME 2025 majority voting at 85.42% versus an
LLM tournament at 82.92% and a set-based judge at 81.25% (Table 2). Minority
Sentinel reports negative net gain for a GPT-4o debate judge. These settings are
not direct benchmark replications of OR-Select, but they defeat any broad claim
that showing a judge lose to voting is new or overturns consensus.

### Defensible contribution statement

> Under an explicitly independent binary-comparison model, the paper derives
> the exact finite-pool correctness advantage of Copeland selection over answer
> plurality, obtains the three-candidate break-even condition, and studies its
> finite-pool, wrong-answer-collision and pair-dependent extensions. An offline
> audit separately compares answer correctness and preference-ranking fit on
> fixed stored candidate pools.

The large-pool error-decay obstruction in the supplement is additional theory,
not evidence that the actual soft-score/composite selector obeys that model.
The precise priority of every extension has not been independently established.

## What would justify a stronger EJOR recommendation?

EJOR's editorial policy requires a major new research finding or novel OR
approach; technical correctness and supportive reviews alone do not ensure
acceptance. The present assessment remains **major revision / research-strength
decision required**, not a submission-ready certification.

Two distinct routes could substantively strengthen the work:

1. **Theory-led:** establish a consequential result beyond the small stylized
   case—for example, a verified comparison for the implemented soft-score rule,
   or a nontrivial broader theorem with a demonstrable decision implication.
   Existing finite-pool enumeration and asymptotic bounds should be evaluated
   for that role, not advertised as a new algorithm.
2. **Method-led:** demonstrate an actionable selector or selection policy on
   held-out tasks, with stronger judge configurations and controlled comparisons
   against voting and pertinent current methods. The design must separate judge
   effects from objective weights, length and candidate-model composition.

Neither route has been completed by editing prose. New scientific results must
be proved or measured before entering the paper. New paid/live model runs were
not authorized or performed in this audit.

The earlier internal review also records paired-effect precision, mathematical
grading sensitivity and public GPQA replay limitations. Those are author-side
validation/packaging matters, not a list of unfinished tasks inserted into the
article. Necessary truthful model and data-access disclosures remain.

## Changes made from this check

- Added PGED and Minority Sentinel to the article's comparison with prior work.
- Updated Best-of-Majority, Best-of-Infinity and Beyond Majority Voting to their
  verified 2026 conference metadata; retained citation keys for compatibility.
- Aligned README, methodology, ablation interpretation, result-regeneration
  notes and explanatory code docstrings with the paper's actual scope.
- Kept historical preregistrations, collected data and numerical macro contents
  unchanged. Verification evidence is `docs/ejor_repo_audit.json`.
- Distinguished local manuscript revisions from the published v1.0.0 archive.

## Primary sources

1. [Best-of-Majority: official ICLR 2026 proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/94cbc452f8fe10cc6350e3c06fe75171-Abstract-Conference.html);
   [primary text](https://arxiv.org/html/2510.03199).
2. [Best-of-Infinity: official ICLR 2026 program](https://iclr.cc/virtual/2026/poster/10011606);
   [primary text](https://arxiv.org/html/2509.21091).
3. [Beyond Majority Voting: ICML 2026, PMLR 306:1311–1340](https://proceedings.mlr.press/v306/ai26d.html);
   [primary text](https://arxiv.org/html/2510.01499).
4. [PGED, version 5](https://arxiv.org/html/2410.12869v5).
5. [Minority Sentinel](https://arxiv.org/html/2606.29270).
6. [Coppersmith–Fleischer–Rudra primary paper](https://cse.buffalo.edu/faculty/atri/papers/algos/CFR06.pdf).
7. [When Do Noisy Votes Reveal the Truth?](https://doi.org/10.1145/2892565).
8. [Agreement Overstates Evidence: abstract and metadata](https://arxiv.org/abs/2609.22512).
9. [EJOR editorial policy](https://www.euro-online.org/web/pages/518/european-journal-of-operational-research-ejor).
10. [EJOR author guide](https://www.sciencedirect.com/journal/european-journal-of-operational-research/publish/guide-for-authors).
