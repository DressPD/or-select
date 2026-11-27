# Expert Systems with Applications: guide-for-authors check (2026-11-27)

Checked against the guide text supplied by the author (page shows CiteScore 17.0 and Impact Factor 9.4). The guide links
the Elsevier LaTeX template, GenAI policies and the research-data policy, which were not read.

| Requirement in the guide | Status |
|---|---|
| **Double anonymized review**: title page and anonymized manuscript as separate files; supplementary material also anonymous | Done: `submission/eswa/anonymous/` (manuscript, supplement, sources, figures, highlights) and `submission/eswa/author_files/` (title page, cover letter, declarations). The earlier package wrongly assumed single-anonymized review |
| No author names, affiliations or acknowledgments in the manuscript | Pass: PDF text, sources, bibliography output and supplement contain no author, affiliation, repository or DOI strings; the author's own archive record is removed from the zipped `refs.bib` |
| Title page: title, author given and family names, affiliation with superscript letter and full postal address, corresponding author address and email, acknowledgments, competing-interests declaration | Pass: `Submission_Title_Page.pdf` (acknowledgments: none) |
| Abstract of at most 250 words, stand-alone, no citations | Pass: 218 words |
| 1 to 7 keywords, avoid multiword keywords using "and"/"of", only established abbreviations | Pass: 6 keywords, none using "and"/"of"; "LLM" is established |
| Highlights encouraged: separate editable file with "highlights" in its name, 3 to 5 bullets, at most 85 characters | Pass: `highlights.txt`, 5 bullets, longest 79 characters |
| Numbered sections and subsections, abstract unnumbered, cross-references by number | Pass |
| Tables as editable text, captions, cited in text, no vertical rules; "use tables sparingly" | Partly: 11 tables, no vertical rules. The numbers shown in text and tables overlap in places; consider moving the finite-pool and Beta-threshold tables to the supplement if a reviewer objects |
| Figures as separate files with captions; PDF vector is accepted | Pass: `anonymous/figures/` |
| Appendices lettered A, B with A.1 numbering | Not applicable as built: the proofs and extra tables are an online supplement with S-numbering, cited in the text. If the editor wants appendices in the article, they can be moved and renumbered |
| Supplementary material cited in the text with captions | Pass |
| References in APA 7th edition style, alphabetical then chronological, DOIs where available, preprints marked | Partly: the build uses an author-year style (`apalike-local.bst`) that is APA-like but not an exact APA 7 implementation (for example the ampersand and DOI formatting). Elsevier reformats references at acceptance; adjust entries by hand if a reviewer or editor insists |
| Research data, Option C: deposit in a repository and give the link at submission; explain if not possible | Ready: enter the archive DOI in the submission form; the anonymous manuscript says so and explains the GPQA exclusion |
| Funding statement in the standard wording | Pass |
| Declaration of generative AI in a new section before the references | Pass |
| CRediT roles | On the title page; the guide says "encouraged" |
| Competing-interests declaration; declarations tool always completed | Text on the title page; **author action:** complete the portal tool and upload the Word file it generates |
| LaTeX source files (`.tex`); a PDF is not an acceptable source file | Ready: `eswa-latex-source.zip`, rebuilt in a clean directory |
| American or British English but not both | Pass after the spelling check on the shared sources |
| Inclusive language | Pass |
| No page limit stated | None found in the guide; the anonymous manuscript is 37 pages in the `elsarticle` preprint format |
| Scope: expert and intelligent systems; design, development, testing, implementation and management; practical guidelines | Addressed in the introduction, Section "Design guidelines for system builders" and the cover letter. See the fit assessment in `docs/venue_decision.md`; no application domain from the guide's list is evaluated |

Author actions: complete the declarations tool, upload the anonymous files and the author files as separate items, enter
the archive DOI and CRediT roles in the form, and read the linked Elsevier template and AI policies.
