#!/usr/bin/env python3
"""Package the double-anonymized Expert Systems with Applications submission into submission/eswa/.

    python3 scripts/make_eswa_manuscript.py     # generate main_eswa.tex and supplement_eswa.tex
    (build main_eswa, supplement_eswa, Cover_Letter, Submission_Title_Page with pdflatex/bibtex)
    python3 scripts/package_elsevier.py

The journal follows double anonymized review (its guide for authors), so the package has two folders:
    submission/eswa/anonymous/     files that reviewers may see: main_eswa.pdf, supplement_eswa.pdf, highlights.txt,
                                   figures/, eswa-latex-source.zip (anonymous sources; the author's archive record is
                                   removed from refs.bib)
    submission/eswa/author_files/  Submission_Title_Page.pdf (author details, acknowledgments, competing interests, CRediT),
                                   Cover_Letter.pdf, and the declaration texts
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / "manuscript"
DEST = ROOT / "submission" / "eswa"
ANON = DEST / "anonymous"
AUTH = DEST / "author_files"
for d in (ANON / "figures", AUTH):
    d.mkdir(parents=True, exist_ok=True)

for name in ("main_eswa.pdf", "supplement_eswa.pdf"):
    shutil.copy2(MS / name, ANON / name)
shutil.copy2(MS / "highlights.txt", ANON / "highlights.txt")
for name in ("Submission_Title_Page.pdf", "Cover_Letter.pdf", "Credit_Author_Statement.txt",
             "Declaration_of_Competing_Interest.txt", "Declaration_of_Generative_AI.txt"):
    shutil.copy2(MS / name, AUTH / name)
figures = sorted(MS.glob("Figure_*_*.pdf"))
for fig in figures:
    shutil.copy2(fig, ANON / "figures" / fig.name)


def anonymous_bib(text: str) -> str:
    """Drop the author's own archive entry (uncited in the anonymous text)."""
    entries = text.split("\n@")
    return "\n@".join(e for e in entries if "dressino2026orselect" not in e.split(",", 1)[0])


# supplement_eswa.aux lets a build of main_eswa.tex alone resolve the xr cross-references into the supplement
sources = ["main_eswa.tex", "supplement_eswa.tex", "supplement_body.tex", "refs.bib", "elsarticle.cls", "apalike-local.bst",
           "main_eswa.bbl", "supplement_eswa.bbl", "supplement_eswa.aux"]
sources += [p.name for p in sorted(MS.glob("*_data.tex"))] + [p.name for p in figures]
with zipfile.ZipFile(ANON / "eswa-latex-source.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for name in sources:
        if name == "refs.bib":
            z.writestr(name, anonymous_bib((MS / name).read_text(encoding="utf-8")))
        else:
            z.write(MS / name, name)
print("packaged", len(sources), "anonymous source files and", len(figures), "figures into", DEST)
