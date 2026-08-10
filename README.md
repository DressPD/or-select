# OR-Select: Deterministic Best-Answer Selection over Stochastic LLM Ensembles via Integer Programming

Run folder for a no-fine-tuning prototype that turns a distribution of N stochastic LLM
answers into one deterministic, auditable choice.

The LLM generation step stays probabilistic (temperature, sampling, seeds). Everything
downstream — scoring, pairwise comparison, aggregation, final pick — is a deterministic OR
pipeline: same N candidates in, same winner out, every time.

## Core Idea

1. Generate N candidate answers to the same query (same model/different seeds, or
   heterogeneous models).
2. Score each candidate (calibrated confidence).
3. Build a pairwise comparison matrix via an LLM judge, using permutation
   self-consistency (judge each pair both orders, average) to cancel position bias.
   Byte-identical candidates skip the judge entirely (see "A concrete finding" in
   `docs/methodology.md` for why).
4. Compute a deterministic self-consistency signal from the candidate texts alone
   (zero API cost) — the classic self-consistency-voting baseline, expressed as one
   objective term rather than the whole decision rule.
5. Solve a multi-objective integer program that selects exactly one winner:

```text
maximize   sum_i x_i * (w1*quality_i + w2*confidence_i + w4*consistency_i - w3*cost_i)
subject to sum_i x_i = 1
           x_i in {0,1}
           quality_i >= min_quality   (optional gate)
```

6. Output = deterministic best answer, plus the scores that justify it.

Full formulation, including the pairwise Kemeny-style extension, is in
`docs/methodology.md`. Ablations (does the self-consistency term matter? does
bidirectional judging matter?) are in `docs/ablations.md`. Full benchmark
results (open-ended queries vs. baselines, GSM8K ground-truth accuracy) are in
`docs/benchmark_results.md`.

## Folder Map

```text
data/              example queries + a GSM8K ground-truth sample
prompts/           generation and judge prompts
or_select/         active Python package (pipeline, providers, selection, baselines)
scripts/           benchmark and ablation entry points (see below)
manuscript/        paper sources: main.tex (full technical report, elsarticle)
                   and judge2026_submission.tex (condensed, anonymized short
                   paper for JUDGe 2026 / NeurIPS workshop submission)
docs/              methodology, ablation results, benchmark results
outputs/           generated run artifacts; safe to delete before a new run
                   (gitignored)
tests/             unittest suite; offline tests run with zero API calls,
                   tests/test_providers.py auto-skips without live keys
```

### `or_select/` package

| Module | Role |
|---|---|
| `pipeline.py` | Orchestrates one query end to end; CLI entry point |
| `runner.py` | Batch pipeline over a JSONL file of queries; `--resume` skips already-completed ones |
| `generate.py` / `scoring.py` / `pairwise.py` / `consistency.py` / `selection.py` | The five pipeline stages |
| `providers.py` | Real backends: OpenAI, Gemini, OpenRouter — retry/backoff, stable seeding, fail-fast on permanent errors |
| `baselines.py` | Non-OR comparisons: self-consistency-alone, greedy-single-sample |
| `gsm8k.py` | Ground-truth benchmark support: answer extraction, grading |

### `scripts/`

| Script | What it does |
|---|---|
| `gsm8k_benchmark.py` | Grades OR-Select vs. baselines against GSM8K ground truth; `--resume` supported |
| `compare_baselines.py` | Compares OR-Select's winner against baselines on an existing `selection.json` |
| `ablation_consistency.py` | Offline: does the self-consistency term ever change the winner? |
| `ablation_permutation.py` | Live: does bidirectional (vs. forward-only) judging change the winner? |

## Run Pipeline

1. Put LLM API credentials in `.env` (copy `.env.example`; `.env` is gitignored).

```bash
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=...
```

2. Install provider SDKs (not needed for the placeholder backend).

```bash
pip install -r requirements.txt
```

3. Run the toy example end-to-end with the deterministic placeholder backend
   (no API keys required — validates the OR core in isolation).

```bash
python3 -m or_select.pipeline --query "What is the capital of France?" --n 10
```

4. Run against a real provider, or heterogeneously across both to validate
   the research claim (deterministic selection holds regardless of which
   models generated the candidates).

```bash
python3 -m or_select.pipeline --query "..." --n 10 --provider openai
python3 -m or_select.pipeline --query "..." --n 10 --provider gemini
python3 -m or_select.pipeline --query "..." --n 10 --provider openrouter
python3 -m or_select.pipeline --query "..." --n 10 --provider both
```

5. Run a batch of queries (`--resume` skips queries that already have a saved result).

```bash
python3 -m or_select.runner --input data/example_queries.jsonl --workers 3 --provider openrouter --resume
```

6. Run the GSM8K ground-truth benchmark, or the ablations.

```bash
python3 scripts/gsm8k_benchmark.py --provider openrouter --n 3 --limit 8 --resume
python3 scripts/ablation_consistency.py outputs/runs/*/selection.json
python3 scripts/ablation_permutation.py outputs/runs/*/selection.json --provider openrouter
```

7. Run the test suite (offline; live-provider tests auto-skip without keys set).

```bash
python3 -m unittest discover -s tests
```

8. Compile a manuscript. Run from `manuscript/`.

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex                    # full technical report
latexmk -pdf -interaction=nonstopmode -halt-on-error judge2026_submission.tex    # condensed workshop short paper
```

`judge2026_submission.tex` needs the official `neurips_2026.sty` swapped in before
actual submission — see the note at the top of the file.

## Active Outputs

- `outputs/runs/<query_id>/selection.json` — full candidate set, scores, and winner for one query
- `outputs/gsm8k_benchmark*.json` — per-problem grading + accuracy for the GSM8K benchmark
- `outputs/ablation_*.json` — ablation results

## Reproducibility notes

- Live results in `docs/benchmark_results.md` and `docs/ablations.md` used a single
  free-tier model (OpenRouter, `nvidia/nemotron-3-ultra-550b-a55b:free`) as generator,
  scorer, and judge throughout — OpenAI and Gemini were configured but unavailable
  during that work (no credits / daily quota exhausted respectively).
- Free-tier rate limits are real and severe: observed upstream queue depths up to
  3517 against a 32-request provider-side limit. `providers.py` retries with backoff;
  `runner.py`/`gsm8k_benchmark.py` checkpoint incrementally so a killed run can
  `--resume` without redoing completed work.
- `docs/ablations.md` documents a data-hygiene bug we found and fixed mid-project:
  two early smoke-test result files predated the exact-match short-circuit and the
  self-consistency term, and including them in an ablation glob silently mixed
  pre-fix and post-fix scoring semantics. Both ablations were corrected to use only
  post-fix data; see that doc for the full account.

## Design Boundary

- No training, no fine-tuning.
- Generation stays probabilistic; only selection is required to be deterministic.
- Same candidate set + same judge outputs must always yield the same winner
  (solver determinism, not just "usually agrees").
- Judge position bias is treated as a first-class error source, not noise
  (permutation self-consistency is mandatory, not optional).
- Failed or malformed candidates remain explicit failures, never silently dropped.

## License

MIT — see `LICENSE`.
