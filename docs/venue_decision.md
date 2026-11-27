# Venue decision (updated 2026-11-27): Elsevier and Taylor & Francis OR journals

A first submission was desk-rejected for fit and novelty; its journal-specific files were removed (they remain in git
history). The target is restricted to **Elsevier and Taylor & Francis journals**, and the paper was strengthened with two
new results before retargeting (see below). Current target: **IISE Transactions (Taylor & Francis)**.

## Why IISE Transactions
- VHB Rating 2024: **A** (OR area list). It is the best-ranked Elsevier/T&F OR-engineering journal whose scope plausibly
  covers the paper. The journal publishes "papers with a strong methodological focus motivated by real problems that impact
  engineering practice", in four focused issues (Design and Manufacturing; Data Science, Quality and Reliability;
  Operations Engineering and Analytics; Supply Chain and Logistics).
- The paper now has a decision-theoretic result with an actionable rule (vote first, judge only on ties) and a
  difficulty-aware threshold, not only an audit; that serves the "strong methodological focus". It does not by itself supply a
  classic engineering motivation: the introduction draws the analogy with redundant inspection with adjudication, but fit is a
  risk. No LLM-selection paper in IISE Transactions was found (the search tool covers journal archives poorly).
- Requirements: the instructions-for-authors text supplied by the author (updated 2026-10-20), checked in
  `docs/iise_transactions_checklist.md`: about 30 pages including references, 11 pt, 1 inch margins, 1.5 spacing for everything
  including appendices, no footnotes, American spelling, abstract of 200 words, at most 10 keywords, double-blind review,
  LaTeX allowed (anonymous PDF plus one zip of sources), data availability statement, generative-AI declaration, CRediT,
  biographical note. The linked pre-submission checklist, reproducibility-report template and reference guide were not
  available to me and must be read before upload.
- Build status: `main_iise.pdf` is 25 pages, abstract 184 words, no identifying strings; supplement 14 pages;
  `submission/iise/iise-latex-source.zip` rebuilds in a clean directory.

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
