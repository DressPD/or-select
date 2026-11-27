#!/usr/bin/env python3
"""Package the Elsevier-format submission (Expert Systems with Applications) into submission/eswa/.

    (build main, supplement, Cover_Letter and Submission_Title_Page with pdflatex/bibtex as in manuscript/BUILD_README.md)
    python3 scripts/package_elsevier.py

Single-anonymized review is assumed (the author's details stay in the files). Writes:
    submission/eswa/{main,supplement,Cover_Letter,Submission_Title_Page}.pdf
    submission/eswa/{highlights.txt, Credit_Author_Statement.txt, Declaration_*.txt}   separate text files Elsevier journals ask for
    submission/eswa/figures/Figure_*.pdf                                              figures as separate files
    submission/eswa/eswa-latex-source.zip                                             editable sources (elsarticle class included)
The journal's own guide for authors was not available to this repository's authors; see docs/eswa_checklist.md.
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / "manuscript"
DEST = ROOT / "submission" / "eswa"
(DEST / "figures").mkdir(parents=True, exist_ok=True)

for name in ("main.pdf", "supplement.pdf", "Cover_Letter.pdf", "Submission_Title_Page.pdf"):
    shutil.copy2(MS / name, DEST / name)
for name in ("highlights.txt", "Credit_Author_Statement.txt", "Declaration_of_Competing_Interest.txt", "Declaration_of_Generative_AI.txt"):
    shutil.copy2(MS / name, DEST / name)
figures = sorted(MS.glob("Figure_*_*.pdf"))
for fig in figures:
    shutil.copy2(fig, DEST / "figures" / fig.name)

# supplement.aux lets a build of main.tex alone resolve the xr cross-references into the supplement
sources = ["main.tex", "supplement.tex", "supplement_body.tex", "refs.bib", "elsarticle.cls", "apalike-local.bst",
           "main.bbl", "supplement.bbl", "supplement.aux"]
sources += [p.name for p in sorted(MS.glob("*_data.tex"))] + [p.name for p in figures]
with zipfile.ZipFile(DEST / "eswa-latex-source.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for name in sources:
        z.write(MS / name, name)
print("packaged", len(sources), "source files and", len(figures), "figures into", DEST)
