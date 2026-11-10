# EJOR submission review

**Internal working report — not part of the journal submission.**

**Manuscript at original review:** *Reproducible Answer Selection over Large Language Model Ensembles, with an Exact Kemeny Reference and a Ground-Truth Audit*

**Current submission title:** *Pairwise Judging versus Voting for Language Model Answer Selection: Finite-Pool Theory and an Empirical Audit*

**Review date:** 10 November 2026

**Recommendation:** **Major revision — not submission-ready.**

This report reviews the manuscript, online supplement, submission materials, relevant implementation, offline tests, archived-data workflow, journal guidance, and close prior work. Locations use source-file line numbers, which remain unambiguous across PDF pagination changes. They refer to the version reviewed, before any manuscript revisions.

## Editorial revision follow-up

**Latest repo/literature follow-up:** `docs/novelty_audit.md` compares the online
primary sources, including PGED and Minority Sentinel now cited in the article.
`docs/ejor_repo_audit.json` and `docs/citation_audit.json` record the final
30-page build, 218 passing offline
tests, 90 exact theorem settings with zero mismatches, and all nine generated
data files reproduced byte-for-byte. Runtime behavior and experimental records
are unchanged. README, methodology, ablation interpretation, metadata and
explanatory code docstrings are synchronized. The installed bibliography style
remains unbundled; local validation does not certify portable source packaging.

The subsequent revision targets **at most 30 pages**, including references, with 11-point type and 1.5 line spacing. The first shortening pass reached **23 pages** and compressed explanatory material too aggressively. Following author feedback, the next pass restores operational context, close-literature comparison, method interpretation, finite-pool calculations and two central tables. That restoration produced **29 pages**; the final published-reference and citation pass produces **30 pages**, with the supplement still **10 pages**. `docs/ejor_shortening_evidence.json` records the restoration build and `docs/citation_audit.json` the later citation build; `docs/ejor_review_evidence.json` describes the original audit, not the current pagination. `docs/ejor_length_changes.md` lists what was removed, condensed, relocated and restored.

The revision removes repeated contribution/result summaries and the duplicate accuracy plot; condenses the protocol, discussion and conclusion; moves secondary generator and soft-score tables into the supplement; and retains the central theorem, its proof, formulations and core result tables. The finite-pool threshold table and RewardBench category table return to the main text in the restoration pass. The practical use case now appears in the Introduction.

It also removes “overturns” and universal deployment-test claims, states conditional comparison independence, separates soft-score diagnostics from binary-comparison theory, corrects the scope of the inherited ranking bound, and discloses integerization and answer-level replay limitations. Cover letter, highlights and diagram labels are aligned. Numerical result macros, run files and implementation remain unchanged.

**This is an editorial correction, not a submission-readiness certification.** Outstanding decisions include sufficient EJOR methodological novelty, paired effect-size uncertainty, checks of mathematical grading discordances, a permitted GPQA replay artifact, and portable solver/build dependencies. A stronger-judge experiment would broaden the empirical evidence; theory for soft-score selection would create the operational bridge that the revised manuscript now explicitly declines to claim. The numbered findings below preserve the original review and are not a claim that every cited wording defect remains present.

These are internal review assessments, not text to insert into the paper. The submission's internal-review TODO list has been removed; completed methods, theorem assumptions and data-access conditions remain described accurately. The novelty assessment does **not** establish duplication of the exact finite-pool theorem: close prior work establishes several ingredients and the possibility that voting beats judging, while the exact finite-pool comparison remains the specific theoretical contribution advanced here. Whether that contribution is substantial enough for EJOR is distinct from whether an identical theorem has already appeared.

## Summary

The paper addresses an important selection decision: given several generated answers, when should an external pairwise judge replace plurality voting? Its strongest components are an explicitly auditable pipeline, comparison with a Kemeny ranking reference, paired ground-truth evaluation, and an exact small-pool model connecting candidate accuracy to the comparison accuracy needed to outperform voting. The manuscript also documents model withdrawals, protocol changes, output truncation, and its single-judge limitation more openly than many empirical papers. These are genuine strengths.

The central three-candidate calculation is algebraically correct **under conditionally independent comparison outcomes and the other stated modeling restrictions**. Independent exhaustive enumeration matched its formula at 90 parameter settings. However, the statement currently omits comparison independence, and the empirical quantity called judge accuracy is a mean soft score, not the Bernoulli comparison accuracy in that theorem. The latter is a substantive inferential gap, not a wording issue. Consequently, the current empirical threshold table does not establish that the measured judge lies below a valid operational break-even threshold, let alone that any judge-based selector cannot help.

I agree that “overturns” should be removed throughout the submission. I do **not** yet endorse the proposed replacement “gives the test to check any other judge” without qualification. The defensible result is a model-specific break-even calculation plus a negative audit of one free-tier judge configuration. EJOR Theory and Methodology fit is plausible, but sufficient methodological originality remains an editorial risk: the one-hot objective is an argmax, the ranking approximation is inherited, and the negative empirical phenomenon already appears in close prior work. Neither this review nor passing tests can make a submission “bomb-proof.”

## Major issues

### 1. The empirical threshold application uses the wrong estimand

**Severity: Critical.** `manuscript/main.tex:364–386, 846–876, 945–956`; `scripts/judge_threshold_empirical.py:29–57`; `or_select/pairwise.py`.

The theorem uses a hard comparison that favors the correct candidate with probability \(q\). In contrast, the empirical analysis averages the soft probability assigned to the correct candidate, after averaging forward and reverse prompts. The implemented quality selector maximizes weighted row sums of these scores. An average score is neither the probability of a hard comparison being correct nor sufficient to determine the selector's accuracy.

**Counterexample:** set every correct–wrong weight to 0.6 in the correct direction and every same-class weight to 0.5. Weighted outdegree then selects a correct candidate whenever one exists. At \(p=0.8,N=3\), its accuracy is \(1-(1-p)^3=0.992\), exceeding plurality's 0.928. Yet its mean mixed-pair soft score is only 0.6, below the reported 0.8035 threshold; the Bernoulli theorem at \(q=0.6\) predicts 0.84608 instead. This disproves the current bridge even before adding confidence, consistency, or cost.

**Required:** either derive a result for the actual score-valued selector, or clearly separate the theorem from the empirical audit. For a direct hard-comparison validation, specify how scores become outcomes, measure the corresponding correctness probability, reproduce the theorem's selector and tie policy, and investigate dependence and heterogeneity. Until then, relabel the table as a descriptive soft-score diagnostic and remove threshold-based certifications of empirical failure. RewardBench accuracy, hard mixed-pair accuracy, and mean soft score must have different names.

### 2. Comparison independence is missing from the theorem statement

**Severity: Significant; invalid as a theorem from the stated marginals alone.** `manuscript/main.tex:364–386, 1047–1080`; `manuscript/supplement_body.tex:6–16, 169–214`.

Candidate correctness is explicitly independent, but the three comparison outcomes are not explicitly conditionally independent. The proof multiplies comparison probabilities. Marginal accuracy \(q\) alone does not justify this.

For example, conditional on one or two correct candidates, couple the two mixed comparisons so that both favor their correct endpoint with probability \(q\), and both favor their wrong endpoint otherwise. Keep the same-class edge fair. Every mixed edge still has marginal accuracy \(q\), but selection accuracy becomes \(p^3+3p(1-p)q\). At \(p=q=0.8\), this is 0.896, versus the theorem's 0.92672.

**Required:** explicitly state conditional independence of all pair outcomes given the correctness vector, fresh uniform same-class comparisons, and the independent uniform tie rule. State that correct candidates share the same answer label and wrong labels are distinct in the base model. Carry the appropriate independence assumptions into the extensions and concentration arguments. Describe this as an idealized stochastic comparison model, not as the observed API's established behavior.

### 3. Abstract, highlights, cover letter, and discussion exceed the evidence

**Severity: Significant.** `manuscript/main.tex:59, 130–137, 926–956, 998–1008`; `manuscript/Cover_Letter_EJOR.tex:15–17`; `manuscript/highlights.txt`.

One free-tier judge configuration cannot overturn a general assumption about judges. Homogeneous results do not establish equivalence or absence of useful signal. Heterogeneous results establish that the **evaluated composite selector** underperforms plurality in the pooled sample, not that every use of its judge must underperform. A stronger judge could clear a model-specific threshold. Existing work also reports majority beating judge-based selection.

**Required:** remove “overturns,” universal “any judge-based selector” claims, and unsupported equivalence language. Use “no statistically detected improvement” for the homogeneous comparison and “lower pooled accuracy for the evaluated configuration” for the heterogeneous comparison. Do not present an unvalidated model threshold as the empirical explanation of those outcomes. Apply revisions consistently to all submission files, not only the abstract.

### 4. Novelty needs a sharper, less permissive assessment

**Severity: Significant; EJOR desk-rejection risk.** `manuscript/main.tex:95–128, 172–208, 265–353`; references [4–6] below.

The paper properly attributes the 5-approximation and admits it introduces no faster solver. However, encoding independent candidate scores with one-hot variables is computationally an argmax, and exact small-instance Kemeny optimization is established methodology. Their implementation and use as an audit reference are valuable artifacts, not new optimization algorithms.

Close work matters particularly:

- **Komiyama et al., Best-of-Infinity:** adaptive voting, MILP ensemble weights, and an AIME 2025 selection comparison already showing majority outperforming judge tournaments and set selection. The negative phenomenon and an OR/MILP framing are therefore not new by themselves.
- **Di et al., Best-of-Majority:** finite-budget theoretical treatment combining answer frequency and imperfect reward information. Different assumptions and procedures, but a close comparator for the claimed theory contribution.
- **Ai et al., Beyond Majority Voting:** aggregation under heterogeneous accuracies and dependence. Different from external pairwise Copeland selection, but directly relevant to the practical limitation of the iid model.

**Required:** add an assumption/result/comparator table distinguishing the exact finite-\(N\) pairwise threshold from these contributions. State what is newly proved, what is a computational reference, and what is empirical evidence. Explain why the new theorem and extensions support a substantive OR decision, rather than relying on “not previously in EJOR.” A genuinely stronger judge comparison would improve empirical persuasiveness; alternatively, stronger theory handling a material real-world departure could improve the methodological case. Publication-level novelty cannot be certified by the current audit.

### 5. Average judge quality does not validate homogeneous pairwise bounds

**Severity: Significant.** `manuscript/main.tex:428–465, 846–876`; `manuscript/supplement_body.tex:6–16, 139–146`.

The extensions can use a common lower bound on every relevant mixed-pair probability through coupling. A pooled average does not establish such a bound. Nor does an average below the homogeneous threshold prove that every pair is too weak. Generator identity, task difficulty, answer length, and within-problem dependence may all affect comparison quality. Pool-average \(p\) likewise need not describe each prompt's candidate correctness distribution.

The wrong-answer collision parameter \(\rho\) is useful, but it does not model dependence of candidate correctness, correlated judge errors, or all possible wrong-label distributions. At \(\rho=1\), all wrong answers share one label; this is not a generic four-option multiple-choice model with three possible distractors.

**Required:** scope homogeneous thresholds to their model; state exactly what each extension relaxes. Describe heterogeneous-track plug-in values as illustrative unless a valid heterogeneous model is derived and checked. Remove “quality-only is the most favourable case” and “independent cost can only move accuracy toward random selection” as general propositions unless additional assumptions and proofs are supplied. Informative auxiliary signals can improve a selector.

### 6. The uncertainty analysis does not support a deployment decision rule

**Severity: Significant.** `manuscript/main.tex:557–576, 846–876, 973–991`; empirical-threshold script; preregistration documents.

The threshold table bootstraps wrong-answer collision estimates, while treating estimated candidate accuracy as fixed and not quantifying uncertainty in the mixed-pair judge estimate. Its bands are therefore **not** uncertainty bands for whether the judge clears a deployment threshold. Mixed-pair counts are small on some tracks: 72 on homogeneous GPQA and 28 on homogeneous MMLU-Pro, clustered within problems. Even a large pair count does not imply that many independent observations.

Exact paired McNemar testing is appropriate for a fixed paired comparison. The pooled homogeneous result has 10 versus 13 discordant wins, a difference of −3/532 = −0.56 percentage points; its nonsignificance is not equivalence. The heterogeneous result has 10 versus 32, a difference of −22/402 = −5.47 points. Report paired effect intervals as well as p-values. Six homogeneous benchmarks contain 532 unique problems; four heterogeneous tracks reuse 402 of those problems. Do not count these as 934 independent unique problems.

**Required:** use problem-level resampling or an appropriate paired interval; if retaining threshold estimation, jointly propagate uncertainty in all estimands with a valid model. Label the post-registration pooled and added-track analyses exploratory. Explain deviations from the original MATH track's registered primary tests and interval choices. State the target population: these deterministic convenience subsets and tracks are not a random sample of all reasoning tasks. Avoid interpreting RewardBench's selected first-seven-per-subset sample as population-representative calibration.

### 7. Generator preference and cost dominance are not isolated causal mechanisms

**Severity: Significant.** `manuscript/main.tex:736–756, 785–808, 926–943`; `scripts/analyze_selection.py`; `scripts/ablation_weights_offline.py`.

Generator selection shares describe the **composite OR-Select objective**, not the pairwise judge alone. Output length, confidence, consistency, generator identity, and answer quality can be associated. Comparing cost spread only with the range of the quality component does not prove that cost determines the winner: all objective terms and the competing candidates' signs matter. The ablations are informative, but do not by themselves establish a causal decomposition into four mechanisms.

**Required:** attribute selection shares to OR-Select. Report quality-only and component-wise winner changes; separate conditional associations from causal explanations. For an actual judge-bias claim, use controlled order/model-identity/length checks or appropriately qualified language. Describe cost as a word-count penalty with arbitrary scaling, not measured API spend or latency.

### 8. “Exact Kemeny” and “exact replay” require more precise certificates

**Severity: Significant.** `manuscript/main.tex:286–353, 892–899, 1010–1018`; `or_select/selection.py:27, 83–98`; `or_select/kemeny.py:88–110`; `scripts/ablation_weights_offline.py:66–101`.

Both implementations round objectives at scale 10,000. The Kemeny solver optimizes rounded pair differences, not literally the original real-valued matrix objective; rounded ties can change the optimal ranking. A single solver worker is not a cross-version canonical tie policy. A conflict budget can return a feasible, nonoptimal ranking, which must not be called an exact optimum. The existing replay fidelity calculation compares extracted final-answer strings, not selected candidate IDs, full texts, objective values, or rankings. Equal extracted answers can mask different candidate selections.

**Verified positive finding:** all 854 saved current-version Kemeny results inspected report `is_optimal=True`. No budget-exhausted reference was found in that set. This supports the current solver-status claim, but does not independently certify the unrounded objective or canonical tie resolution.

**Required:** distinguish optimality for the integerized objective from the unrounded objective. Publish solver/version metadata, status, objective and bound, and a canonical tie policy or all-optimal-winner convention. With pools of at most six, independently enumerate at most 720 permutations to validate the Kemeny reference. Verify candidate-level replay, separately reporting answer-level agreement and exclusions for rows lacking judgments. Pin the environment and make the fidelity claim match what is actually checked.

The inherited 5-approximation concerns the **full ranking's disagreement objective** under complementary nonnegative weights. It is not a top-one correctness guarantee, not an approximation guarantee for the composite score, and not a new theorem here. Keep this distinction visible in the abstract, highlights, and conclusion.

### 9. Public exact replay is incomplete without GPQA-derived artifacts

**Severity: Significant.** `manuscript/main.tex:1010–1018`; README reproduction steps; Zenodo record [7]; scripts' missing-file handling.

The public archive explicitly omits GPQA output JSON because it contains gated question text. Respecting redistribution restrictions is correct. However, regenerating outputs with live models is a new stochastic experiment, not replay of the published experiment; model withdrawal makes this distinction especially important. Offline scripts silently skipping absent tracks can produce an apparently successful but incomplete regeneration.

**Required:** release a license-compatible derived/redacted GPQA artifact sufficient for the advertised numerical audit, or clearly delimit public reproducibility. Candidate correctness flags, anonymous problem IDs, final labels, selector decisions, permitted comparison matrices, and certificate metadata may suffice for much of the audit without redistributing questions; verify what the dataset license permits before release. Add a manifest of expected track counts and hashes, and fail loudly or explicitly label partial reproduction when required inputs are absent. Distinguish local full-data regeneration from public-archive reproduction.

### 10. Comparator names, grading, and pool construction need tightening

**Severity: Significant.** `manuscript/main.tex:227–255, 473–552`; `or_select/baselines.py`; `or_select/math_eval.py`; provider retry implementation.

“Greedy” is the first sampled candidate, not an independently generated temperature-zero greedy answer. Plurality uses extracted answers, whereas the composite consistency term uses full-text identity. Fixed candidate order resolves plurality ties in favor of earlier generators in heterogeneous pools. Truncation/invalid-output resampling changes the sampled population; different seeds do not establish independent candidate correctness. Model replacements further change the pool distribution.

MATH grading relies on heuristic string normalization rather than general mathematical equivalence; its own implementation acknowledges false negatives such as unsimplified equivalent fractions. Differential formatting by length or generator could affect selector comparisons.

**Required:** rename “greedy” to “first sampled answer” unless actual greedy decoding is added. Explain both consistency definitions and tie policies. Audit order sensitivity for heterogeneous ties. State the effective post-retry sampling procedure. Manually adjudicate at least method-discordant MATH cases under a documented blinded rule, report changed counts if any, and disclose residual grading limitations. Preserve the useful model-drift documentation, but do not call the heterogeneous population stationary.

### 11. Several mathematical statements need local corrections

**Severity: Significant for correctness; mostly inexpensive to repair.**

- **Cost lemma:** `main.tex:413–426` quantifies a strict inequality over every \(j\), including the shortest candidate itself, which would require \(0>0\). Exclude that index; state candidate eligibility and nonnegative-weight assumptions.
- **Boundary and threshold wording:** `main.tex:381–385` divides by zero at \(q=1\). State the interior domain and treat endpoints separately. With a strict improvement condition, \(q^*\) is a break-even root/infimum, not an attained “smallest winning” value.
- **Numerical endpoint:** `main.tex:443–444` gives 0.935 for the stated \(N=3\) to \(7\) range; the supplement's \(N=7,p=0.8,\rho=0\) value is approximately 0.945. The 0.935 value is for \(N=6\).
- **Large-\(N\) bound:** `supplement_body.tex:86–97, 221–234` should explicitly restrict the optimization variable to a binomial fraction \(\eta\le1\), state the interior \(q<1\) domain, and handle endpoints. Clarify that the designated wrong candidate is selected conditional on the correctness configuration. The missing fixed-index factor is **not** an error if that is the intended designation.
- **Consistency is not finite-\(N\) impossibility:** `main.tex:938–943`; `supplement_body.tex:169–186`. Plurality tending to one when the correct label is most probable does not mean a judge cannot improve finite-sample accuracy or the error exponent. A perfect judge already provides a counterexample. Global average candidate accuracy also does not establish this regime for each prompt.

### 12. Submission formatting and source reproducibility are not yet cleared

**Severity: Confirmed formatting blocker.** `manuscript/main.tex:1–3, 1082`; supplement bibliography setup; submission files.

The checked official EJOR guide calls for a regular manuscript of at most 35 pages, single-column 11-point text with 1.5 spacing and no line numbering. The current source uses `\linespread{1.24}`. In an isolated copy, a complete local TeX/BibTeX rebuild succeeds at 35 pages. Changing only that spacing command to `\linespread{1.5}` and recompiling produces **41 pages**, six over the checked limit. The original source/PDF was not modified.

The bibliography style `apalike-ejor` is not tracked in the repository, but it **is installed in the current TeX environment**, explaining the successful local build. Thus there is no observed local bibliography compilation failure. A portable source bundle still needs the required dependency or documented installation route; the local success does not establish a clean-machine build.

**Required:** cut/restructure at least six pages at the tested compliant spacing; do not solve the limit with tighter spacing. Move secondary ablations, implementation detail, or established formulations to the supplement while preserving the principal theorem, empirical estimands, and limitations in the main text. Compile from a portable source bundle and recheck pagination. Confirm APA author–date formatting rather than relying on an unofficial template. Recheck title, abstract, keyword, highlights, declarations, and submission upload requirements against the live guide immediately before upload. Detailed checklist below.

## Minor issues

1. `main.tex:172–179`: the strict latent-ranking Condorcet noise model is not “exactly” the two-correctness-class model with fair same-class comparisons. Describe the relationship without identifying them.
2. `main.tex:220, 958–967`: generation is not the only stochastic API stage. Deterministic **replay given all saved outputs** is different from deterministic generation and judging.
3. `main.tex:958–967`; `supplement_body.tex:343–367`: repeated scores differing does not uniquely establish that a provider ignores a seed unless prompts, model/version, seed, and all other settings were fixed. Fresh seeds do not prove independent samples.
4. `main.tex:265–273`: the displayed minimum-quality constraint should gate the selected candidate, matching the implementation, rather than require every candidate to clear the minimum. Define the off-diagonal mean explicitly; \(W_{ii}\) is not part of quality aggregation.
5. `main.tex:830–841`; `supplement_body.tex:250` and baseline table: “No selector beats plurality” is numerically false. MBR is slightly higher on both pooled groups, without a significant paired improvement. Say that no tested alternative demonstrates a significant improvement, with multiplicity/exploratory qualifications.
6. `main.tex:75` and related framing: plurality with an explicit tie rule is well-defined even when all answers differ. It may be uninformative; it is not undefined.
7. `main.tex:557–576`: “floor” is a random-selection reference, not a mathematical lower bound on every selector. Define recovery as undefined when oracle accuracy equals this reference.
8. `main.tex:945–956`: move a **qualified** “Outcome and where it applies” subsection to the end of the Introduction. Separate theoretical eligibility screening from held-out deployment evaluation.
9. `main.tex:519–526, 584–610`: retain both macro and micro RewardBench summaries, explain deterministic subset selection, and do not equate its overall score with in-distribution mixed-pair accuracy.
10. `main.tex:973–991`: keep the strong limitation disclosures, but reconcile them with stronger abstract/discussion claims rather than relying on a late caveat to undo those claims.
11. `supplement_body.tex:321–337`: three ungraded illustrative queries are not accuracy evidence. Distinct full texts also do not rule out common semantic answers.
12. `supplement_body.tex:375–383`: the worked example reconstructs quality algebraically from the saved final score rather than independently recovering a stored matrix. Label it an illustration, not an independent component-level replay validation.
13. `scripts/ablation_weights_offline.py:99`: if “SC + quality” is intended to break only plurality ties, implement/describe lexicographic `(count, quality)` rather than addition, whose boundary behavior can cross count tiers.
14. `requirements.txt`: versions are unpinned; distinguish the successful current-environment test run from clean-environment installation and long-term reproducibility.
15. AI-use statements should accurately name tools actually used. This review cannot verify the historical model identity in the existing declaration. The author remains responsible for mathematics, references, and the final text.

## Mathematical verification

### Independently verified base result

For the intended independent-edge, uniform-tie model, conditional selection probabilities are

\[
a_1(q)=q^2+\tfrac13q(1-q),\qquad
a_2(q)=q^2+\tfrac53q(1-q),
\]

where the subscript is the number of correct candidates. Thus

\[
A_J=p^3+3p^2(1-p)a_2(q)+3p(1-p)^2a_1(q),
\qquad A_V=p+p^2(1-p).
\]

Subtracting yields the manuscript's

\[
\Delta=p(1-p)\{(1-p)(2q-1)(q+1)-p(3-2q)(1-q)\}.
\]

An independent audit enumerated all eight correctness vectors and all eight comparison vectors using exact rational arithmetic at 90 settings: \(p=0.1,\ldots,0.9\), \(q=0.1,\ldots,1.0\). **Zero mismatches.** This is stronger than merely rerunning the manuscript's own enumeration code, but remains verification of the specified model rather than of real API assumptions.

- At \(p=0.8\), the break-even root is **0.8035152756999545**.
- At \(q=1/2\), \(A_J=p\), so \(\Delta=-p^2(1-p)\); at \(p=0.8\), this is −0.128.
- The theorem **does quantify how much** a better judge helps through \(\Delta(p,q)\). The limitation is transport to real judging, not absence of a modeled gain formula.
- The monotone coupling argument and large-pool consistency direction are sound with the needed independence/same-class assumptions made explicit. The displayed concentration bound is loose rather than invalid merely because a smaller union factor may be possible.
- The finite-\(N\) enumeration and wrong-collision extensions are useful. They should not be advertised as resolving arbitrary heterogeneity or dependence.

### What was not established

No proof was found that a mean soft score below the Bernoulli threshold excludes useful weighted selection. The explicit counterexample above shows that general claim is false. No theorem establishes that the evaluated composite objective is the most favorable possible use of the judge. Neither an exact ranking optimum nor a 5-approximate ranking implies high answer correctness.

## Empirical and reproducibility verification

- **Offline test suite:** 218 tests passed; the live-provider test module was excluded. This checks the current environment, not every dependency/version combination or every manuscript inference.
- **No paid/live model experiments launched.** The review uses saved outputs and read-only public-source checks.
- **Main paired counts:** homogeneous 10 OR-only versus 13 plurality-only correct decisions, \(n=532\); heterogeneous 10 versus 32, \(n=402\). These support a nonsignificant homogeneous comparison and a significant negative pooled heterogeneous comparison, not equivalence or universal judge failure.
- **Baseline contradiction checked:** pooled MBR accuracy is 85.9% versus plurality 85.5% for homogeneous pools, and 85.3% versus 85.1% for heterogeneous pools. The relevant paired comparisons are not significant; “none numerically better” is incorrect.
- **Threshold estimand inspected:** mean correct-directed pair weight, not a count of successful hard comparisons. Its \(\rho\)-only bootstrap cannot justify the claimed deployment classification.
- **Replay check inspected:** existing “fidelity” measures extracted-answer agreement. Full candidate identity and ranking replay require additional checks.
- **Public archive:** DOI `10.5281/zenodo.24112045` resolves to the stated release; its description explicitly excludes GPQA output JSON. A public release exists, but that is not by itself proof of full paper-number reproducibility.
- **Local numerical regeneration:** `Results_data.tex`, `Selection_data.tex`, `Ablation_data.tex`, `Baselines_data.tex`, and `ThresholdEmpiricalGeneral_data.tex` regenerate byte-for-byte identically when their destinations are redirected to an isolated copy. This is a genuine strength. Local GPQA JSON files exist; the public-archive limitation must not be confused with their local absence.
- **Kemeny status check:** all 854 current-version saved references report optimality for the solver's integerized objective. Independent exhaustive ranking certification was not performed.
- **TeX build:** `pdflatex`, `bibtex`, and two further `pdflatex` passes succeed in an isolated copy. The custom bibliography style is supplied by the existing TeX installation, not tracked source. Current main PDF: 35 pages; supplement: 10 pages. With the main source's spacing changed to 1.5 in the isolated copy: **41 pages**.
- **Abstract/highlights:** expanding the abstract's numeric macros gives a whitespace count of **247 words**, within 250 but with almost no margin. A naive PDF extraction count is misleading because it includes author footnotes and line-wrap artifacts. All five existing highlight lines are within 85 characters, even counting their leading bullet markers; content, not length, is the problem.
- **Recorded verification:** see [`ejor_review_evidence.json`](ejor_review_evidence.json) for the local build, macro comparison, spacing, and saved-status results. Temporary build copies were removed after the audit.

## EJOR submission checklist

Checked against official indexed guide text [1] and EJOR scope [2]. The full guide was not retrievable directly in this session; reconfirm requirements in the live submission system.

| Item | Assessment / action |
|---|---|
| Article category | Theory and Methodology is a plausible category only if the new OR contribution is made substantive and explicit. |
| Regular-paper length | **Fails the tested compliant layout: 41 pages versus 35 allowed.** Current compressed-layout PDF has 35 pages. |
| Layout | Single column, 11 point, 1.5 spacing, no line numbers. Current `\linespread{1.24}` needs correction and six pages of shortening at the tested setting. |
| Review anonymity | Single-anonymized according to the checked guidance; do not unnecessarily strip the author from a compliant title page. |
| Title | Avoid formulas and unexplained abbreviations/acronyms. The present title is spelled out but long; shortening would help. |
| Abstract | Maximum 250 words. Current expanded-source whitespace count: 247. Revise overclaims, avoid unexplained abbreviations/formulas, and recount the final text. |
| Keywords | Maximum five; first from the journal's official list. Current first keyword, “Artificial intelligence in OR,” matches the checked list. |
| Highlights | Separate editable file; 3–5 bullets, each at most 85 characters including spaces. Five are supplied and meet the length cap; substantive claims need correction. |
| References | APA author–date; verify actual rendered style and all citation resolutions. Custom `.bst` is installed locally but untracked. |
| Figures/tables | Embed near first discussion; captions must distinguish aggregate pool sizes, unique problems, macro/micro scores, and the meaning of intervals. |
| Title page | Author/affiliation/correspondence materials exist. Author should verify current postal/email/ORCID details. |
| Cover letter | Remove “overturns” and universal screening claims; state the new methodology accurately. Verify the currently appropriate editor/address at upload. |
| Competing interests / funding / CRediT | Materials exist; author must verify factual declarations and upload them in the required fields. |
| Generative AI disclosure | Materials exist; verify accuracy and consistency with journal policy and actual use. |
| Data/code availability | DOI exists; explicitly disclose GPQA limitation and distinguish replay from regeneration. Release a complete permitted audit manifest. |
| Source bundle | Local isolated rebuild passes. Include/document the external bibliography-style dependency and test a portable bundle without stale generated artifacts. |

Do **not** use EJOR Short Communications merely as a shorter format for this paper: the checked scope describes that category as correcting important errors in previously published EJOR papers.

## Recommended claim revisions

### Abstract / Introduction outcome

> In paired evaluations of one free-tier judge configuration, the evaluated composite selector shows no statistically detected improvement over plurality in homogeneous pools and lower pooled accuracy in heterogeneous pools. We separately derive an exact break-even condition for an idealized independent-comparison Copeland model. These results motivate measuring judge quality and validating the intended selector on held-out tasks rather than assuming that additional judging improves selection.

This wording deliberately does not claim that the current soft-score table validates the theoretical condition. It should be revisited if that bridge is repaired.

### Methodological contribution

> Our theoretical contribution is an exact finite-pool comparison of plurality and judge-based Copeland selection under explicit probabilistic assumptions, with enumerated extensions for pool size and wrong-answer collisions. Exact Kemeny optimization provides an established ranking reference, and saved outputs support an auditable evaluation of the implemented selectors.

Do not call the established Kemeny formulation, inherited approximation factor, or the one-hot argmax a new optimization algorithm.

### Practical use case, suitable for the Introduction after qualification

> The threshold is an analytical diagnostic for small candidate pools with approximately independent correctness and comparison outcomes, a specified tie rule, and a comparison process matching the model. It is not a universal deployment test for arbitrary scoring judges. In practice, estimate task-specific quantities on labeled data, assess uncertainty and model departures, and compare the actual selector with plurality on held-out problems.

### Cover letter

> The submission studies when pairwise answer judging can improve on plurality. It combines an exact finite-pool threshold under an explicit stochastic model, a Kemeny ranking reference, and a paired audit of one free-tier configuration. The empirical results are configuration-specific; the methodological contribution is the transparent separation of ranking optimality, answer correctness, and assumptions needed for threshold-based reasoning.

### Safer replacement highlights

Each line below is comfortably below the 85-character limit; verify the exact final upload text.

```text
An auditable pipeline compares answer selectors on saved candidate pools
Exact Kemeny rankings provide a reference, not a correctness guarantee
One free-tier judge configuration does not improve on plurality in this audit
An exact small-pool model gives a break-even condition for pairwise judging
Explicit assumptions delimit when the threshold can inform selector choice
```

## Submission gates and recommendation

### Gate A — Scientific validity: mandatory

1. Repair or remove the soft-score-to-Bernoulli threshold inference everywhere.
2. Add conditional comparison independence and fix the local theorem/lemma/domain statements.
3. Remove unsupported universal, equivalence, causal, and finite-\(N\) impossibility claims.
4. Add paired effect intervals and correctly label exploratory/post-registration analyses.
5. Audit grading on method-discordant mathematical answers and clarify the sampled-answer comparator.

### Gate B — EJOR contribution: mandatory decision

6. Write a close-prior-work comparison and an honest novelty statement.
7. Decide whether the present exact threshold plus extensions is a sufficiently substantive new OR result. If not, strengthen theory around a real model departure or add convincing selector-specific validation with a genuinely stronger judge. A more polished narrative alone cannot guarantee this gate.
8. If general judge claims are retained, evaluate more than one weak judge on fixed pools with matched protocols. This review does not authorize or perform new paid API experiments.

### Gate C — Audit and production: mandatory

9. Validate all exact-reference statuses and integerization effects; strengthen fidelity checks beyond extracted answers.
10. Publish a complete permitted audit artifact, input manifest, hashes, pinned environment, and explicit missing-input behavior.
11. Produce clean, compliant main/supplement builds; verify reference style and page count at required spacing.
12. Synchronize abstract, Introduction, Discussion, conclusion, highlights, cover letter, and availability statement.

**Final recommendation: Major revision.** The base calculation is salvageable and useful, and the negative empirical audit can be reported honestly. The current submission is not ready because its central empirical threshold interpretation is unsupported, the theorem statement lacks a necessary independence assumption, and the manuscript exceeds the checked page limit at required spacing. Local numerical regeneration and saved Kemeny statuses check out, but audit-scope and portability claims need tightening. No evidence of research misconduct was established. No confidential-editor allegation is warranted.

**Edits performed during this review:** this report and temporary audit helpers only. The manuscript, cover letter, source implementation, and reported results have not been silently revised.

## Sources and review limitations

1. **EJOR Guide for Authors:** <https://www.sciencedirect.com/journal/european-journal-of-operational-research/publish/guide-for-authors>. Official indexed excerpts checked; direct full-page access failed. Submission rules may change.
2. **EJOR scope:** <https://www.euro-online.org/web/pages/518/european-journal-of-operational-research-ejor> and <https://shop.elsevier.com/journals/european-journal-of-operational-research/0377-2217>.
3. **Coppersmith, Fleischer, and Rudra:** primary approximation paper, <https://cse.buffalo.edu/faculty/atri/papers/algos/CFR06.pdf>; technical report <https://eccc.weizmann.ac.il/report/2005/131/>. Used to check the scope of the inherited ranking guarantee.
4. **Komiyama et al., Best-of-Infinity:** <https://arxiv.org/html/2509.21091>. Read for adaptive voting, MILP ensemble design, and the already-reported majority-versus-judge comparison.
5. **Di et al., Best-of-Majority:** <https://arxiv.org/html/2510.03199>. Read for finite-budget selection theory using frequency and imperfect reward information.
6. **Ai et al., Beyond Majority Voting:** <https://arxiv.org/html/2510.01499>. Read for heterogeneous/dependent aggregation theory.
7. **Public artifact:** <https://doi.org/10.5281/zenodo.24112045>, machine-readable record <https://zenodo.org/api/records/24112045>.

The full main source and supplement were read. Relevant selectors, grading, analysis scripts, prompts, protocol notes, and submission materials were inspected. Three central EJOR-reference metadata records were checked against Crossref, and the approximation result and three close selection/aggregation papers were checked directly. This is **not** a comprehensive literature search, full citation-by-citation verification, plagiarism clearance, legal dataset-license opinion, or real-world validation of the judge's stochastic assumptions. No live model calls or new large-scale experiment was run. Acceptance and desk-screening outcomes remain editorial judgments.
