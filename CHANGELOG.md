# OR-Select release notes

## v1.1.0 — 10 November 2026

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
  Zenodo concept DOI; the paper's original-dataset citation remains v1.0.0.

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
- The GitHub release is not proof of successful automatic Zenodo archiving.
  Confirm the new version in the existing Zenodo record before citing a new
  version-specific DOI. Do not assign v1.0.0's DOI to v1.1.0.

## v1.0.0 — 10 November 2026

Initial code/data archive. DOI: `10.5281/zenodo.24112045`.
