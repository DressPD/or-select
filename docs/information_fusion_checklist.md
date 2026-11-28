# Information Fusion: guide-for-authors check (2026-11-28)

Checked against the aims and scope and the guide for authors supplied by the author (page shows CiteScore 26.7 and
Impact Factor 17.4). Linked policies (Elsevier GenAI policies, research data policy, LaTeX template) were not read.
Numbers marked generated come from `scripts/package_infofusion.py` (`submission/information_fusion/SUBMISSION_CHECKLIST.md`).

| Requirement | Status |
|---|---|
| Research article, 10 to 35 pages including figures, tables, references; at most 50 references | Pass (generated): 33 pages in the `elsarticle` preprint layout, 49 references. Selector internals, ablations and the Kemeny reference moved to the supplement |
| Single anonymized review: author block allowed in the manuscript | Pass: author, affiliation, corresponding email and ORCID in `main.tex` |
| LaTeX source files required, PDF alone not accepted; template | Pass: `elsarticle` class; sources in `source/` and `informationfusion-latex-source.zip`, rebuilt in a clean directory with no undefined references. The official journal template was not downloaded; the class is the Elsevier one |
| Abstract at most 250 words, stand-alone | Pass (about 246 words) |
| 1 to 7 keywords, no multiword "and/of" keywords | Pass: 6 keywords |
| Highlights: separate file with "highlights" in name, 3 to 5 bullets, at most 85 characters | Pass: `highlights.txt`, 5 bullets, longest 73 characters |
| Numbered sections, abstract unnumbered | Pass |
| Tables as editable text, captions, no vertical rules, used sparingly | Pass for form; 13 tables including generated ones, some overlap in numbers |
| Figures as separate files with captions | Pass: `figures/` (vector PDF) |
| Appendices lettered A, B | Not applicable as built: proofs and extra tables are an online supplement (S-numbering), cited in the text |
| References numbered in order of appearance, in square brackets; LTWA journal abbreviations; DOIs | Pass: `elsarticle-num-names.bst` with numeric citations; journal names abbreviated; DOIs where available. Order of appearance depends on the style's sorting and was not hand-checked |
| Research data, Option C: deposit and give the link, or explain | Ready: data availability section; enter the archive DOI in the form |
| Funding statement standard wording | Pass |
| Declaration of generative AI use, new section before references | Pass |
| CRediT roles (corresponding author) | Pass: in the manuscript |
| Competing interests; declarations tool always completed | Text ready in `declarations/`; **author action:** complete the Elsevier tool and upload the Word document |
| Acknowledgements only in a separate section before references, not on the title page | Pass: none to declare |
| Cover letter answering the seven required questions, concise, fit with scope, novelty | Pass: `Cover_Letter.pdf`. Answer 1 states plainly that universal self-consistency and trained verifiers were not compared |
| Graphical abstract (encouraged): at least 1328 px wide, longest side horizontal, readable at 13 cm | Done: `Graphical_Abstract.pdf` (vector, about 20 cm wide, generated from the same data macros as the paper) |
| References: real, existing sources; DOIs; preprints marked | Checked 2026-11-28: every DOI entry compared with Crossref (title, year, volume, pages, first author; no real mismatches), eight arXiv identifiers compared with arXiv, the Zenodo archive title corrected to its record. About 20 conference-paper entries have no DOI and were not checked against the proceedings |
| Inclusive language; British or American English, not both | Pass after the earlier spelling check |

Reviewer risks (not guide items): the audit uses one free-tier judge and exact ties are rare; no trained-verifier or
LLM-Blender baseline; universal self-consistency was run (`scripts/usc_baseline.py`, 538 problems, same judge: ties
plurality in homogeneous pools, worse in heterogeneous pools, strong position bias) with the free judge; two paid small
judges (Claude Haiku 5.5, GPT Luna; `scripts/strong_judges.py`, about $2.1 spent) also do not beat voting, with partial
coverage (Haiku: 151 homogeneous pools pairwise, many truncated replies; Luna: all 334 homogeneous pools, 34 sampled
heterogeneous pools, universal self-consistency on all 538); no frontier-scale judge was tested.
