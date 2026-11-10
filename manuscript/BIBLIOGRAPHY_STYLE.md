# Bundled bibliography style

`apalike-ejor.bst` is a **local adaptation**, not an official EJOR/Elsevier
style or a claim of complete APA conformance. Its filename preserves the
manuscript's existing `\bibliographystyle{apalike-ejor}` interface.

## Source and redistribution

Derived from Oren Patashnik's `apalike.bst`, version 0.99a, 8 December 2010:

https://mirrors.ctan.org/biblio/bibtex/base/apalike.bst

The upstream header grants the following permission:

> Copyright (C) 1988, 2010 Oren Patashnik.
> Unlimited copying and redistribution of this file are permitted as long as
> it is unmodified. Modifications (and redistribution of modified versions)
> are also permitted, but only if the resulting file is renamed.

This modified version is renamed **`apalike-ejor.bst`**. The notice is retained
in the file. The original code and local changes may be redistributed under
that permission; further modified versions must also be renamed. This is a
third-party licensing exception to the repository's general MIT license.

## Local changes

- Ampersand separators in author lists and two-author citation labels.
- Comma-separated article volume/issue and page range.
- Unprefixed proceedings titles and page ranges; proceedings publisher/address
  omitted to retain the existing output; italic, sentence-case miscellaneous titles.
- DOI-first links, falling back to an explicit URL, using `\url`.
- Link/note punctuation matching the manuscript's reference-list conventions.
- Unused abbreviation macros and explanatory comments omitted.

Author/year/title sorting, disambiguation and entry-type handling derive from
`apalike`. The manuscript already loads the URL support required by the style.
No installed custom bibliography style is needed when building this source set.

The existing third-party `elsarticle.cls` and `elsarticle-num-names.bst` retain
their own LaTeX Project Public License notices. They are not relicensed as MIT.
