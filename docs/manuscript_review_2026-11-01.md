# Peer review of the revised manuscript, 2026-11-01

Review workflow: `review-paper` skill (Cambridge/Wiley structure) applied to `manuscript/main.tex`
after the revision described at the end. Results are regenerated from `outputs/` by
`scripts/create_results_macros.py`, `analyze_selection.py`, `ablation_weights_offline.py`.

## Summary

The paper formulates best-of-N answer selection as an integer program over a judge-derived pairwise
matrix plus a deterministic self-consistency term, notes that the Copeland aggregate inherits the
5-approximation of Coppersmith et al. against the Kemeny optimum, and audits the method on GSM8K, MATH
Level 5, AIME 2026 and GPQA Diamond with an exact Kemeny-Young reference, paired exact tests and a
floor/oracle recovery metric. The audit is negative: no benefit over majority vote with one generator, a
significant harm with heterogeneous generators, explained by an objective whose word-count cost term
dominates the judge's quality term (444/480 replayed problems) and by a judge that concentrates picks on
one generator (69.7%).

Strengths: exact replayability (480/480 stored winners reproduced), complete coverage accounting, paired
tests, a diagnostic that separates selector quality from available headroom, honest limitations.
Weaknesses: one weak, free-tier judge/generator model; heterogeneous tracks still incomplete; the
diagnoses are post hoc.

## Major issues

1. **Incomplete heterogeneous coverage** (Table 8). MATH 131/134, AIME 25/30, GPQA 90/198 graded;
   GPQA still has 86 untried and 19 truncated problems. Severity: Critical for submission. The direction
   is clear on GSM8K and MATH, but headline pooled numbers (2 vs 25) will move. Needs the remaining runs,
   then a re-run of the three scripts and a re-read of Sections 5.2-5.5.
2. **Mixed heterogeneous pool.** Laguna-S 2.1 was withdrawn mid-study; 79-131 graded problems per
   heterogeneous track still contain its candidates, newer rows use Xing4.0-29B. Severity: Significant.
   Disclosed in Section 4.1 and Table 8; a clean pool would need reslotting (about 25 free calls per row).
3. **Single judge and generator model.** The judge scores 60.5% on RewardBench, below the pre-registered
   trust band, so conclusions are about a weak judge. Severity: Significant. A stronger judge (paid test,
   needs approval) would show whether the negative result is a property of selection or of this judge.
4. **Post hoc diagnoses.** Weight ablations, pick shares and the length analysis were not pre-registered.
   Severity: Minor-Significant; stated in Limitations, and the pre-registered comparison is primary.
5. **Replay coverage is uneven** (Table 7): MATH homogeneous 25/134, AIME homogeneous 9/30 replayable
   because older rows did not store judge outputs. Severity: Minor; the homogeneous ablation is weak.

## Minor issues

1. Two residual overfull boxes (< 20 pt).
2. The seed non-determinism finding is a single earlier observation (provider and model differ from the
   audit); kept as a clearly labelled pilot note.
3. Track A is three queries without ground truth: kept only as an illustration.
4. Elsevier requires a generative-AI use declaration; not added (author's statement).
5. The repository should be archived (e.g. Zenodo) and cited by DOI, not by GitHub URL.

## Recommendation

**Major revision (before submission):** finish the heterogeneous passes, decide on the mixed pool and on a
stronger-judge replication, then regenerate the numbers. The framing and the analyses are sound for the
current data.

## What changed in this revision

- Rewrote the manuscript around the audit: new title, abstract, introduction, contributions, related work,
  protocol, results, discussion, limitations, conclusion. No claim of superiority; the null/harm results
  are the contribution.
- Replaced every hand-typed result with macros generated from `outputs/`; new tables: paired tests,
  headroom/recovery, generator pick shares, offline weight ablation, coverage, higher-cap second pass.
- Fixed the RewardBench claim: 90.1% belonged to an earlier Nemotron-3-Ultra / reasoning-enabled judge
  configuration; the shipped judge scores 60.5%. Errata added to the pre-registration docs.
- Citations: verified every 2025-2026 reference against arXiv; removed 17 internal `note` fields that
  printed in the bibliography; added GSM8K, MATH, Kemeny 1959, Universal Self-Consistency, "not fair
  evaluators"; corrected how Ding, Kohli and the Borda/Copeland/Kemeny paper are characterised.
- Rebuilt Figure 2 from data; updated highlights, cover letter, title page, credit statement.
