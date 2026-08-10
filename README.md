# OR-Select: Deterministic Best-Answer Selection over Stochastic LLM Ensembles via Integer Programming

Run folder for a no-fine-tuning prototype that turns a distribution of N stochastic LLM
answers into one deterministic, auditable choice.

The LLM generation step stays probabilistic (temperature, sampling, seeds). Everything
downstream — scoring, pairwise comparison, aggregation, final pick — is a deterministic OR
pipeline: same N candidates in, same winner out, every time.

## Core Idea

1. Generate N candidate answers to the same query (same model/different seeds, or
   heterogeneous models).
2. Score each candidate (calibrated confidence / self-consistency).
3. Build a pairwise comparison matrix via an LLM judge, using permutation
   self-consistency (judge each pair both orders, average) to cancel position bias.
4. Solve a multi-objective integer program that selects exactly one winner:

```text
maximize   sum_i x_i * (w1*quality_i + w2*confidence_i - w3*cost_i)
subject to sum_i x_i = 1
           x_i in {0,1}
           quality_i >= min_quality   (optional gate)
```

5. Output = deterministic best answer, plus the scores that justify it.

Full formulation, including the pairwise Kemeny-style extension, is in
`docs/methodology.md`.

## Folder Map

```text
data/              example query/candidate sets
prompts/           generation and judge prompts
or_select/         active Python package
manuscript/        paper source and bibliography
docs/              methodology notes (formal model, math)
outputs/           generated run artifacts; safe to delete before a new run
```

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

5. Run a batch of queries.

```bash
python3 -m or_select.runner --input data/example_queries.jsonl --workers 3 --provider both
```

6. Compile paper.

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Run from `manuscript/`.

## Active Outputs

- `outputs/runs/<query_id>/candidates.json`
- `outputs/runs/<query_id>/pairwise_matrix.json`
- `outputs/runs/<query_id>/selection.json`

## Design Boundary

- No training, no fine-tuning.
- Generation stays probabilistic; only selection is required to be deterministic.
- Same candidate set + same judge outputs must always yield the same winner
  (solver determinism, not just "usually agrees").
- Judge position bias is treated as a first-class error source, not noise
  (permutation self-consistency is mandatory, not optional).
- Failed or malformed candidates remain explicit failures, never silently dropped.
