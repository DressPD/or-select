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

*Live run in progress — see `outputs/gsm8k_benchmark_initial.json` once
complete. This section will be filled in with the actual accuracy numbers
and a per-problem breakdown.*

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
