# IISE Transactions: instructions-for-authors check (2026-11-27)

Checked against the instructions text supplied by the author (page "Updated October 20, 2026"). The page links to a
Pre-submission Checklist, a Post-acceptance Checklist, a Reproducibility Report template and a reference guide; **those four
documents were not available to me**, and the page warns that non-compliant papers may be desk rejected, so read them
before upload.

| Requirement in the instructions | Status |
|---|---|
| Original article, English | Pass |
| Order: title, abstract, keywords, main text with introduction and conclusion, acknowledgments, declaration of interest, references; figures and tables inline | Pass: Figure 1 and all main tables inline; no acknowledgments (blind); data, interest, funding and AI statements precede the references |
| At most about 30 pages, 11 pt, 1 inch margins, single column, 1.5 spacing, including references, tables and figures | Pass: `main_iise.pdf` is 25 pages at 1.5 spacing with the references also at 1.5 |
| 11 pt, 1 inch margins, 1.5 spacing also for appendices | Pass: the supplement uses the same settings (14 pages) |
| No footnotes | Pass: none in either file |
| American spelling | Pass after the check: one British form ("analysing") fixed; a keyword search found no others |
| Double quotation marks | Pass: LaTeX double quotes only |
| Unstructured abstract of 200 words | Pass: 184 words, single paragraph |
| At most 10 keywords | Pass: 6 |
| Double-blind review | Pass: manuscript, supplement and the LaTeX zip contain no author, affiliation, repository or DOI strings (searched in the PDF text, the sources, the bibliography and the `.bbl` files); the author's own archive record is filtered out of the zipped `refs.bib` |
| LaTeX: upload the PDF as "Manuscript - anonymous", plus sources as a single zip marked "LaTeX Source Files" | Ready: `submission/iise/main_iise.pdf` and `iise-latex-source.zip` (22 files; rebuilt from the zip in a clean directory) |
| Author details on a cover page: full names, affiliations, ORCID, corresponding author email | Ready: `Submission_Title_Page.pdf`; upload as the author-details file |
| CRediT roles | Enter in the portal (single author); the text is in `Credit_Author_Statement.txt` |
| Funding details | Pass: statement in the manuscript |
| Disclosure statement | Pass: "no competing interests" statement present; suggested wording is "The authors report there are no competing interests to declare" |
| Generative-AI declaration | Pass: statement describes the tools and the review by the author |
| Biographical note of at most 200 words per author | Pass: short note on the title page |
| Data availability statement with persistent identifier or access route | Partly: the blind manuscript says the identifier is given in the submission form (needed to keep review blind); enter the archive DOI there. Data policy is "share on reasonable request" |
| Figures: 1200 dpi line art; PS, JPEG, TIFF or Word accepted, EPS and PS preferred | Ready: the figures are vector PDFs; EPS copies are in `submission/iise/figures/` |
| Tables editable | Pass |
| SI units | Not applicable |
| Supplemental material is published via Figshare | Optional: `supplement_iise.pdf` is the online supplement |
| Reference style per the T&F reference guide | **Unverified:** the guide was not provided. The build uses `chicago.bst` with natbib, as the IISE LaTeX template does; check against the reference guide |
| Reproducibility Report (template linked) | **Unverified:** not provided; ask whether it is required at submission |
| Scope: strong methodological focus motivated by real problems that impact engineering practice | Risk, see below |

Journal focus (from the instructions): four focused issues: Design and Manufacturing; **Data Science, Quality and
Reliability**; Operations Engineering and Analytics; Supply Chain and Logistics. The most plausible home is Data Science,
Quality and Reliability. The paper's motivation is language-model answer selection, not a classic industrial-engineering
problem; the introduction now draws the analogy with redundant inspection with adjudication on disagreement, but a reviewer
may still ask why this belongs in an industrial-engineering journal.

Author actions: read the four linked documents; enter the archive DOI, CRediT roles and the corresponding author in the
portal; upload the anonymous PDF and the LaTeX zip as separate file types; keep the cover letter and title page out of the
anonymous files.
