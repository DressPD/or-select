# Release decision after v1.0.0

Decision date: **10 November 2026**. Internal author/release guidance.

## Decision: archive a new version before submission

**Yes — a new GitHub/Zenodo version is warranted. Recommend `v1.1.0`.**
This is a manuscript/documentation release with no selection-API or experimental
data change. The minor-version recommendation reflects the substantial new
scientific-artifact organization and interpretation, rather than a code feature.

The existing GitHub release is
[v1.0.0](https://github.com/DressPD/or-select/releases/tag/v1.0.0), published
10 November 2026 at 14:25:35 UTC. Its tag points to
`c2e80d4033555445fd03018620a4868a91bfc07c`. Before the present commit, master
already contained four later commits. The pending revision adds substantially
more changes than a typographical correction:

- Restructured 30-page main article and a separate online supplement.
- Explicit theorem independence and tie-breaking assumptions; compact proof,
  explicit break-even root and finite-pool interpretation.
- Removal of universal operational-threshold and “overturns” claims; soft
  preference scores no longer stand in for Bernoulli comparison accuracy.
- Corrected approximation, integerization and answer-level replay scope.
- Updated diagrams, submission files, prior-art discussion and bibliography.
- Synchronized repository explanations and machine-readable offline evidence.

Publishing from master alone does not update a GitHub release or a Zenodo ZIP.
Readers otherwise receive a materially different article from the cited archive.

## Preserve the existing record

The verified Zenodo v1.0.0 record is
[10.5281/zenodo.24112045](https://doi.org/10.5281/zenodo.24112045).
Its uploaded file is `DressPD/or-select-v1.0.0.zip` (2,290,363 bytes).
The verified all-versions concept DOI is
[10.5281/zenodo.24112044](https://doi.org/10.5281/zenodo.24112044).

Do not move the old tag, overwrite its archive or assign its version DOI to
the new contents. `CITATION.cff` and the article currently retain the real,
published v1.0.0 DOI; no unpublished v1.1.0 DOI has been invented.

## Before creating v1.1.0

1. Include a redistributable `apalike-ejor.bst` in the source bundle, or otherwise
   supply an author-approved portable bibliography dependency. The existing
   local installation compiled successfully, but the file is unbundled and
   agent access to the installed copy was denied.
2. Verify author/declaration metadata and the final main/supplement PDFs.
3. Keep GPQA question-containing originals out of the public package; accurately
   distinguish permitted public data from local replay inputs.
4. Finalize release metadata and notes for the new version. Historical
   preregistrations and original run files remain unchanged.
5. Prefer opening a **new-version draft on the existing Zenodo deposit** and
   reserving its real version DOI before tagging. With that reserved DOI,
   update `CITATION.cff`, the dataset reference and cover letter, rebuild and
   commit the final source/PDF set. Never invent or predict the DOI.
6. Tag/release the approved commit and publish the matching archive. If relying
   on GitHub–Zenodo integration instead, confirm the integration's DOI/version
   workflow before publishing; do not assume it creates or updates a record
   automatically. Avoid duplicate deposits and verify that the published DOI,
   version, commit and archived source/PDFs agree. The all-versions concept DOI
   is an alternative citation only when intentionally citing the project across
   versions rather than identifying a particular reproducibility snapshot.

This request authorized pushing the repository and deciding whether another
release is needed. It did not ask to publish a new release. No new release or
Zenodo deposit was created by this decision document. Packaging and archiving
do not certify EJOR acceptance or scientific priority.
