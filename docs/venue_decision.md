# Venue decision (updated 2026-11-27): Elsevier and Taylor & Francis OR journals

A first submission was desk-rejected for fit and novelty; its journal-specific files were removed (they remain in git
history). The target is restricted to **Elsevier and Taylor & Francis journals**, and the paper was strengthened with two
new results before retargeting (see below). Current target: **IISE Transactions (Taylor & Francis)**.

## Why IISE Transactions
- VHB Rating 2024: **A** (OR area list). It is the best-ranked Elsevier/T&F OR-engineering journal whose scope plausibly
  covers the paper: its Data Analytics and Machine Learning department asks for data-driven decision-making, and its scope
  spans industrial engineering, statistics, computer science and OR (journal scope page, search snippet).
- The paper now has a decision-theoretic result with an actionable rule (vote first, judge only on ties) and a
  difficulty-aware threshold, not only an audit. This is a fit argument, not a precedent: no LLM-selection paper in IISE
  Transactions was found (the search tool covers journal archives poorly).
- Requirements used (Overleaf IISE template text plus a 2021 checklist snippet; the checklist PDF itself returned HTTP 403,
  so **re-read the live instructions**): at most about 30 pages from title page to references, 11 pt, 1 inch margins,
  1.5/double spacing, abstract single paragraph (checklist snippet: at most 200 words), double-blind review with a blind
  manuscript, no footnotes, figures and tables inline, appendices as supplemental online material,
  order title, abstract, keywords, text, acknowledgments, declaration of interest, references, appendices;
  natbib author-year (`chicago` in the template; the repo uses its own `apalike-local.bst`).
- Build status: `main_iise.pdf` is 25 pages, abstract about 190 words, no identifying strings; supplement 12 pages.

## Alternatives, in order (Elsevier / Taylor & Francis only)
1. Information Fusion (Elsevier) - best topic fit (decision-level fusion; three related 2026/2023 papers verified through
   Crossref), but not in the VHB catalogue, 35-page / 50-reference limits, and the guide requires seven cover-letter answers.
   Its build is the elsarticle `main.tex` (numeric style needs `elsarticle-num-names.bst`).
2. Operations Research Letters (Elsevier, VHB B) - a theory-only letter (about 8 pages) from the finite-pool results.
3. Computers & Operations Research (Elsevier, VHB B), Decision Support Systems (Elsevier, VHB B), JORS (T&F, VHB B).
4. Discrete Applied Mathematics (Elsevier, VHB A) only for a pure theory paper.

VHB Rating 2024 (OR/IS area lists, verified): EJOR A, INFORMS J. Computing A, IISE Transactions A, Discrete Applied
Mathematics A, Operations Research Letters B, C&OR B, Omega B, JORS B, IJPR B, Decision Support Systems B,
Expert Systems with Applications B. Information Fusion has no VHB entry. ABS/AJG and Clarivate JCR need logins and were
not verified. Do not submit to two venues in parallel.

## New results added in this revision (all offline, zero API calls)
- A (`scripts/difficulty_mixture.py`): with per-problem accuracy p ~ F, the Copeland-minus-plurality gap is
  A(q)m1 - B(q)m2, so the break-even depends on F only through r_F = E[p^2(1-p)] / E[p(1-p)^2]. At mean accuracy 0.8 the
  break-even ranges from 0.706 (kappa=1) to 0.804 (single p). On the homogeneous judged rows (n=130, AIME 2025 and
  MMLU-Pro) the own-k prediction of the Copeland-minus-plurality gap is -2.2 points against -1.3 observed, while the pooled-p
  model predicts -10.3. Plug-in check on small samples; q-hat on MMLU-Pro is below one half.
- B (`scripts/hybrid_rule.py`): vote first, judge only on ties is Bayes-optimal in the model for every N and q >= 1/2 and weakly
  dominates plurality and Copeland (verified by exact enumeration for N=3,4 and in floats for N=5,6; proof in the
  supplement). On stored runs it matches voting (hom. 84.1 vs 84.1, het. 92.0 vs 92.5; discordant 1/1 and 1/2) and beats Copeland-everywhere
  in heterogeneous pools (92.0 vs 85.5; discordant 14/1, p<0.001). Exact vote ties are rare (11 of 164 and 11 of 200 problems),
  so it adds no detectable gain over voting with the tested judge.

## Parked builds
- `manuscript/main_tmlr.tex` (TMLR, double-blind) is kept in sync but TMLR is neither Elsevier nor T&F.
- Three TMLR papers and three Information Fusion papers are cited in the related work (journal references verified on
  arXiv and Crossref respectively; abstracts and metadata only).

## Build
`scripts/make_iise_manuscript.py` generates `manuscript/main_iise.tex` and `supplement_iise.tex` from `main.tex`
and `supplement.tex`; see `manuscript/BUILD_README.md` for the pdfLaTeX/BibTeX sequence.

## Before submitting (author actions)
- Read the live IISE Transactions instructions; confirm length, abstract limit, reference style, the right department, and how
  the supplement and blind files are uploaded. See `docs/iise_transactions_checklist.md`.
- Upload the blind manuscript (`main_iise.pdf`), the blind supplement, the title page with author details, and the cover letter.
- Provide an anonymized code and data archive; remove the GitHub URL and Zenodo DOI from anything uploaded.
- Decide on the paid stronger-judge run; every empirical claim rests on one weak judge.
