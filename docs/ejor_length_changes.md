# Manuscript length and contribution clarification

**Current checked revision: 30 main-manuscript pages including references; 10 supplementary pages.** Main text remains 11-point with 1.5 line spacing. The restoration and initial repo audit produced 29 pages. The final citation audit upgraded published references and added classical noisy-voting context; the rebuilt bibliography brings the article to exactly the requested 30-page ceiling. All builds succeeded, with no unresolved references/citations or overfull boxes. Latest evidence: `docs/citation_audit.json` and `docs/ejor_repo_audit.json`; online literature comparison: `docs/novelty_audit.md`.

## Why 41 pages became 23

The original main manuscript occupied **35 pages at line spread 1.24**, or **41 pages when rebuilt at 1.5 spacing**. The first editorial revision occupied **23 pages at 1.5 spacing**, including references. Thus 41 and 23 are comparable layout measurements; the reduction did not use a smaller font or tighter spacing.

The first revision was too aggressive for a request to stay within 30 pages. It combined removal of repetition, relocation of secondary material, substantial compression of explanatory prose, and a shorter bibliography after peripheral citations were removed. The page reduction cannot honestly be apportioned into exact page counts for each edit: figures, tables, references and page breaks reflow together.

## What changed in the first revision

| Original material | Treatment in the 23-page revision | Scientific content |
|---|---|---|
| Five-item contribution list, Introduction outcome, Discussion outcome, conclusion summaries | Combined and shortened; use case moved to Introduction | Repeated claims removed, principal contributions retained |
| Four extended Related Work paragraphs | Reduced to three compact paragraphs | Core citations retained; contextual discussion and peripheral citations reduced |
| Stage-by-stage pipeline description | Condensed around the diagram and score definitions | Generation, comparison, confidence, consistency, cost and selection retained |
| One-hot selection and exact Kemeny formulations | Retained with shorter explanation | Objectives and constraints retained; implementation precision clarified |
| Three-candidate threshold theorem and appendix proof | Kept theorem; replaced long appendix proof with a compact proof beside it | Result and proof retained |
| Elementary cost-dominance lemma | Removed | Replaced by the direct objective-scale explanation and measured ablation evidence |
| General finite-pool, pair-dependent and wrong-answer-collision analysis | Reduced to a brief main-text summary; detailed analysis kept in supplement | Results and derivations retained in submission package |
| RewardBench category table | Moved from main text to supplement | Measurements retained |
| Generator-share and selection table | Moved from main text to supplement | Measurements retained |
| Empirical soft-score/model-threshold table | Moved to supplement and relabeled as descriptive sensitivity analysis | Measurements retained; unsupported substitution of soft scores for binary accuracy removed |
| Accuracy plot duplicating the track accuracy table | Removed from main text | Same numerical results retained in table; figure source not deleted |
| Track-by-track narration of tables | Condensed | Accuracy, paired discordances and recovery tables retained |
| Objective diagnosis, generator preferences and weight ablations | Combined into one main-text subsection | Ablation table retained; secondary diagnostics retained in supplement |
| Extra selectors, coverage and higher-cap rescues | Brief main-text interpretation; detailed supplementary tables retained | Results retained |
| Three-question open-ended pilot | Removed from main-text narrative; retained in supplement | Pilot observations retained; no ground-truth accuracy claim |
| Discussion and conclusion | Substantially shortened | Main interpretation and scope retained; repetitive summaries removed |
| Bibliography | Rebuilt from citations actually retained | Some peripheral references disappeared with the removed contextual prose |

No benchmark rows, saved model outputs, numerical result macros, selection implementation or experimental results were deleted. The first revision was not an 18-page loss of experimental evidence; it was an unusually large reduction in exposition plus relocation and reflow.

## Restoration after author feedback

The follow-up restores explanatory depth while retaining the **30-page ceiling**. It restores the operational decision context, a fuller comparison with close prior work, explanation of the score components and optimization reference, and additional interpretation of the finite-pool analysis. The general finite-pool threshold table and RewardBench category table return to the main text rather than remaining supplementary. The main text also gives the explicit break-even root, a numerical gain example and the finite-pool accuracy calculations, making the theorem easier to use without following supplementary derivations. It does not restore repeated abstracts of the results or the duplicate accuracy plot. The restoration-stage build is recorded in `docs/ejor_shortening_evidence.json`; the subsequent citation-finalization build is in `docs/citation_audit.json`.

## What the novelty comment means

The review did **not** establish that the exact finite-pool binary-Copeland condition has already been published. It identified established ingredients and overlapping questions:

| Prior contribution | Relationship to this manuscript |
|---|---|
| Kemeny--Young ranking and integer-programming formulations | Established reference machinery, not a new algorithmic claim here |
| Weighted-win ranking's 5-approximation | An inherited guarantee for the full disagreement ranking, not a new correctness theorem |
| Pairwise LLM judging and answer selection | Established approaches; combining them alone does not establish methodological novelty |
| Komiyama et al., *Best-of-Infinity* | Already compares selectors and reports cases where voting beats judges; that negative phenomenon is not new by itself |
| Di et al., *Best-of-Majority* | Studies reward/frequency selection and minimax inference-scaling performance rather than this exact finite binary tournament calculation |
| Ai et al., *Beyond Majority Voting* | Uses higher-order information for heterogeneous, correlated aggregation; relevant context rather than evidence of an identical theorem |

The manuscript's specific theoretical contribution is the exact finite-pool comparison, its explicit assumptions and extensions. The audit adds fixed-pool evaluation, an exact ranking reference and stored-output diagnostics. Whether this combination is sufficiently substantial for EJOR is an editorial judgment, not a finding of duplication. The review does not certify priority over all possible prior literature.

## Submission text versus internal review

Internal assessment and action items belong in `docs/ejor_submission_review.md`, not in the manuscript, supplement, highlights or cover letter. The revised submission should state its contributions positively and report completed methods and results, without an internal checklist about novelty, extra intervals, grading checks or replay work.

This separation does not remove factual qualifications: the tested judge configuration, assumptions of the theorem, answer-extraction method, sampling design and actual data-access conditions still need accurate descriptions. No additional experiment or validation is represented as completed merely by removing a review TODO.
