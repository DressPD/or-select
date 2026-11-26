# Venue decision after the EJOR desk rejection (2026-11-27)

EJOR-D-26-05411 was desk-rejected for insufficient contribution to Theory & Methodology of OR;
the editor suggested an ML venue (ICLR). Decision: **submit to TMLR**.

## Why TMLR
- Acceptance rests on whether claims are supported by evidence, not on novelty
  (<https://www.jmlr.org/tmlr/acceptance-criteria.html>); a null-result audit with exact paired tests fits.
- Closest prior work sits in ML venues: JETTS (ICML 2025), provable scaling laws for knockout
  selection (NeurIPS 2025), calibrated judge aggregation (arXiv 2512.03019).
- Rolling submission (about 9 weeks to a decision), no fees; main text fits the 12-page guidance.
- Does not depend on the paid Decision-1 judge test.

## Ranking caveat (verified 2026-11-27, VHB Rating 2024 area lists)
EJOR A, INFORMS J. Computing A, Management Science A+, Operations Research A+, Decision Support Systems B,
Omega B, Computers & OR B, JORS B. TMLR and INFORMS J. Data Science have no verified ranking.
ABS/AJG grades were not verified. If an A-ranked outlet is mandatory, INFORMS J. Computing needs an added
optimisation/computing contribution first.

## Alternatives, in order
1. INFORMS J. Data Science, second GenAI/LLM special issue (deadline 2027-03-01 per the journal's calls page; read the call text first).
2. INFORMS J. Computing, after strengthening the optimisation content.
3. ICML 2027 (full papers 2027-01-22 per secondary listings; unconfirmed on the official call).

TMLR and a journal or conference must not be submitted in parallel (dual submission).

## Build
`python3 scripts/make_tmlr_manuscript.py` regenerates `manuscript/main_tmlr.tex` from `main.tex` and
`supplement_body.tex`; then `pdflatex`, `bibtex`, `pdflatex` x2 on `main_tmlr.tex`. The build uses
`tmlr.sty` and `tmlr.bst` (TMLR style files, github.com/JmlrOrg/tmlr-style-file).

## Before submitting on OpenReview (author actions)
- Upload `submission/tmlr/main_tmlr.pdf` (anonymous) and the anonymized code/data archive; remove the
  GitHub URL and Zenodo DOI from anything uploaded.
- Suggest action editors and reviewers; declare no conflicts that you do not have.
- Camera-ready only: restore the author block, the public archive DOI, funding and AI-use statements.
