# Venue decision (updated 2026-11-28): Information Fusion

A first submission (EJOR) was desk-rejected for fit and novelty; its journal-specific files were removed (they remain in
git history), as were the later ESWA, IISE Transactions and TMLR builds. Publication cannot be guaranteed anywhere.

## Decision

**Information Fusion (Elsevier)**, restricted by the author to Elsevier and Taylor & Francis journals. Reasons: the paper
treats answer selection as decision-level fusion (a free vote and a priced judge); the journal's scope lists decision
fusion, multi-classifier and decision systems, fusion system design and computational-resource optimization, and welcomes
fundamental theoretical analyses; recent LLM-ensemble and LLM-judge papers appear there; the guide is verified
(`docs/information_fusion_checklist.md`). Reported impact factor 17.4 and CiteScore 26.7 (journal page); no VHB entry;
ABS and JCR were not accessible.

Earlier recommendations withdrawn: Expert Systems with Applications (the paper evaluates no application domain),
IISE Transactions (no language-model precedent, weak scope fit), TMLR (no verified A ranking; also outside the author's
publisher restriction).

## Alternatives, in order

1. Pattern Recognition (Elsevier): closest methods audience (classifier combination, voting, crowdsourcing); guide not read.
2. Operations Research Letters or Mathematical Social Sciences (Elsevier), theory-only cut.
3. Artificial Intelligence (Elsevier): stretch, very selective.
Outside the restriction: TMLR, JAIR, Machine Learning; Annals of OR and Social Choice and Welfare for a theory-only version.
Do not submit to two venues in parallel.

## Evidence

Second scan (Crossref titles since 2023; counts are lower bounds, JMLR and TMLR could not be measured):

| Journal | Publisher | LLM-titled | LLM + vote/judge terms | Voting/aggregation titles without LLM |
|---|---|---|---|---|
| Social Choice and Welfare | Springer | 0 | 0 | 34 |
| Annals of Operations Research | Springer | 1 | 0 | 30 |
| Pattern Recognition | Elsevier | 22 | 4 | 38 |
| Machine Learning | Springer | 29 | 4 | 13 |
| Journal of Artificial Intelligence Research | AAAI Press | 15 | 2 | 7 |
| Artificial Intelligence | Elsevier | 16 | 0 | 3 |
| Mathematical Social Sciences | Elsevier | 0 | 0 | 11 |
| Operations Research Letters | Elsevier | 0 | 0 | 3 |

First scan (articles since 2024): Information Fusion 31 LLM-titled papers (3 with selection terms), Expert Systems with
Applications 43 (5), Knowledge-Based Systems 42 (5), IISE Transactions 0, EJOR 2 (0).

Information Fusion papers used as anchors (metadata verified through Crossref; read at the level of title and metadata,
not full text): Campagner et al. 2023 (aggregation models), Pan et al. 2020 (multi-classifier fusion), Zoppi and Popov
2025 (confidence ensembles), Yu et al. 2026 (majority voting for crowdsourcing), Monteiro et al. 2023 (classifier-pool
diversity), Birman et al. 2022 (cost-effective ensemble selection), Aledo et al. 2025 (partial-ranking consensus),
Sáenz-Royo and Chiclana 2025 (pairwise versus holistic judgments), Zhou et al. (LLM-judge bias; listed as 2027, volume 139).

## Contributions in the current manuscript (all offline, zero API calls)

- Exact finite-pool break-even judge accuracy; difficulty-mixture effective-odds threshold (`scripts/difficulty_mixture.py`).
- Vote first, judge only on ties: Bayes-optimal in the model, weakly dominates plurality and Copeland
  (`scripts/hybrid_rule.py`); on stored runs it uses 6.7% / 4.3% of the judge comparisons with no detectable accuracy gain.
- Colliding wrong answers (`scripts/collision_model.py`): exact accuracy and judge cost of margin-gated judging; the
  required judge accuracy falls as wrong answers concentrate (0.96, 0.82, 0.57 at p=0.5 for s=0, 0.5, 0.9); stored runs have
  collision share 0.52 and 0.38, judge accuracy on mixed pairs 0.55 and 0.59, required 0.84 to 0.99, which predicts the null result.

## What would raise the odds (not done)

A stronger-judge run on tie-rich problems with at least three judges of different strength (paid, needs approval), a
universal self-consistency baseline (needs new generation), and one real application domain.
