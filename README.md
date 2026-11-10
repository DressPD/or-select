# OR-Select: Reproducible Best-of-N Answer Selection over LLM Ensembles

A no-fine-tuning pipeline that turns N stochastic LLM answers into one auditable choice, plus the audit protocol and
theory used to test whether the choice is *accurate*. Selection is cast as an integer program over a judge-derived
pairwise matrix and a text-agreement term. Stored inputs support offline replay in a fixed solver environment.
The paper (`manuscript/main.tex`) reports a ground-truth audit against self-consistency and an integerized
Kemeny-Young reference, and an exact finite-pool analysis of a specified binary judge/Copeland rule against plurality.

Generation, confidence scoring and live pairwise judging can all vary. The aggregation is fixed given stored
inputs; cross-version canonical solver tie-breaking is not implemented. Soft preference weights in the audit
are not the Bernoulli comparison accuracy in the theorem.

## Pipeline

1. **Generate** N candidates (one model with distinct seeds, or round-robin over several models).
2. **Score** each candidate (confidence in [0, 1], cost = word count).
3. **Compare** every pair with an LLM judge in both orders and average (permutation self-consistency); identical stripped-text
   candidates skip the judge and get 0.5.
4. **Self-consistency** from the candidate texts alone (zero API cost).
5. **Select** exactly one winner by solving, with CP-SAT:

```text
maximize   sum_i x_i * (w1*quality_i + w2*confidence_i + w4*consistency_i - w3*cost_i)
subject to sum_i x_i = 1,  x_i in {0,1}
           x_i = 0 if quality_i < min_quality (optional selected-candidate gate)
```

`quality_i = mean_{j != i} W[i, j]` is the weighted-win aggregate. Invalid extracted answers are ineligible when
at least one valid answer exists. CP-SAT maximizes coefficients rounded after multiplication by 10,000; the
one-hot problem is an argmax. The Kemeny reference separately maximizes integerized ranking agreement and
returns an optimality flag. The inherited 5-approximation concerns the full weighted-win ranking's
disagreement, not top-answer correctness or the composite objective. See `docs/methodology.md`.

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
| `baselines.py` | Self-consistency and first-sampled-answer baselines (legacy key: `greedy`) |
| `gsm8k.py`, `math_eval.py`, `gpqa.py`, `mmlu_pro.py`, `reward_bench.py` | Answer extraction and grading per benchmark |
| `rejudge.py`, `extended.py` | Re-judging stale rows; the flagged higher-token-cap second pass |
| `runner.py`, `core.py` | Batch runner; shared types |

### `scripts/`

| Script | Role |
|---|---|
| `gsm8k_benchmark.py`, `math_benchmark.py` (MATH Level 5, AIME), `gpqa_benchmark.py`, `mmlu_pro_benchmark.py`, `reward_bench_benchmark.py` | Run a track; `--resume`, `--retry-failures`, `--extended-cap`, `--no-rejudge` |
| `fetch_*_sample.py` | Build `data/*.jsonl` (GSM8K sample is committed; GPQA is fetched locally) |
| `create_results_macros.py`, `analyze_selection.py`, `ablation_weights_offline.py`, `baselines_extra_offline.py` | Offline analyses that write the manuscript's `*_data.tex` |
| `judge_threshold_theory.py`, `judge_threshold_general.py`, `judge_threshold_extensions.py`, `judge_threshold_empirical.py` | Binary threshold theory and separate empirical soft-score/collision diagnostics |
| `create_manuscript_tables.py`, `rewardbench_bias_check.py` | Worked example; RewardBench length diagnostic |
| `ablation_consistency.py`, `ablation_permutation.py`, `compare_baselines.py` | Pilot-run ablations and baseline comparison on `outputs/runs/` |

## Run

```bash
cp -n .env.example .env         # keep existing credentials; add only the keys needed
python3 -m pip install --no-input -r requirements.txt

python3 -m or_select.pipeline --query "What is the capital of France?" --n 5     # placeholder backend, no keys
python3 -m or_select.pipeline --query "..." --n 5 --provider openrouter          # real backend
python3 scripts/gsm8k_benchmark.py --provider openrouter --n 3 --limit 8 --resume
```

Providers: `placeholder`, `openai`, `gemini`, `openrouter`, `both`, `openrouter_mixed` (three-vendor heterogeneous pool).
Per-track commands are in `docs/benchmark_results.md`.

## Reproduce the paper

```bash
python3 scripts/create_results_macros.py
python3 scripts/analyze_selection.py
python3 scripts/ablation_weights_offline.py
python3 scripts/baselines_extra_offline.py
python3 scripts/judge_threshold_theory.py
python3 scripts/judge_threshold_general.py
python3 scripts/judge_threshold_extensions.py
python3 scripts/judge_threshold_empirical.py
python3 scripts/create_manuscript_tables.py
```

These commands make zero API calls, but overwrite generated tables and skip missing tracks. Full paper-table
regeneration requires the original local GPQA files; a public checkout alone cannot reproduce those rows.
See `docs/benchmark_results.md` for inputs and the distinction between replay and a new live run.

For TeX prerequisites and the complete build sequence, including bibliography and cross-document passes,
see [submission files and build instructions](docs/submission_files.md). Offline tests: run each
`tests/test_*.py` module except `tests/test_providers.py`, which makes live API calls.

## Data

- `outputs/*.json` hold candidate and grading records. Only the stored-judgment subset supports alternate-weight
  replay. The weight-ablation fidelity check compares extracted final answers, not exact candidate identities.
  All tracks except GPQA Diamond are tracked in this repository.
- GPQA outputs embed the question text. GPQA is distributed password-gated to deter contamination, so those files are not
  published here. The fetch/benchmark scripts make new runs, not an exact replay of the original stochastic outputs.
  The GPQA rows of the manuscript tables require the original local files and applicable benchmark access.
- Free-tier rate limits are real: runs checkpoint after every problem and `--resume` continues them.

## Design boundary

- No training or fine-tuning; replay assumes fixed inputs, input order and solver environment.
- Order averaging mitigates order sensitivity; it does not remove every positional or content-dependent bias.
- Failed or malformed candidates remain explicit failures, never silently dropped; coverage is reported as graded/total.

## License

MIT, see `LICENSE`, for the code.

Data sources and licences: the small samples in `data/` are subsets of public benchmarks (GSM8K, MATH,
MATH-500, AIME 2025 and 2026 via MathArena, MMLU-Pro, RewardBench). Each sample keeps the licence and terms of its
original source, which govern its reuse; check them before redistributing. GPQA Diamond is not redistributed
(password-gated upstream); `scripts/fetch_gpqa_sample.py` regenerates it locally.

To cite the software and data, see `CITATION.cff`.

## Release and manuscript status

`CITATION.cff` and DOI `10.5281/zenodo.24112045` identify the published **v1.0.0** archive, not every later working-tree
revision. Local manuscript changes do not update that immutable archive or the remote repository automatically.
Current submission inventory: `docs/submission_files.md`. Online prior-art comparison and internal publication
assessment: `docs/novelty_audit.md`. Historical preregistrations and stored run files remain unchanged.

Citation coverage and source policy: [citation audit](docs/citation_audit.md).
A new **v1.1.0** archive is recommended before submission; see the
[release decision and prerequisites](docs/release_decision.md). A git push alone is not a new release.
