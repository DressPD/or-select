# OR-Select: Reproducible Best-of-N Answer Selection over LLM Ensembles

A no-fine-tuning pipeline that turns N stochastic LLM answers into one auditable choice, plus the audit protocol and
theory used to test whether the choice is *accurate*. Selection is cast as an integer program over a judge-derived
pairwise matrix and a deterministic self-consistency term; given the stored judge outputs the winner is exactly
reproducible. The paper (`manuscript/main.tex`) reports a ground-truth audit against self-consistency and an exact
Kemeny-Young reference, and a closed-form analysis of when a pairwise judge can beat plurality voting.

Generation stays probabilistic. Everything after it (pairwise comparison, aggregation, final pick) is deterministic
given the candidates and the judge's outputs.

## Pipeline

1. **Generate** N candidates (one model with distinct seeds, or round-robin over several models).
2. **Score** each candidate (confidence in [0, 1], cost = word count).
3. **Compare** every pair with an LLM judge in both orders and average (permutation self-consistency); byte-identical
   candidates skip the judge and get 0.5.
4. **Self-consistency** from the candidate texts alone (zero API cost).
5. **Select** exactly one winner by solving, with CP-SAT:

```text
maximize   sum_i x_i * (w1*quality_i + w2*confidence_i + w4*consistency_i - w3*cost_i)
subject to sum_i x_i = 1,  x_i in {0,1},  quality_i >= min_quality (optional)
```

`quality_i = mean_j W[i, j]` is the Copeland-style aggregate of the pairwise matrix; the exact Kemeny-Young ranking
(`or_select/kemeny.py`) is computed as a reference. See `docs/methodology.md`.

## Layout

```text
or_select/    pipeline, providers, selection, Kemeny reference, benchmark graders, rejudge/extended-cap helpers
scripts/      benchmark runners, offline analyses that generate the manuscript numbers, data fetchers
data/         benchmark samples (GPQA Diamond is fetched locally, never committed)
prompts/      generation and judge prompts
docs/         methodology, ablations, results index, pre-registrations (historical), review notes, target journals
manuscript/   main.tex (elsarticle) and supplement.tex (online supplement), figures, generated *_data.tex macro files, submission documents
outputs/      stored run files (benchmark JSON); GPQA files are not published, see "Data" below
tests/        unittest suite
```

### `or_select/`

| Module | Role |
|---|---|
| `pipeline.py` | One query end to end; provider selection; CLI |
| `generate.py`, `scoring.py`, `pairwise.py`, `consistency.py`, `selection.py` | The pipeline stages |
| `kemeny.py` | Exact Kemeny-Young ranking (CP-SAT, deterministic conflict budget) |
| `providers.py` | OpenAI, Gemini, OpenRouter backends with retry, stable seeds, stall timeouts, per-model output caps |
| `baselines.py` | Self-consistency and greedy baselines |
| `gsm8k.py`, `math_eval.py`, `gpqa.py`, `mmlu_pro.py`, `reward_bench.py` | Answer extraction and grading per benchmark |
| `rejudge.py`, `extended.py` | Re-judging stale rows; the flagged higher-token-cap second pass |
| `runner.py`, `core.py` | Batch runner; shared types |

### `scripts/`

| Script | Role |
|---|---|
| `gsm8k_benchmark.py`, `math_benchmark.py` (MATH Level 5, AIME), `gpqa_benchmark.py`, `mmlu_pro_benchmark.py`, `reward_bench_benchmark.py` | Run a track; `--resume`, `--retry-failures`, `--extended-cap`, `--no-rejudge` |
| `fetch_*_sample.py` | Build `data/*.jsonl` (GSM8K sample is committed; GPQA is fetched locally) |
| `create_results_macros.py`, `analyze_selection.py`, `ablation_weights_offline.py`, `baselines_extra_offline.py` | Offline analyses that write the manuscript's `*_data.tex` |
| `judge_threshold_theory.py`, `judge_threshold_general.py`, `judge_threshold_extensions.py`, `judge_threshold_empirical.py` | Threshold theory: closed form, general N, large-N bound, measured accuracy |
| `create_manuscript_tables.py`, `rewardbench_bias_check.py` | Worked example; RewardBench length diagnostic |
| `ablation_consistency.py`, `ablation_permutation.py`, `compare_baselines.py` | Pilot-run ablations and baseline comparison on `outputs/runs/` |

## Run

```bash
cp .env.example .env            # add OPENAI_API_KEY / GOOGLE_API_KEY / OPENROUTER_API_KEY as needed
pip install -r requirements.txt

python3 -m or_select.pipeline --query "What is the capital of France?" --n 5     # placeholder backend, no keys
python3 -m or_select.pipeline --query "..." --n 5 --provider openrouter          # real backend
python3 scripts/gsm8k_benchmark.py --provider openrouter --n 3 --limit 8 --resume
```

Providers: `placeholder`, `openai`, `gemini`, `openrouter`, `both`, `openrouter_mixed` (three-vendor heterogeneous pool).
Per-track commands are in `docs/benchmark_results.md`.

## Reproduce the paper

```bash
python3 scripts/create_results_macros.py && python3 scripts/analyze_selection.py \
  && python3 scripts/ablation_weights_offline.py && python3 scripts/baselines_extra_offline.py \
  && python3 scripts/judge_threshold_theory.py && python3 scripts/judge_threshold_general.py \
  && python3 scripts/judge_threshold_extensions.py && python3 scripts/judge_threshold_empirical.py
cd manuscript && for t in supplement main main; do pdflatex -interaction=nonstopmode -halt-on-error $t.tex; done  # plus bibtex main && bibtex supplement; the two documents cross-reference each other
```

Zero API calls; tracks with a missing output file are skipped. Tests (offline): `python3 -m unittest tests.test_<name>`
for each module except `tests/test_providers.py`, which needs live keys.

## Data

- `outputs/*.json` hold every candidate, the judge's confidences and pairwise matrices, and the graded results, so any
  selection can be replayed exactly. All tracks except GPQA Diamond are tracked in this repository.
- GPQA outputs embed the question text. GPQA is distributed password-gated to deter contamination, so those files are not
  published here; regenerate them with `scripts/fetch_gpqa_sample.py` and `scripts/gpqa_benchmark.py`, or contact the author.
  The GPQA rows of the manuscript tables need those local files.
- Free-tier rate limits are real: runs checkpoint after every problem and `--resume` continues them.

## Design boundary

- No training or fine-tuning; generation is probabilistic, selection is deterministic given fixed judge outputs.
- Judge position bias is a first-class error source (permutation self-consistency is mandatory).
- Failed or malformed candidates remain explicit failures, never silently dropped; coverage is reported as graded/total.

## License

MIT, see `LICENSE`, for the code.

Data sources and licences: the small samples in `data/` are subsets of public benchmarks (GSM8K, MATH,
MATH-500, AIME 2025 and 2026 via MathArena, MMLU-Pro, RewardBench). Each sample keeps the licence and terms of its
original source, which govern its reuse; check them before redistributing. GPQA Diamond is not redistributed
(password-gated upstream); `scripts/fetch_gpqa_sample.py` regenerates it locally.

To cite the software and data, see `CITATION.cff`.
