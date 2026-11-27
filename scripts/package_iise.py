#!/usr/bin/env python3
"""Package the anonymous IISE Transactions submission files into submission/iise/.

    python3 scripts/make_iise_manuscript.py   # generate main_iise.tex, supplement_iise.tex
    (build both with pdflatex/bibtex as in manuscript/BUILD_README.md)
    python3 scripts/package_iise.py

Writes (the guide asks for LaTeX sources as ONE zip, and prefers EPS figures):
    submission/iise/main_iise.pdf, supplement_iise.pdf      anonymous manuscript and online supplement
    submission/iise/Cover_Letter.pdf, Submission_Title_Page.pdf   author-identifying files, uploaded separately
    submission/iise/iise-latex-source.zip                   anonymous sources only (no author information)
    submission/iise/figures/*.eps                           EPS copies of the vector figures (via pdftops)
"""
from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / "manuscript"
DEST = ROOT / "submission" / "iise"
DEST.mkdir(parents=True, exist_ok=True)

for name in ("main_iise.pdf", "supplement_iise.pdf", "Cover_Letter.pdf", "Submission_Title_Page.pdf"):
    shutil.copy2(MS / name, DEST / name)

figures = sorted(MS.glob("Figure_*_*.pdf"))
(DEST / "figures").mkdir(exist_ok=True)
for fig in figures:
    subprocess.run(["pdftops", "-eps", str(fig), str(DEST / "figures" / (fig.stem + ".eps"))], check=True)

sources = ["main_iise.tex", "supplement_iise.tex", "supplement_body.tex", "refs.bib", "chicago.bst"]
sources += [p.name for p in sorted(MS.glob("*_data.tex"))]
sources += [p.name for p in figures]
sources += ["main_iise.bbl", "supplement_iise.bbl"]


def anonymous_bib(text: str) -> str:
    """Drop the author's own archive entry (uncited in the blind text) so the zip carries no identifying record."""
    entries = text.split("\n@")
    kept = [e for e in entries if "dressino2026orselect" not in e.split(",", 1)[0]]
    return "\n@".join(kept)


with zipfile.ZipFile(DEST / "iise-latex-source.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for name in sources:
        if name == "refs.bib":
            z.writestr(name, anonymous_bib((MS / name).read_text(encoding="utf-8")))
        else:
            z.write(MS / name, name)
print("packaged", len(sources), "source files and", len(figures), "EPS figures into", DEST)
