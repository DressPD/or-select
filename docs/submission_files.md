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
| Complete editable upload bundle | Sources and licensed dependencies in `manuscript/` | `submission/ejor-source-package.zip` |

The main article uses 11-point type and 1.5 line spacing. The user ceiling is
30 pages including references; EJOR's regular-paper ceiling is 35. Current
build counts and checks: `docs/source_package_audit.json` (latest source-package
check), with earlier experimental/reproduction checks in `docs/ejor_repo_audit.json`.

The main article uses `Figure_1_Pipeline.pdf`; the supplement uses the worked
example and order-averaging diagram. Retain their `.tex` sources and generated
data. `Figure_4_Accuracy.pdf` is a legacy, unused plot, not an additional result.

## Dependencies

- `requirements.txt` lists Python dependencies, not a lockfile. The audit JSON
  records the validation environment, not necessarily the original collection environment.
- TeX needs `pdflatex`, `bibtex` and the standard packages requested by the sources.
  **`apalike-ejor.bst` is now bundled**, with its redistribution permission and
  upstream provenance in `manuscript/BIBLIOGRAPHY_STYLE.md`. The local adaptation
  derives from public CTAN `apalike.bst`; the inaccessible installed custom style
  was not read or copied. The main and supplement bibliographies are byte-identical
  to the existing rendered versions (40 and five entries respectively).
- The upload ZIP was built from sources without `.aux`/`.bbl` files, with BibTeX
  search paths restricted to the extracted source directory. A second check
  compiles only the main entry point from the extracted delivery ZIP. Both pass
  without checked build warnings; main/supplement remain 30/10 pages. This tests
  isolation from the custom installed style, not installation of TeX on a blank OS.
- `pdfinfo` and `pdftotext` support PDF auditing, not document compilation.

## Ready-to-upload bundle

Use **`submission/ejor-source-package.zip`** for editable sources. It contains
the entry points, generated numerical macros, figure assets and sources,
class/style files, license notices, build instructions and a SHA-256 manifest.
Cross-reference `.aux` and `.bbl` files from the verified build are included as
portal conveniences, not prerequisites for a full clean build. Select `main.tex`
as the main entry point. See `manuscript/BUILD_README.md` for the pass sequence.

The four PDFs in `submission/` retain the exact bytes of the published PDFs.
The rebuilt source outputs have identical extracted text. No raw benchmark
records, credentials, or internal review notes are in the source ZIP.

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

The v1.0.0 dataset archive and v1.1.0 software/manuscript archive remain unchanged.
`CITATION.cff` identifies the already published v1.1.0 release. The author selected
**push only** for this subsequent source-packaging fix: no v1.1.1 release or new
Zenodo deposit is authorized. The completed bundle is available from the current
repository, not retroactively inside the immutable v1.1.0 Zenodo ZIP. Do not
relabel that old archive or move its tag. A later approved release would need a
new version and verified archive record before changing version-specific citations.

Historical preregistrations and stored run files retain their original contents.
Internal review, novelty-audit and machine-readable audit files in `docs/` are
not journal attachments. Verify author identity, affiliation, correspondence,
CRediT and AI-use declarations before uploading.

## Journal sources

- [Official EJOR author guide](https://www.sciencedirect.com/journal/european-journal-of-operational-research/publish/guide-for-authors).
- [EJOR editorial policy](https://www.euro-online.org/web/pages/518/european-journal-of-operational-research-ejor).

Packaging does not certify methodological significance or predict acceptance.
The separate scientific assessment is `docs/novelty_audit.md`.
