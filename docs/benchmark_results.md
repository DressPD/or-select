# Benchmark results

The results, tables and interpretation live in the manuscript (`manuscript/main.tex`, Results section). Every number there is
generated from the stored run files in `outputs/` by the scripts below; this page only says what the tracks are, where the
files are, and how to regenerate everything. Nothing here is a second copy of a result, so it cannot go stale.

## Tracks

| Track | Task | Generation | Output file |
|---|---|---|---|
| A | 3 open-ended queries, no ground truth (pilot illustration only) | N=5 homogeneous | `outputs/runs/<query_id>/selection.json` |
| B | GSM8K, first 40 test problems | N=3 homogeneous; N=6 heterogeneous | `gsm8k_benchmark_initial.json`, `gsm8k_benchmark_heterogeneous.json` |
| C | MATH Level 5 (134 problems of MATH-500) | N=3; N=6 | `math_benchmark_full.json`, `math_benchmark_heterogeneous.json` |
| D | AIME 2026 (30 problems) | N=3; N=6 | `aime_2026_benchmark.json`, `aime_2026_heterogeneous.json` |
| E | GPQA Diamond (198 questions) | N=3; N=6 | `gpqa_benchmark.json`, `gpqa_heterogeneous.json` |
| F | AIME 2025 (30 problems), robustness check | N=3 | `aime_2025_benchmark.json` |
| G | MMLU-Pro (100-question sample, up to 10 options) | N=3 | `mmlu_pro_benchmark.json` |
| RB | RewardBench judge validation (161 rows) | judge only | `reward_bench_benchmark.json`, `reward_bench_benchmark_heterogeneous.json` |

Methods compared: OR-Select (`or_select/pipeline.py`), self-consistency (plurality over extracted answers), first sampled
answer (legacy key `greedy`, not temperature-zero decoding) and the integerized Kemeny-Young winner (`or_select/kemeny.py`); further selectors are replayed offline
(`scripts/baselines_extra_offline.py`). Candidates come from `nvidia/nemotron-3.5-lightning:free` (homogeneous) or from
that model, `xingchen-agi/xing4.0-29b-a4b:free` and `cohere/north-mini-code:free` (heterogeneous; early heterogeneous rows
still contain `poolside/laguna-s-2.1:free`, withdrawn by the provider, and are reported as such). The judge is always the
Nemotron model.

## Regenerating the manuscript numbers (zero API calls)

```bash
python3 scripts/create_results_macros.py        # Results_data.tex: tracks, paired tests, coverage, RewardBench
python3 scripts/analyze_selection.py            # Selection_data.tex: recovery, pick shares
python3 scripts/ablation_weights_offline.py     # Ablation_data.tex: weight ablations by replay
python3 scripts/baselines_extra_offline.py      # Baselines_data.tex: additional selectors
python3 scripts/judge_threshold_theory.py       # Theory_data.tex: binary N=3 threshold and descriptive soft weights
python3 scripts/judge_threshold_general.py      # ThresholdGeneral_data.tex: general N, correlated wrong answers
python3 scripts/judge_threshold_extensions.py   # ThresholdExt_data.tex: N=7, wrong-answer structure, large-N bound, cost
python3 scripts/judge_threshold_empirical.py    # ThresholdEmpiricalGeneral_data.tex: model sensitivity at estimated collisions
python3 scripts/create_manuscript_tables.py     # Figure_3_WorkedExample_data.tex (needs outputs/runs/)
```

Run each from the repository root. Tracks whose output file is missing are skipped.
The two GPQA files are local-only; without the original files, these commands do
not reproduce all published rows. New live GPQA runs are not exact replay.
The empirical soft weights are descriptive, not Bernoulli accuracies that certify
the theorem. Only uncertainty in the collision estimate is bootstrapped there.

## Running a track

```bash
python3 scripts/gsm8k_benchmark.py     --provider openrouter --n 3 --output outputs/gsm8k_benchmark_initial.json --resume
python3 scripts/math_benchmark.py      --provider openrouter --n 3 --input data/math_level5_sample.jsonl --output outputs/math_benchmark_full.json --resume
python3 scripts/math_benchmark.py      --provider openrouter --n 3 --input data/aime_2026_sample.jsonl --output outputs/aime_2026_benchmark.json --resume
python3 scripts/gpqa_benchmark.py      --provider openrouter --n 3 --output outputs/gpqa_benchmark.json --resume   # needs scripts/fetch_gpqa_sample.py first
python3 scripts/mmlu_pro_benchmark.py  --provider openrouter --n 3 --output outputs/mmlu_pro_benchmark.json --resume
python3 scripts/reward_bench_benchmark.py --provider openrouter
```

Useful flags: `--resume` skips completed rows; `--retry-failures` re-attempts rows that ended in an infrastructure error;
`--extended-cap 65536` runs the flagged higher-token-cap second pass on rows truncated at the main cap; `--no-rejudge` stops
`--resume` from re-judging stored candidates. Heterogeneous runs use `--provider openrouter_mixed`; see each script's `--help`.
A finished heterogeneous row is never re-slotted or re-run.

## Pilot (Track A)

Three open-ended queries (N=5, no ground truth) check that the pipeline behaves where self-consistency has nothing to vote
on: across the 15 candidates none was byte-identical to another, so self-consistency fell back to an arbitrary tie-break
every time and OR-Select differed from both baselines on all three queries (score margins 0.088, 0.446 and a near-tie of
0.003). With three queries and no ground truth this illustrates the mechanics; it is not evidence about selection quality.
