# Submission files and reproducibility

Status: local working revision, 10 November 2026. Internal packaging guide;
not part of the journal manuscript.

## Authoritative files

| Purpose | Editable source | Deliverable |
|---|---|---|
| Main article | `manuscript/main.tex`, `refs.bib`, generated macro files | `manuscript/main.pdf` |
| Online supplement | `manuscript/supplement.tex`, `supplement_body.tex` | `manuscript/supplement.pdf` |
| Cover letter | `manuscript/Cover_Letter_EJOR.tex` | `manuscript/Cover_Letter_EJOR.pdf` |
| Title/author page | `manuscript/Submission_Title_Page.tex` | `manuscript/Submission_Title_Page.pdf` |
| Highlights | `manuscript/highlights.txt` | Same editable file |
| CRediT roles | `manuscript/Credit_Author_Statement.txt` | Same editable file |
| Competing interests | `manuscript/Declaration_of_Competing_Interest.txt` | Same editable file |
| AI disclosure | `manuscript/Declaration_of_Generative_AI.txt` | Same editable file; also in main article |

The main article uses 11-point type and 1.5 line spacing. The user ceiling is
30 pages including references; EJOR's regular-paper ceiling is 35. Current
build counts and checks: `docs/ejor_repo_audit.json`.

The main article uses `Figure_1_Pipeline.pdf`; the supplement uses the worked
example and order-averaging diagram. Retain their `.tex` sources and generated
data. `Figure_4_Accuracy.pdf` is a legacy, unused plot, not an additional result.

## Dependencies

- `requirements.txt` lists Python dependencies, not a lockfile. The audit JSON
  records the validation environment, not necessarily the original collection environment.
- TeX needs `pdflatex`, `bibtex`, the requested packages, and **`apalike-ejor.bst`**.
  The style is installed in the audited environment but is not bundled here.
  Check with `kpsewhich apalike-ejor.bst`.
  **Portable source packaging is incomplete until the author supplies this
  style file, with its redistribution terms, in `manuscript/`.** The agent's
  workspace policy denied access to the installed copy; no access restriction
  was bypassed. The local PDF build succeeds, but that is not a clean-machine test.
- `pdfinfo` and `pdftotext` support PDF auditing, not document compilation.

## Full document build

Run from **`manuscript/`**, after any intended table generation. These commands
do not make model calls. Multiple passes resolve cross-document references.

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
bibtex supplement
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error Cover_Letter_EJOR.tex
pdflatex -interaction=nonstopmode -halt-on-error Submission_Title_Page.tex
```

Rebuild figure PDFs when their sources change. Check logs for undefined
citations/references, unresolved cross-references, multiply defined labels and
overfull boxes. A zero exit status alone is not a submission-ready document.

## Offline evidence versus new live runs

`docs/benchmark_results.md` lists all nine table-generation scripts and inputs.
They skip missing tracks and write generated macros; compare their outputs
before accepting any change. Original local GPQA files are required for the
complete tables and are absent from the public archive. Fresh API runs do not
reproduce the original stochastic generations. Only stored-judgment rows support
alternate-weight replay; answer-level fidelity is not candidate-identity fidelity.

Run offline unittest modules excluding `tests/test_providers.py`, which uses
live services. No API credentials are needed for offline checks.

## Release boundary

The v1.0.0 Zenodo DOI and `CITATION.cff` identify an already published software
archive. Local edits do not update that archive, a GitHub release or the remote
repository. A new approved release needs its own version, packaged sources/PDFs,
dependency information and archive record. Update archive citations only after
that record exists; do not relabel old v1.0.0 evidence as a new release.

Historical preregistrations and stored run files retain their original contents.
Internal review, novelty-audit and machine-readable audit files in `docs/` are
not journal attachments. Verify author identity, affiliation, correspondence,
CRediT and AI-use declarations before uploading.

## Journal sources

- [Official EJOR author guide](https://www.sciencedirect.com/journal/european-journal-of-operational-research/publish/guide-for-authors).
- [EJOR editorial policy](https://www.euro-online.org/web/pages/518/european-journal-of-operational-research-ejor).

Packaging does not certify methodological significance or predict acceptance.
The separate scientific assessment is `docs/novelty_audit.md`.
