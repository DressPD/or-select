# Venue decision (updated 2026-11-27): Elsevier and Taylor & Francis OR/AI journals

A first submission was desk-rejected for fit and novelty; its journal-specific files were removed (they remain in git
history). The target is restricted to **Elsevier and Taylor & Francis journals**. After comparing past publications,
the current target is **Expert Systems with Applications (Elsevier)**. Publication cannot be guaranteed anywhere; this
ordering maximizes topical fit and precedent, then rating.

## Evidence: recent papers by journal (Crossref scan, titles only, articles since 2024)
`LLM-titled` counts papers whose title names language models; `selection terms` counts those whose title also has
judge, voting, ensemble, aggregation, consensus, self-consistency, best-of, selection, ranking, reward, verification,
preference, pairwise, multi-agent or debate. Counts are lower bounds (Crossref title matching is fuzzy, 30 hits per
query), so read them as relative signals.

| Journal | Publisher | LLM-titled | Selection terms | Closest precedents (titles; metadata checked for the two ESWA papers) |
|---|---|---|---|---|
| **Expert Systems with Applications** | Elsevier | 43 | 5 | LLM-driven group consensus decision-making (2026); LLM-guided maintenance decision-making (2027) |
| Knowledge-Based Systems | Elsevier | 42 | 5 | dynamic adaptive ensemble decoding for LLMs; hybrid prompt ensembles; data voting |
| Engineering Applications of AI | Elsevier | 37 | 3 | ensemble-based transfer testing for LLMs |
| Information Fusion | Elsevier | 31 | 3 | ensemble learning with LLMs for formal verification |
| Applied Soft Computing | Elsevier | 30 | 2 | self-consistency voting framework for physics reasoning |
| Information Sciences | Elsevier | 24 | 4 | "When does relational calibration help an LLM-as-a-judge?" (2026) |
| Decision Support Systems | Elsevier | 12 | 1 | LLM-based physician-selection behaviour |
| Int. J. Production Research | T&F | 13 | 3 | LLM multi-agent risk assessment (applications) |
| Journal of Decision Systems | T&F | 4 | 1 | users anchoring on LLM rankings |
| JORS | T&F | 1 | 1 | crowd wisdom vs LLMs for team selection |
| Omega | Elsevier | 1 | 1 | LLM and ML consensus for surgery scheduling |
| EJOR | Elsevier | 2 | 0 | none on selection |
| IISE Transactions | T&F | 0 | 0 | none (no title with "language model" since 2021) |
| Computers & OR, Computers & Industrial Engineering | Elsevier | 0 | 0 | none |

## Why Expert Systems with Applications first
- Most LLM-titled papers of the OR/AI candidates and an OR-style precedent (LLM-driven group consensus decision-making),
  cited in the related work.
- Elsevier's own transfer suggestions after the first rejection listed it at impact factor 9.4, CiteScore 17.0, first
  decision in about 5 days (figures from that email; not independently checked). VHB Rating 2024: B.
- Single-anonymized review (Elsevier default; not confirmed for this journal), so no blind build is needed.
- Caveats: **its guide for authors was not available** (ScienceDirect refuses automated access): confirm page limit,
  reference style, highlights and any cover-letter questions before upload (`docs/eswa_checklist.md`). The journal
  publishes a very large volume, so selectivity per paper is uncertain; the scope is applications of intelligent systems,
  and the paper is theory plus an audit with a null result on one weak judge.

## Alternatives, in order
1. Information Fusion (Elsevier) - guide verified earlier: research article 10-35 pages, at most 50 references, seven
   cover-letter questions. The current sources exceed both limits (39 pages in the elsarticle preprint format, 51 references),
   so it needs trimming, numeric references (`elsarticle-num-names`) and its cover-letter questions before use. No VHB entry.
2. Knowledge-Based Systems, Applied Soft Computing, Information Sciences (Elsevier): strong LLM-ensemble/voting/judge
   precedents but weaker ratings (Information Sciences VHB C); guides not checked.
3. Journal of the Operational Research Society (T&F, VHB B): OR identity and one crowd-versus-LLM selection paper, few LLM
   papers overall; Operations Research Letters (Elsevier, VHB B) for a theory-only letter.
4. IISE Transactions (T&F, VHB A): no LLM precedent; its build and checklist are kept (`submission/iise/`,
   `docs/iise_transactions_checklist.md`); engineering-practice motivation is the main risk.

VHB Rating 2024 (verified from VHB lists): EJOR A, INFORMS J. Computing A, IISE Transactions A, Discrete Applied Mathematics A,
Artificial Intelligence B, Decision Support Systems B, Expert Systems with Applications B, Operations Research Letters B,
C&OR B, Omega B, JORS B, IJPR B, Information Sciences C. Information Fusion, Knowledge-Based Systems and Applied Soft
Computing have no VHB entry. ABS/AJG and Clarivate JCR need logins and were not verified. Do not submit to two venues in parallel.

## Contributions in the current manuscript (all offline, zero API calls)
- Exact finite-pool break-even judge accuracy; difficulty-mixture effective-odds threshold with a per-problem prediction
  check (`scripts/difficulty_mixture.py`; own-k gap prediction -2.2 points vs observed -1.3, pooled-p model -10.3).
- Vote first, judge only on ties: Bayes-optimal in the model, weakly dominates plurality and Copeland
  (`scripts/hybrid_rule.py`); on stored runs it matches voting, beats Copeland-everywhere in heterogeneous pools
  (14 vs 1 discordant, p<0.001) and uses 6.7% / 4.3% of the judge comparisons; no detectable gain over voting.
- One weak free-tier judge underlies every empirical claim; a stronger-judge run (paid, needs approval) is the largest gap.

## Builds and packages
- `manuscript/main.tex` (elsarticle, author-year, `apalike-local.bst`) is the Elsevier source; `scripts/package_elsevier.py`
  writes `submission/eswa/` (PDFs, highlights, declarations, figures, source zip rebuilt in a clean directory).
- IISE: `scripts/make_iise_manuscript.py` and `scripts/package_iise.py` write the blind build in `submission/iise/`.
- TMLR: `scripts/make_tmlr_manuscript.py`; parked (not an Elsevier or T&F journal).

## Before submitting to Expert Systems with Applications (author actions)
- Read the live guide for authors; adapt reference style, length and any declarations; the cover letter has no
  journal-specific questions because none were verified.
- Enter the CRediT roles, funding, competing-interest and generative-AI statements as the portal asks (texts are in `submission/eswa/`).
- Decide on the stronger-judge run before submission if possible.
