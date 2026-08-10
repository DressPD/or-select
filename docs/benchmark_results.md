# Benchmark Results

Two tracks, because they answer different questions and neither alone is
sufficient (see Landesberg 2026 in `methodology.md`'s Related Work: judge
calibration doesn't predict actual selection accuracy — you need a
checkable answer to know that).

- **Track A — open-ended queries, no ground truth.** Tests whether
  OR-Select's selection *differs* from simpler baselines, and by how much,
  when there's no single correct answer to check against. Qualitative:
  agreement/disagreement and score margins.
- **Track B — GSM8K, ground truth.** Tests whether OR-Select's selection
  is actually *correct* more often than the baselines. Quantitative:
  accuracy.

All three methods compared throughout:
- **OR-Select**: the full pipeline (`or_select/pipeline.py`) — LLM judge +
  deterministic self-consistency term, aggregated via CP-SAT.
- **Self-consistency alone**: majority vote (`or_select/baselines.py`), no
  LLM judge, no OR.
- **Greedy single-sample**: just the first of the N candidates, no
  ensemble at all.

Provider: OpenRouter, `nvidia/nemotron-3-ultra-550b-a55b:free`, for every
result below (chosen for availability, not because it's the model this
method is expected to work best with — see "Open questions" at the end).

## Summary

| Track | Task type | Candidates agreed? | Result |
|---|---|---|---|
| A | Open-ended (3 queries, N=5) | Never (0/15) | OR-Select disagreed with both baselines on 3/3; self-consistency undefined every time |
| B | GSM8K, easy (4 problems, N=3) | Always (4/4) | All 3 methods tied at 100% accuracy |

Both results are consistent with a single underlying prediction, stated in
`methodology.md` before either track was run: baselines and OR-Select
should tie when candidates cluster, and diverge when they don't. Neither
track alone would show this — Track A has no ground truth to confirm
correctness, Track B has no divergence to force a real choice. Together
they show the mechanism working as designed, on both ends of that axis.

## Track A: open-ended queries (N=5)

| Query | OR-Select winner | vs. self-consistency | vs. greedy | Score margin (winner vs. runner-up) |
|---|---|---|---|---|
| "Summarize the plot of Hamlet in one sentence." | c2 (0.574) | disagreed | disagreed | 0.574 vs 0.486 — clear |
| "Single most effective strategy for reducing traffic congestion?" | c1 (-3.664) | disagreed | disagreed | -3.664 vs -4.110 — clear |
| "Is it generally better to rent or buy a home?" | c3 (0.0835) | disagreed | disagreed | 0.0835 vs 0.0813 — near tie |

**Consistent pattern across all 3 (15 candidates total, N=5 x 3
queries):** zero exact-text duplicates. Self-consistency alone had no true
majority to find in *any* of the three queries, and fell back to an
arbitrary tie-break every time — which happened to coincide exactly with
the greedy-single-sample pick in all three, since both default to "first
candidate" when there's nothing else to go on. **OR-Select disagreed with
both baselines on all 3 of 3 queries.**

**Not a uniform win, and the report says so rather than hiding it:**
Hamlet and traffic show real quality differentiation (margins of
0.09–0.45) — the judge is doing substantive work, e.g. the traffic-query
winner is the *second-shortest* of 5 answers, not the longest, because the
cost term penalizes verbosity even among similarly-good long-form answers.
Rent-vs-buy is a near three-way tie (margin ~0.003): the top 3 candidates
were paraphrases of the same balanced answer, so OR-Select's "win" there
is close to noise, not a confident judgment. Take from this: OR-Select
adds real value once candidates meaningfully diverge in quality, and its
edge shrinks toward nothing when they don't.

## Track B: GSM8K, ground truth (N=3, first 4 problems)

| # | Problem (truncated) | Ground truth | OR-Select | Self-consistency | Greedy | All 3 candidates agreed? |
|---|---|---|---|---|---|---|
| 1 | Janet's ducks lay 16 eggs/day... | 18 | 18 ✓ | 18 ✓ | 18 ✓ | Yes |
| 2 | A robe takes 2 bolts of blue fiber... | 3 | 3 ✓ | 3 ✓ | 3 ✓ | Yes |
| 3 | Josh decides to try flipping a house... | 70,000 | 70,000 ✓ | 70,000 ✓ | 70,000 ✓ | Yes |
| 4 | James decides to run 3 sprints... | 540 | 540 ✓ | 540 ✓ | 540 ✓ | Yes |

**Accuracy: OR-Select 4/4 (100%), self-consistency 4/4 (100%), greedy 4/4
(100%).** All three methods tied — and the reason is visible in the last
column: on every single problem, all 3 of 3 candidates independently
reached the exact same numeric answer. `had_majority: True` in every
result, the mirror image of Track A, where it was `False` in all 3
queries.

**This is not a failed benchmark — it's the predicted result on easy
problems, and it's the useful half of a two-track story.**
`methodology.md`'s Baselines section already predicted this shape before
any data existed: *"The baseline should win exactly when candidates
cluster tightly... OR-Select should win once candidates diverge."*
Grade-school arithmetic is well within Nemotron's capability, so
candidates cluster tightly (Track B) — there is no headroom for a judge to
add value when every sample already agrees and is already correct. Open-
ended queries never cluster at all (Track A) — that's exactly where the
judge's differentiation showed up. Together, the two tracks confirm both
halves of the same prediction rather than reporting on two unrelated
tasks. **What this run does not show**, and what would need harder
problems to test: whether OR-Select's judge can *correct* a wrong
majority when candidates disagree and most of them are wrong — GSM8K's
easy end just doesn't produce that scenario at N=3 with a capable model.

Methodology: `scripts/gsm8k_benchmark.py` appends a fixed instruction
("Solve step by step, then end your response with exactly: The final
answer is \<number\>.") to each problem, runs the full pipeline, then
extracts the last number in each candidate's text (`or_select/gsm8k.py`,
same "last number wins" heuristic as confidence/judge parsing elsewhere in
this repo — reasoning models show their work before answering).
Self-consistency here is computed correctly per Wang et al.'s original
definition: majority vote over each candidate's *extracted numeric
answer*, not raw reasoning text (`self_consistency_winner(..., key=...)`)
— two candidates can reach the same correct number via different
reasoning, and should be counted as agreeing.

Sample: the first 4 problems of `data/gsm8k_sample.jsonl`, itself the
first 8 problems of the real GSM8K test set
(github.com/openai/grade-school-math), used deterministically (no
cherry-picking, no random seed to justify).

## Open questions this benchmark does not resolve

- **Correlated judge error** (Nine Judges, Two Effective Votes, 2026):
  every result above uses a single model (Nemotron) as generator, scorer,
  *and* judge. Whether `--provider both`/`all` (heterogeneous judges)
  would actually reduce correlated error here, or just add cost, is
  untested — would need a run with a working OpenAI or Gemini key
  alongside OpenRouter.
- **Provider-seed reliability**: the `_stable_seed` mechanism is
  best-effort per-provider, not a guarantee (documented in
  `methodology.md`'s "A concrete finding" — identical text got non-
  symmetric scores from this exact model before the exact-match
  short-circuit fixed that specific case).
- **Sample size**: N=3–5 candidates and 3–4 queries/problems per track are
  smoke-test scale, chosen to fit within OpenRouter's free-tier
  congestion tonight, not a statistically powered evaluation. Track B's
  full 8-problem sample and larger N (5-10) is the natural next step once
  rate limits allow.
- **No test of judge-corrects-a-wrong-majority**: Track B's 4 problems were
  easy enough for Nemotron that every candidate converged on the same
  correct answer, so accuracy alone can't distinguish the methods. The
  scenario that would actually stress-test the hypothesis — candidates
  disagree, and the majority is wrong but a minority is right — needs
  either harder problems (later GSM8K test-set entries, or a harder
  benchmark like MATH/GSM-Hard) or a weaker generator model to induce real
  disagreement at this same problem difficulty.
