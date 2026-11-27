# Venue decision (updated 2026-11-27): Elsevier and Taylor & Francis OR/AI journals

A first submission was desk-rejected for fit and novelty; its journal-specific files were removed (they remain in git
history). Publication cannot be guaranteed anywhere.

## Reassessment (2026-11-27, supersedes the ESWA-first recommendation further down)

The earlier recommendation of Expert Systems with Applications was wrong for this paper: its guide lists application
domains (finance, risk assessment, information retrieval and so on) and the paper evaluates none. What the paper is: a
decision-theoretic result (vote-first is Bayes-optimal in a finite-pool model), a break-even theory with a difficulty-aware
version, a cost measurement and a reproducible audit with a null result on one weak judge. It belongs where aggregation
theory or evaluation methodology is reviewed, not where applications are.

Second scan (Crossref titles since 2023; JMLR and TMLR could not be measured because of proxy errors; IP&M returned no records):

| Journal | Publisher | LLM-titled | LLM + vote/judge terms | Voting/aggregation titles without LLM | Reading |
|---|---|---|---|---|---|
| Social Choice and Welfare | Springer | 0 | 0 | 34 | voting theory home; no LLM; audience wants axioms |
| Annals of Operations Research | Springer | 1 | 0 | 30 | OR plus voting theory; VHB B |
| Pattern Recognition | Elsevier | 22 | 4 | 38 | classifier combination, voting, crowdsourcing; closest methods audience in Elsevier |
| Machine Learning | Springer | 29 | 4 | 13 | LLM plus majority voting items |
| Journal of Artificial Intelligence Research | AAAI Press | 15 | 2 | 7 | LLM benchmarks and voting theory in one venue |
| Artificial Intelligence | Elsevier | 16 | 0 | 3 | computational social choice; very selective; VHB B |
| Mathematical Social Sciences | Elsevier | 0 | 0 | 11 | voting theory; no LLM |
| Operations Research Letters | Elsevier | 0 | 0 | 3 | short theory letters; VHB B |
| Intl. J. of Approximate Reasoning | Elsevier | 4 | 0 | 7 | rank aggregation and consensus |
| Autonomous Agents and Multi-Agent Systems | Springer | 3 | 0 | 5 | judgment aggregation, majority |
| TMLR | JMLR org | n/a | n/a | n/a | not measurable here; three on-topic TMLR papers verified earlier; accepts papers on soundness of claims, not novelty |

No journal publishes the intersection (LLM answer selection with voting theory): the topic is open but also unproven. The
paper's own weaknesses decide the outcome more than the venue: elementary theory, a null empirical result, one weak
judge, and only 11 exact-tie problems per group, which limits what the vote-first audit can show.

**Within Elsevier and Taylor & Francis**, in order of fit: Pattern Recognition, Information Fusion (guide verified;
needs trimming and a stronger bar), Mathematical Social Sciences and Operations Research Letters (theory-only versions),
Artificial Intelligence (stretch). **If the restriction can be lifted**, TMLR gives the best odds for this paper, followed
by JAIR and Machine Learning; Annals of OR and Social Choice and Welfare suit a theory-only version.

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

## Decision analysis (guides for Expert Systems with Applications, Information Fusion and IISE Transactions were supplied)

Priority order set by the author: get published, in a journal that matters, ideally with an OR identity. Acceptance odds
cannot be computed; the ranking uses observable proxies (topical precedent, scope match, how hard the guide's demands are
to meet with this paper, readiness). 1 is weak, 5 is strong; judgements, not measurements.

| Criterion | ESWA | Information Fusion | IISE Transactions |
|---|---|---|---|
| Recent LLM precedent (scan) | 5 (43 LLM-titled, 5 with selection terms, a consensus decision-making paper) | 4 (31, 3) | 1 (0) |
| Scope match with the guide's own words | 3 (design, testing and management of intelligent systems, practical guidelines; but the examples are application domains and none is evaluated) | 5 ("decision fusion", "multi-classifier/decision systems"; algorithms and theory welcome) | 2 (methodology motivated by real engineering problems; only an analogy to inspection) |
| Demands the paper cannot meet | Low: no length limit; asks for application relevance | High: cover letter must show comparison with state of the art (5 references) and public datasets; "novelty" bar; 35-page limit (38 now) | Medium: 30 pages (26 ok), engineering motivation |
| Review model and readiness | Double anonymized, package built and rebuilt in a clean directory | Single anonymized; needs trimming to 35 pages and a numeric-style build; cover-letter answers rewritten | Double blind; build exists but is stale (old title) |
| Standing | Impact factor 9.4, CiteScore 17.0 (journal page); VHB B | Impact factor reported 15 to 17 (aggregators, unverified); no VHB entry | VHB A; impact factor not checked |
| OR identity | Low | Low | High |
| Speed of a first answer | Elsevier data shows about 5 days to first decision | Unknown | Unknown |

Reading: Information Fusion is the best match for the topic as the guide words it, but it sets the highest bar and the
paper is weakest exactly where that bar bites (no state-of-the-art baselines such as universal self-consistency or a trained
verifier, one weak judge, a null result). ESWA has the most precedent and the lowest compliance burden, and its stated
mission (practical guidelines for building intelligent systems) is what the new narrative supplies; its weakness is that
reviewers may ask for a real application domain. IISE Transactions has the best rating among the OR journals but no
precedent and a weak scope match, so it is the highest-risk first attempt.

**Recommendation:** submit to **Expert Systems with Applications first**; if it is rejected, adapt to the reviewers'
comments and move to **Information Fusion** (after trimming), then Knowledge-Based Systems. Keep IISE Transactions as a
stretch only if you want an OR-journal identity and can accept a likely scope rejection. This is a bet on the highest
chance of a first acceptance, not a claim of acceptance.

**What would change the recommendation:**
- A stronger-judge run and one real application domain (for example a risk-assessment or decision-support question set)
  would lift every journal; with them, Information Fusion becomes a reasonable first choice.
- If the editors at ESWA desk-reject for lack of an application, that decision arrives fast and costs little.

Caveats on the evidence: the scan counts titles only and is a lower bound; impact factors other than ESWA's are unverified;
the guides for Knowledge-Based Systems, Applied Soft Computing and Information Sciences were not available.

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
- `manuscript/main.tex` (elsarticle, author-year, `apalike-local.bst`) is the shared source. ESWA is double anonymized:
  `scripts/make_eswa_manuscript.py` writes the anonymous manuscript and supplement, and `scripts/package_elsevier.py`
  writes `submission/eswa/anonymous/` and `submission/eswa/author_files/` (source zip rebuilt in a clean directory).
- IISE: `scripts/make_iise_manuscript.py` and `scripts/package_iise.py` write the blind build in `submission/iise/`;
  regenerate and rebuild it (the title changed since it was packaged).
- TMLR: `scripts/make_tmlr_manuscript.py`; parked (not an Elsevier or T&F journal); also stale after the title change.
- Information Fusion: no separate build; it needs the numeric style (`elsarticle-num-names.bst`), a trim from about 38 to
  35 pages, and a cover letter with its seven required answers.

## Before submitting to Expert Systems with Applications (author actions)
- Complete the declarations tool and upload the anonymous files and the author files as separate items
  (`docs/eswa_checklist.md`); enter the archive DOI and CRediT roles in the form.
- Adjust the reference style by hand if the editors insist on exact APA 7.
- Decide on the stronger-judge run, and ideally add one real application domain, before submission.
