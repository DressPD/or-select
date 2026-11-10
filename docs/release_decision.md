# Release decision after v1.0.0

Decision date: **10 November 2026**. Internal author/release guidance, prepared
before publication. The author subsequently authorized publishing v1.1.0;
execution and final metadata follow `CHANGELOG.md` and the GitHub release.

**Execution confirmed:** v1.1.0 was published on GitHub at
`1ffd6c84e1637f50d6ef6b0168db4288354bc602`, with four matching PDF assets.
Automatic Zenodo archiving produced version DOI
[10.5281/zenodo.24115542](https://doi.org/10.5281/zenodo.24115542), in the existing
concept record. No manual deposit is needed. The post-release metadata commit
records that assigned DOI without modifying the released tag or its archive.
The planning discussion below is retained as provenance; confirmed execution
supersedes its pre-publication uncertainty.

**Subsequent source-package fix:** the missing bibliography style is now bundled,
licensed and verified in isolation; see `docs/source_package_audit.json` and
`submission/ejor-source-package.zip`. The author explicitly selected **push only**,
not a v1.1.1 release. Existing tags and Zenodo records remain unchanged; the
completed bundle belongs to the current repository revision, not the old archive.

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
the new contents. The article retains the real v1.0.0 DOI for its unchanged
original dataset. In the v1.1.0 tag, `CITATION.cff` uses the verified all-versions
concept DOI together with an exact GitHub version/release URL. The post-release
metadata uses the subsequently assigned version DOI. Neither citation
mislabels the v1.0.0 version DOI as v1.1.0 or invents an unpublished DOI.

## Submission/archive follow-up

1. **Completed after v1.1.0:** a redistributable `apalike-ejor.bst` is included
   in the current source bundle. It derives from public CTAN source; the denied
   installed copy was not accessed. Its license notice and modified filename
   are included. The old v1.1.0 archive remains an accurate historical snapshot.
2. Verify author/declaration metadata and the final main/supplement PDFs.
3. Keep GPQA question-containing originals out of the public package; accurately
   distinguish permitted public data from local replay inputs.
4. Finalize release metadata and notes for the new version. Historical
   preregistrations and original run files remain unchanged.
5. The selected citation path for the initial tag uses the already verified
   **concept DOI plus exact GitHub version URL**, while preserving the original
   dataset's v1.0.0 citation. No new DOI is reserved or invented by this workflow.
   For any later version-specific citation, first obtain the real published or
   reserved DOI from the existing Zenodo deposit and verify its version.
6. Tag/release the approved commit and publish the matching archive. If relying
   on GitHub–Zenodo integration instead, confirm the integration's DOI/version
   workflow before publishing; do not assume it creates or updates a record
   automatically. Avoid duplicate deposits and verify that the published DOI,
   version, commit and archived source/PDFs agree. The all-versions concept DOI
   is an alternative citation only when intentionally citing the project across
   versions rather than identifying a particular reproducibility snapshot.

The original request authorized only a push and release decision; the later
request explicitly authorized publishing the new GitHub release. A GitHub
release does not itself prove Zenodo has archived the version. Confirm the
resulting record separately. Packaging and archiving do not certify EJOR
acceptance or scientific priority.
