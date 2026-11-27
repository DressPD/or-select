# Expert Systems with Applications submission check (2026-11-27)

The journal's guide for authors was **not available** to the preparers of this package (ScienceDirect returns HTTP 403
to automated access, and the author has not pasted it). Items below are therefore either generic Elsevier practice,
visible properties of the files, or marked unverified. Paste the live guide to get a requirement-by-requirement check as
was done for Information Fusion and IISE Transactions.

| Item | Status |
|---|---|
| LaTeX with the Elsevier `elsarticle` class; editable sources | Ready: `submission/eswa/eswa-latex-source.zip` rebuilds `main.tex` in a clean directory with no undefined references |
| Abstract | 193 words; confirm the journal's limit |
| Highlights, 3 to 5 bullets of at most 85 characters | Ready: `highlights.txt`, 5 bullets, longest 81 characters (the Elsevier limit used by Information Fusion; confirm for this journal) |
| Keywords | 6 (Decision-level fusion; Large language models; LLM-as-a-judge; Answer selection; Rank aggregation; Self-consistency) |
| Title page with affiliation, address, ORCID and corresponding-author email | Ready: front matter of `main.tex` and `Submission_Title_Page.pdf` |
| CRediT author statement, funding statement, competing-interest declaration, generative-AI declaration | Present in `main.tex`; separate copies in `submission/eswa/` |
| Declaration of generative AI placed before the reference list | Present |
| Data availability | Present; Zenodo archive, GPQA exclusion explained |
| Figures as separate files | Ready: `submission/eswa/figures/` |
| Reference style | Unverified; the build uses an author-year style (`apalike-local.bst`); Elsevier journals usually accept any consistent style at first submission, confirm |
| Length | `main.pdf` is 39 pages in the `elsarticle` preprint format (1.5 spacing); the supplement is separate (12 pages). Confirm any page limit |
| Cover letter | `Cover_Letter.pdf`; no journal-specific questions known |
| Review model | Assumed single-anonymized (Elsevier default); the files carry the author's details. If the guide says double-blind, use the blind build approach in `scripts/make_iise_manuscript.py` as a template |
| Scope | Applications of expert and intelligent systems; the cover letter frames answer selection for language-model systems as the application |

Author actions: paste or read the live guide and fix any mismatch; enter the details in Editorial Manager; keep the
cover letter and title page as separate files if the portal asks for them.
