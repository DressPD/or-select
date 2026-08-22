"""GPQA Diamond answer extraction and grading.

data/gpqa_diamond_sample.jsonl is the full Diamond subset (198 problems) of
GPQA (Rein et al., "GPQA: A Graduate-Level Google-Proof Q&A Benchmark",
COLM 2024, arXiv:2311.12022) -- graduate-level, PhD-written multiple-choice
questions in biology, physics, and chemistry, explicitly designed (canary
string, password-gated release) to resist both search-engine lookup and
training-data contamination. Chosen as a second unsaturated-benchmark test
of hypothesis sub-claim 5 alongside AIME 2026
(docs/gpqa_diamond_preregistration.md): Ding (2026, cited throughout this
repo) used GPQA Diamond specifically because it's where the literature
documents frontier models converging confidently on *wrong* answers, the
exact precondition sub-claim 5 needs and that MATH Level 5/AIME never
produced.

Unlike MATH's free-form LaTeX answers, GPQA is 4-way multiple choice: one
correct answer plus three incorrect distractors, shuffled once per problem
into a fixed A/B/C/D order by scripts/fetch_gpqa_sample.py so all N
candidates for a given problem see the identical option mapping. Grading is
exact-letter-match -- unlike or_select.math_eval's heuristic LaTeX
normalizer, there is no formatting ambiguity to introduce grader false
negatives.
"""

from __future__ import annotations

import re

GPQA_SUFFIX = (
    "\n\nThink it through, then end your response on its own line in the "
    "exact form: ANSWER: X -- where X is the single letter (A, B, C, or D) "
    "of the correct option."
)

_ANSWER_RE = re.compile(r"ANSWER:\s*\(?([A-D])\)?", re.IGNORECASE)
_LAST_LINE_LETTER_RE = re.compile(r"^\(?([A-D])\)?\.?$", re.IGNORECASE)


def extract_choice(text: str) -> str | None:
    """Extract the model's chosen option letter (A-D).

    Prefers the last `ANSWER: X` marker (the format requested by
    GPQA_SUFFIX). Falls back to the last non-empty line if it is *nothing
    but* a bare letter (e.g. a model that answers "B" on its own line
    without the requested prefix) -- deliberately not a bare `\bA\b`-style
    scan over the full response, which would false-positive on stray
    single-letter tokens inside the reasoning (variable names, "a" as an
    article, etc.). Returns None -- an explicit ungraded failure, never a
    guess -- if neither pattern is found.
    """
    matches = _ANSWER_RE.findall(text)
    if matches:
        return matches[-1].upper()
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        m = _LAST_LINE_LETTER_RE.match(line)
        return m.group(1).upper() if m else None
    return None


def is_correct(predicted: str | None, ground_truth: str) -> bool:
    if predicted is None:
        return False
    return predicted.strip().upper() == ground_truth.strip().upper()
