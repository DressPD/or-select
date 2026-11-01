# Peer review, second pass (2026-11-01, after theory generalization)

Manuscript: `manuscript/main.tex` (EJOR submission). Review format: review-paper skill.

## Summary
The paper formulates best-of-N answer selection as an integer program over a judge-derived pairwise matrix, adds an
exact Kemeny-Young reference, and audits the method against self-consistency on four ground-truth benchmarks with paired
exact tests, a headroom/recovery metric and coverage accounting. The result is negative: with one capable generator the
selector ties plurality voting, with mixed generators it is worse. A pairwise-accuracy threshold theory (exact N=3 formula,
exact values to N=7, correlated wrong answers, pair-dependent judges, a large-N lower bound) explains why a judge near chance
cannot help, and the measured pairwise accuracy is compared with it.

Strengths: honest negative result; exact replay of stored selections; exact reference; paired tests; coverage accounting;
theory that is checkable and checked (enumeration, Monte Carlo, unit tests).

## Major issues
1. **Theory buried in Method (Significant) - fixed.** Section 3.5 carried the main theoretical contribution; it is now its own
   Section 4 with its own results subsection.
2. **Duplicate and partly redundant empirical tables (Significant) - fixed.** Two tables reported overlapping quantities (q-hat and
   thresholds); merged into one with mixed-pair counts, wrong-pair counts and bootstrap intervals.
3. **Overstated measurement scope (Significant) - fixed.** The abstract's "we measure 48-55%" now says on which tracks
   (at least 70 mixed pairs); the limitations now state that replayable rows are not a random sample and that homogeneous tracks
   contain few mixed pairs.
4. **Theory not reflected in Discussion/Conclusion/Limitations (Significant) - fixed.** Added a Discussion paragraph, a conclusion
   sentence and a "Theory scope" limitation (independence, symmetric judge, wrong-answer structure, N<=7, quality-only model).
5. **Incomplete runs (Critical, open).** GPQA, MATH, AIME heterogeneous and GPQA homogeneous coverage is partial; AIME 2025 and
   MMLU-Pro (code ready) have not run. Abstract, introduction, highlights and Section 5 must be regenerated and re-read once the
   runs complete.
6. **Single weak judge (Significant, open by decision).** The judge is a free-tier model with 60.5% RewardBench accuracy; this is
   disclosed prominently. A stronger-judge replication would decide whether the conclusion generalizes.

## Minor issues
1. Paragraph headings printed a double period (elsarticle adds one): fixed everywhere.
2. "Appendix Appendix A" in cross-references: fixed.
3. "Nemotron correct on 77-98%" corrected to 77-99% and pointed at Table 11's floor column.
4. Contributions item and Related Work (ii) now describe the generalized theory, not only N=3.
5. `judge2026_submission.tex` (legacy workshop draft with a stale title) was a dead file: deleted in the repository tidy-up.
6. Declaration of generative-AI use is drafted (`Declaration_of_Generative_AI.txt`) and must be confirmed by the author and inserted.
7. Zenodo DOI still to be created and cited in place of the bare GitHub URL.
8. Two overfull boxes (3.4 pt and 1.9 pt) remain; cosmetic.

## Recommendation
**Major revision before submission, pending the completed runs.** The science and the audit are sound and the theory is now
a coherent contribution; the remaining blockers are data completeness (issue 5) and administrative items (6-7 above).
