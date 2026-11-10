# OR-Select release notes

## v1.1.0 — 10 November 2026

GitHub: https://github.com/DressPD/or-select/releases/tag/v1.1.0

Verified Zenodo archive: https://doi.org/10.5281/zenodo.24115542

Manuscript, bibliography and reproducibility-documentation revision.

### Updated

- New manuscript title: **Pairwise Judging versus Voting for Language Model
  Answer Selection: Finite-Pool Theory and an Empirical Audit**.
- Main article reorganized within a 30-page ceiling, with a separate online
  supplement, aligned cover letter, title page, highlights and declarations.
- Explicit finite-pool theorem assumptions, compact proof, break-even root and
  distinction between binary comparison accuracy and empirical soft scores.
- More precise approximation, integerization and answer-level replay claims;
  corrected pipeline/order-averaging diagrams and repository explanations.
- Close prior-art comparisons and published bibliographic metadata.
- Internal citation, novelty, build and offline-verification records.
- Citation metadata identifies v1.1.0 and uses the verified all-versions
  Zenodo concept DOI in the tagged source. A post-release metadata update records
  the subsequently assigned v1.1.0 version DOI. The paper's original-dataset
  citation remains v1.0.0.

### Unchanged

- Selection behavior, recorded experimental runs and all nine numerical macro
  files. No new model calls or stronger-judge experiments were performed.
- Existing v1.0.0 tag and archived files.

### Reproducibility and access

- Offline validation: 218 tests pass; 90 exact theorem settings have zero
  mismatches. Latest title-release build checks are in `docs/release_audit.json`.
- GPQA question-containing originals are not redistributed. Public generated
  tables are present, but complete regeneration needs authorized original inputs.
- TeX compilation requires `apalike-ejor.bst`, installed in the validation
  environment but not bundled. See the submission checklist before uploading
  an editable source package.
- Automatic Zenodo archiving is verified: record `24115542`, version `1.1.0`,
  file `DressPD/or-select-v1.1.0.zip` (2,544,706 bytes). The v1.0.0 record and
  DOI remain unchanged.

## v1.0.0 — 10 November 2026

Initial code/data archive. DOI: `10.5281/zenodo.24112045`.
