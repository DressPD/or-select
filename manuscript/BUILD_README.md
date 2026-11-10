# Building the EJOR submission sources

Main entry point: **`main.tex`**. The online supplement entry point is
**`supplement.tex`**. Cover-letter and title-page entry points are
`Cover_Letter_EJOR.tex` and `Submission_Title_Page.tex`.

## Requirements

Use a standard LaTeX installation with pdfLaTeX, BibTeX, and the packages
requested in the source files. The document class and bibliography style
are included locally: `elsarticle.cls` and **`apalike-ejor.bst`**.
No locally installed custom bibliography style, Python, API credentials,
benchmark data or new model calls are required to compile these sources.

The ZIP includes the precomputed numerical macro files and figure PDFs.
The figure `.tex` sources are provided for editing; rebuilding those figures
is not necessary for the document build below.

## Build all documents

Run inside the extracted source directory:

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

Both documents reference each other with the `xr` package. The alternating
passes resolve those references. The upload ZIP also includes generated
`main.aux`, `supplement.aux`, `main.bbl`, and `supplement.bbl` from the verified
build to support portals that compile only one entry point. These generated
files are conveniences, not substitutes for the editable sources: the complete
sequence above was also checked starting without them. After editing labels or
references, rebuild both documents rather than relying on stale generated files.

For the submission portal, select `main.tex` as the main entry point and upload
the supplement separately in the requested category. Inspect the PDF assembled
by the portal. Keep the title page, highlights, cover letter, and declarations
in their requested categories; do not concatenate them into the article.

## Redistribution and scope

See `BIBLIOGRAPHY_STYLE.md` for the upstream source, local modifications and
redistribution permission for `apalike-ejor.bst`. It is a local adaptation,
not an official EJOR style. `elsarticle.cls` and `elsarticle-num-names.bst`
retain their own copyright and LaTeX Project Public License notices.
The included `LICENSE` records the repository's MIT code license. Packaging
does not relicense third-party material or assign a new journal publishing license.

This source package builds the submitted tables from the supplied macro files.
It is not the raw experimental dataset and contains no GPQA question records.
