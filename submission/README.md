# EJOR upload files

**Editable source ZIP:** [ejor-source-package.zip](ejor-source-package.zip).
Select **`main.tex`** as the main entry point. Its included `BUILD_README.md`
explains the full main/supplement build and cross-reference support files.
`SOURCE_MANIFEST.json` lists included files and SHA-256 hashes.

| File | Upload category |
|---|---|
| `main.pdf` | Main article; 30 pages including references |
| `supplement.pdf` | Online supplement; 10 pages |
| `Cover_Letter_EJOR.pdf` | Cover letter |
| `Submission_Title_Page.pdf` | Title/author page |
| `ejor-source-package.zip` | Editable sources, figures, macros, class and licensed bibliography style |

Highlights and the three author/declaration text files are inside the ZIP and
in `manuscript/` in the repository. Upload them in the portal's requested
categories. Do not concatenate the title page or supplement into the main paper.

Technical validation: `docs/source_package_audit.json` in the repository.
Both isolated clean-source and extracted-ZIP builds pass, without access to the
installed custom bibliography style. Reference lists and extracted PDF text
match the published PDFs. The four PDFs here retain the published file bytes.

No credentials, raw benchmark inputs or internal review documents are in the ZIP.
This is a post-v1.1.0 **push-only** source fix, not a new release or replacement
of the immutable v1.1.0 Zenodo archive.

Remaining author-only steps: confirm author/affiliation/contact details, funding,
competing interests, CRediT and actual AI use; inspect the portal-generated PDF;
complete exclusive-submission/originality and other portal declarations truthfully.
Technical packaging does not guarantee EJOR acceptance.
