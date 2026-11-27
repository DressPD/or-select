# IISE Transactions submission check (2026-11-27)

Sources: the Overleaf "A Template for IISE Transactions" text (IISE Senior Editors, about four years old) and a search
snippet of the 2021 pre-submission checklist. The checklist PDF and the Taylor & Francis instructions page returned HTTP 403
to automated access, so none of this is confirmed against the live instructions. **Re-read them before upload.**

| Requirement (as found) | Status |
|---|---|
| About 30 pages maximum, title page to references | Pass: `main_iise.pdf` is 25 pages |
| 11 pt, 1 inch margins, 1.5/double spacing | Pass: article class, `geometry` 1in, `setstretch{1.5}` (template says 1.5; checklist text says double: confirm) |
| Abstract: single paragraph, snippet says at most 200 words | Pass: 184 words |
| Keywords after the abstract | Pass: 6 keywords |
| Double-blind: blind manuscript without author information | Pass: no author, affiliation, DOI or repository strings (checked in the PDF text of the manuscript and the supplement) |
| No footnotes; figures and tables inline | Pass: tables and Figure 1 inline; the other figures are in the supplement |
| Order: title, abstract, keywords, text, acknowledgments, declaration of interest, references, appendices | Pass; no acknowledgments section (blind) |
| Appendices as supplemental online material | Pass: `supplement_iise.pdf` (12 pages), also blind |
| natbib author-year (template uses `chicago`) | Partly: `chicago.bst` is not available here; uses the repo's `apalike-local.bst` author-year style. Confirm the required style |
| Cover letter | `manuscript/Cover_Letter.tex`; no specific questions were found for this journal |
| Title page with author details (separate from blind file) | `manuscript/Submission_Title_Page.tex` |
| Data availability, generative-AI statement | Present in the blind manuscript; requirements for this journal not found, but Taylor & Francis policy asks for AI-use disclosure |

Author actions: pick the correct department (likely Data Analytics and Machine Learning, or Operations Engineering and
Analytics) after reading the department statements; prepare an anonymized archive; remove the GitHub URL and Zenodo DOI
from anything uploaded; decide on the paid stronger-judge run.
