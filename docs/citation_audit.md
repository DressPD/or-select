# Citation coverage and source-quality audit

Date: **10 November 2026**. Internal author audit, not a journal attachment.

## Result

The article cites the **closest prior work identified in the online search**:
Best-of-Majority, Best-of-Infinity, Beyond Majority Voting, PGED and Minority
Sentinel, alongside self-consistency, PAIRS, LLM-Blender, trained verifiers,
judge-bias studies and classical ranking/voting theory. The main text explains
the distinctions rather than presenting judge failure or graph aggregation as
new. Search scope and substantive comparisons are in `novelty_audit.md`.

The final main/supplement sources cite **40 unique records**:

- **32 journal or proceedings records**, including the classical methods,
  directly relevant EJOR studies and published ML/NLP methods and benchmarks.
  This includes a specialist evaluation workshop, not only main conferences.
- **5 primary preprints:** Universal Self-Consistency, the original GSM8K/verifier
  report, Landesberg's selection-failure analysis, PGED v5 and Minority Sentinel.
- **3 primary software/data records:** OR-Tools, MathArena and the OR-Select archive.

Counts describe publication types, not a numerical quality score. No missing
BibTeX keys remain. The bibliography library retains unused entries; these do
not appear in the rendered references. Keeping that research library is not an
endorsement or use of every entry.

## Source policy and changes

Use published primary research for established methodological claims. Use
original dataset/software documentation for provenance. A relevant preprint is
not automatically weak, but it is not peer-reviewed evidence; do not suppress
close prior art merely because it is recent or unpublished. The four recent
method/selection preprints are explicitly labeled as preprints. The original
GSM8K report remains the primary benchmark/verifier source.

The final pass:

1. Replaced the generic evaluation-statistics preprint with Fagerland,
   Lydersen and Laake's peer-reviewed matched-pairs/McNemar analysis.
2. Removed a redundant recent correlated-error preprint from the cited text;
   the published ICML 2025 study supports that claim directly.
3. Removed a redundant inference-scaling preprint citation where the published
   ICLR 2025 study provides the needed context.
4. Added the published classical noisy-voting analysis to distinguish ranking
   recovery from the manuscript's two-class correctness calculation.
5. Upgraded five old preprint entries to their verified published versions:
   Lightman et al. (ICLR 2024), Snell et al. (ICLR 2025), Panickssery et al.
   (NeurIPS 2024), Wang et al. (ACL 2024), and Atıl et al. (Eval4NLP 2025).
   Published titles, years and author lists now follow the official records;
   the ACL author list also restores Lingpeng Kong.
6. Completed Kim et al.'s ICML 2025 proceedings metadata. The earlier pass
   already upgraded Di/Komiyama to ICLR 2026 and Ai et al. to ICML 2026/PMLR.

## Online verification record

Official records used for the final upgrades:

- [Lightman et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/aca97732e30bcf1303bc22ac3924fd16-Abstract-Conference.html).
- [Snell et al., ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b623663fd9b874366f3ce019fdfdd44-Abstract-Conference.html).
- [Panickssery et al., NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/7f1f0218e45f5414c79c0679633e47bc-Abstract-Conference.html).
- [Wang et al., ACL 2024](https://aclanthology.org/2024.acl-long.511/).
- [Atıl et al., Eval4NLP 2025](https://aclanthology.org/2025.eval4nlp-1.12/).
- [Kim et al., ICML 2025](https://proceedings.mlr.press/v267/kim25e.html).
- [Fagerland et al., BMC Medical Research Methodology 2013](https://doi.org/10.1186/1471-2288-13-91): official indexed metadata;
  direct publisher/PubMed fetches were restricted, so this pass does not claim
  a newly completed full-text read of that article.

Crossref returned matching title/author/volume/page metadata for the Amodio,
De Bock and De Baets EJOR records. Several other requests returned HTTP 429;
those responses are not successful new verifications. Earlier source checks
and the broader review are recorded separately. No secondary search summary
is cited in the paper in place of its primary source.

## Boundaries

“All relevant papers” cannot be certified by a finite search. These checks cover
identified close alternatives and sources for the retained claims; they are
not an exhaustive systematic review, plagiarism search or proof of priority.
Nor does a prestigious venue guarantee every paper's conclusions. The narrow
finite-pool distinction remains supported by the comparison, not transformed
into a guaranteed EJOR-level contribution by strengthening the bibliography.

`citation_audit.json` records coverage, successful rebuilds, a **30-page main
article**, a **10-page supplement**, no unresolved references/citations or
overfull boxes, 218 passing offline tests, and unchanged hashes for all nine
numerical macro files. No live model calls or new empirical findings were used.
