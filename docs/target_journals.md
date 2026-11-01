# Target journals (OR / decision-analytics tier), 2026-11-01

Journals only, no conferences. "Source" says where each fact came from; "unverified" means I could not
open a primary source (Elsevier and INFORMS pages returned HTTP 403 to the fetch tool). Re-check every
row on the publisher page before submitting.

| # | Journal | Rank evidence | Fit | Source / status |
|---|---------|---------------|-----|-----------------|
| 1 | **European Journal of Operational Research (EJOR)** | AJG/ABS 2024: 4 (aggregator); Clarivate JIF 2024 rank 14 of 106 in OR & MS (EURO page) | Theory & Methodology / Decision Support / Computational Intelligence headings. ML is not named; papers without "a major new research finding or novel approach" are desk-rejected | EURO page read directly; AJG grade from journalindexes.com (unverified against charteredabs.org) |
| 2 | **INFORMS Journal on Computing (IJOC)** | AJG 2024: 3 per aggregator (conflicts with my recollection of 4; unverified) | Areas include AI-for-Optimization, Data-Driven Optimization and Intelligent Decision Systems, and Data Science & Machine Learning; requires a real computing contribution and OR methodology | Editorial statement summarized via search (page itself 403); code/data policy not read |
| 3 | **INFORMS Journal on Data Science (IJDS)** | New journal, no grade found | Second virtual special issue on GenAI/LLMs (rolling) | Search result only; page 403 |
| 4 | **Management Science** | AJG 4*, FT50, UTD24 (aggregator, library lists) | Needs a managerial/decision-theoretic angle; weak fit for a benchmark audit | Stretch target |
| 5 | **Operations Research** | AJG 4*, FT50, UTD24; has a "Machine Learning and Data Science" crosscutting area | Needs a theory contribution well beyond Theorem 3.1 | Stretch target |
| 6 | Omega; Decision Support Systems; Computers & OR; Annals of OR; JORS; Decision Sciences | Grades not shown by any source I could open | Plausible fallbacks | Unverified |

Not OR but a journal safety net (no conference): TMLR (judges soundness, not novelty; no CORE rank).

## Readiness for EJOR (what the repo has, what is missing)

Present: highlights (5, <=85 chars), cover letter, title page, CRediT statement, reproducible macro-driven tables
(`scripts/create_results_macros.py`, `analyze_selection.py`, `ablation_weights_offline.py`,
`baselines_extra_offline.py`, `judge_threshold_theory.py`), exact Kemeny-Young reference, **Theorem 3.1** (pairwise-accuracy
threshold) with appendix proof and an empirical check against measured judge accuracy.

Missing before submission:
1. Finish the runs (GPQA hetero, AIME/MATH hetero second pass, AIME 2025, MMLU-Pro) and re-run the five scripts.
2. Declaration of generative-AI use (EJOR/Elsevier require it; text left as a TODO at the end of `main.tex`).
3. Zenodo DOI for code and stored outputs.
4. Desk-reject risk: the OR-novelty argument rests on the exact reference, the threshold theorem and the audit. A
   stronger paper would extend the theorem to N>3 and correlated wrong answers.
5. Verify journal rankings and word/page limits on the publisher pages (403 here).
