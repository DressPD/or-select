# Manual EJOR submission checklist

This checklist is for the author; do not upload internal review/audit documents
as manuscript attachments. It is not a scientific acceptance certificate.

## Actions before submitting

1. **Complete the editable-source package.** Supply a redistributable
   `apalike-ejor.bst` in `manuscript/`, with appropriate redistribution terms,
   or arrange the required bibliography dependency in the journal workflow.
   The installed copy compiled locally but is not bundled. Agent access to
   that installed file was denied; the restriction was not bypassed.
   Confirm the actual uploaded source set builds in the submission system.
2. **Check the new Zenodo version.** Look for v1.1.0 under the existing
   [all-versions record](https://doi.org/10.5281/zenodo.24112044). If automatic
   GitHub archiving has not happened, complete the existing record's new-version
   workflow or verify the GitHub–Zenodo integration. Do not create an unrelated
   duplicate record or reuse the v1.0.0 version DOI for v1.1.0.
   The current software citation uses the verified concept DOI plus the exact
   GitHub release URL; the paper separately cites v1.0.0's unchanged original data.
3. **Verify author statements.** Confirm name, affiliation, email, ORCID,
   funding, competing interests, CRediT roles, and the precise AI-use declaration.
   These declarations require the author's confirmation, not an agent's inference.
4. **Read the final rendered files.** Use the new title consistently in the
   submission form, main article, supplement, title page and cover letter.
   Confirm tables, mathematical symbols and cross-document references in the
   PDF the submission system assembles, not only the local PDFs.

## Files and form entries

Title:

> Pairwise Judging versus Voting for Language Model Answer Selection: Finite-Pool Theory and an Empirical Audit

- Article type: **Theory and Methodology**.
- Main article: `manuscript/main.pdf`, with editable `main.tex`, `refs.bib`,
  required macro files, figure sources/assets and bibliography dependency.
- Supplement: `manuscript/supplement.pdf`, with `supplement.tex` and
  `supplement_body.tex` and their referenced source/assets.
- Title/author page: `manuscript/Submission_Title_Page.pdf` and `.tex`.
- Cover letter: `manuscript/Cover_Letter_EJOR.pdf` and `.tex`.
- Highlights: `manuscript/highlights.txt` (five bullets, each within 85 characters).
- Declarations: the three `Credit_Author_Statement.txt`,
  `Declaration_of_Competing_Interest.txt` and `Declaration_of_Generative_AI.txt`
  files, as requested by the upload form.
- Copy the abstract and keywords from the final source; retain the official
  first keyword **Artificial intelligence in OR**.
- Complete any portal-specific originality, exclusive-submission, reviewer,
  data-availability and publication-option questions truthfully. Do not invent
  reviewers, consents, affiliations or funding information.

Keep password-gated GPQA question-containing originals out of public uploads.
Do not upload `docs/ejor_submission_review.md`, novelty/citation audits or other
internal planning notes as submission documents. They remain repository records.

The title/release update does not complete the additional scientific work
identified in the internal review. An author may proceed with the bounded
claims in the current paper, but should not mistake a clean build or release
for assurance that EJOR will judge the methodological contribution sufficient.

Official requirements:
[EJOR Guide for Authors](https://www.sciencedirect.com/journal/european-journal-of-operational-research/publish/guide-for-authors).
