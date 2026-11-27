# Information Fusion guide-for-authors check (2026-11-27)

Checked against the guide text supplied by the author (not fetched; ScienceDirect refuses automated access).
Re-read the live guide before upload, since requirements can change.

| Requirement | Status |
|---|---|
| Research article, 10-35 pages including references and appendices | Pass: `main.pdf` is 32 pages (elsarticle preprint format); supplement (10 pages) is separate supplementary material |
| Maximum 50 references | Pass: 49 entries in `main.bbl` (one slot left; do not add more without removing one) |
| Abstract at most 250 words, no citations | Pass: about 168 words, no citations |
| 1-7 keywords | Pass: 6 |
| Highlights: 3-5 bullets, 85 characters max, separate editable file with "highlights" in the name | Pass: `manuscript/highlights.txt`, 5 bullets, longest 79 characters |
| Numbered references in order of appearance, numbers in square brackets | Pass: `number,sort&compress` with `elsarticle-num-names.bst` (numeric, names available for in-text author mentions) |
| Journal names abbreviated per LTWA, DOIs where available | Done for journal fields in `refs.bib`; conference proceedings titles are not abbreviated; check DOIs for entries that have one |
| LaTeX template and editable sources at submission; PDF alone not accepted | Pass: Elsevier `elsarticle`; upload all `.tex`, figures, macro files and the `.bst` (see `manuscript/BUILD_README.md`) |
| Numbered sections and subsections, abstract unnumbered | Pass |
| Funding statement in the standard sentence | Pass |
| Generative-AI declaration in its own section before the reference list | Pass |
| CRediT author statement | Pass |
| Competing-interests declaration | Section in manuscript; **author action:** also complete the portal declarations tool and upload the generated Word file |
| Research data: Option C (deposit in a repository, link at submission, or explain why not) | Pass: Zenodo archive; the GPQA exclusion is explained in the data-availability section |
| Figures as separate files with captions | Pass: `Figure_1..4_*.pdf` plus captions in the text |
| Tables as editable text, no vertical rules or shading | Pass (checked: no `\hline` or vertical rules) |
| Title page with affiliation, full address and corresponding-author email | Pass (front matter and `Submission_Title_Page.tex`) |
| Cover letter answering the 7 mandatory questions | Pass: `manuscript/Cover_Letter.tex` (state of the art with 5 references, datasets, validation measures, main claim and significance, evidence, related work, prior publication) |
| Graphical abstract | Optional ("encouraged"); not produced |
| Single anonymized review | No anonymization needed |

Open risks, not formatting:
- Scope: the journal emphasizes architectures, algorithms and applications of fusion. The paper's contribution is theory plus an audit with a null result on one weak judge.
- A stronger-judge run (paid, needs author approval) would improve the evidence section.
