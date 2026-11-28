# OR-Select release notes

## Unreleased

- Theory: Bayes-optimal posterior-odds gate for consulting a judge under colliding wrong answers, with a closed-form
  vote-margin threshold, and exact sequential (optimal-stopping) judging (`scripts/bayes_gate.py`,
  `tests/test_bayes_gate.py`, manuscript Section 5.5, supplement proofs); two classical sequential-analysis references.
  Posterior formula checked against exhaustive enumeration (N up to 7). Not in the v1.2.0 archive; cut a new release
  before relying on the archive for these results.

## v1.2.0 — 28 November 2026

GitHub: https://github.com/DressPD/or-select/releases/tag/v1.2.0

Retitled paper ("Vote First, Judge on Ties"), new results and the Information Fusion submission package.

### Added

- Theory and scripts: vote-first (judge on ties) optimality (`scripts/hybrid_rule.py`), difficulty-mixture threshold
  (`scripts/difficulty_mixture.py`), collision model with margin-gated judging and required judge accuracy
  (`scripts/collision_model.py`), with tests.
- Baselines on stored pools: universal self-consistency with the free judge (`scripts/usc_baseline.py`,
  `outputs/usc_baseline.json`, 538 problems); pairwise judging and universal self-consistency with Claude Haiku 5.5 and
  GPT Luna (`scripts/strong_judges.py`, `outputs/strong_judge_*.json`, about $2.1 spent, partial coverage).
- Information Fusion package builder (`scripts/package_infofusion.py`) and `submission/information_fusion/`
  (manuscript, supplement, cover letter with the journal's seven answers, graphical abstract, highlights, declarations,
  LaTeX source zip, generated checklist); guide check in `docs/information_fusion_checklist.md`.
- Offline provider tests updated for the current openai SDK (226 offline tests pass).

### Changed

- Manuscript retargeted to Information Fusion (numeric references, 31 pages, 47 references); selector internals,
  ablations and the Kemeny reference moved to the online supplement; 24 uncited bibliography entries removed;
  archive reference corrected to its Zenodo title.
- Earlier ESWA, IISE Transactions and TMLR packages and builders removed (still in git history).

## Earlier — source-package completion

- Bundle a redistributable `apalike-local.bst` derived from public CTAN source,
  with retained permission, renamed file and documented changes. The installed
  custom file was not accessed. Bibliographies remain byte-identical.
- Add `submission/ejor-source-package.zip`, license notices, build instructions,
  cross-reference conveniences and manifest. No benchmark inputs or credentials
  enter the bundle. Initial packaging retained exact published PDF bytes.
- Apply the subsequent portal instruction: initial LaTeX submission uses a PDF,
  with sources retained for revision. Move Funding above the AI disclosure so
  that it immediately precedes References; refresh the main PDF and source ZIP.
  Scientific content and the three other published PDFs remain unchanged.
- Verify a source build without preexisting `.aux`/`.bbl` files and an extracted
  ZIP main-entry-point build with custom installed-style search disabled.
  Main/supplement remain 30/10 pages; 218 offline tests pass; all nine numerical
  macro hashes are unchanged. See `docs/source_package_audit.json`.
- Author selected **push only**. No new release or Zenodo record; existing
  v1.0.0/v1.1.0 tags and archives remain unchanged. The v1.1.0 packaging limitation
  described below is historical and does not apply to the current source bundle.

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
- TeX compilation requires `apalike-local.bst`, installed in the validation
  environment but not bundled. See the submission checklist before uploading
  an editable source package.
- Automatic Zenodo archiving is verified: record `24115542`, version `1.1.0`,
  file `DressPD/or-select-v1.1.0.zip` (2,544,706 bytes). The v1.0.0 record and
  DOI remain unchanged.

## v1.0.0 — 10 November 2026

Initial code/data archive. DOI: `10.5281/zenodo.24112045`.
