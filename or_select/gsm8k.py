"""GSM8K answer extraction and grading.

data/gsm8k_sample.jsonl is a small, deterministic sample of the real
GSM8K test set (github.com/openai/grade-school-math), used as a ground-
truth benchmark: unlike the open-ended queries elsewhere in this repo,
"OR-Select's winner is correct" is a checkable fact here, not a
subjective judgment call.
"""

from __future__ import annotations

import re

_NUMBER_RE = re.compile(r"[-+]?\d[\d,]*\.?\d*")

GSM8K_SUFFIX = (
    "\n\nSolve step by step, then end your response with exactly: "
    "The final answer is <number>."
)


def extract_answer(text: str) -> float | None:
    """Extract the final numeric answer from free text.

    Takes the LAST number in the text, matching the "last number wins"
    heuristic used for confidence/judge parsing elsewhere in this repo
    (providers.py's _parse_score): models reason before stating a final
    answer, so the first number in the text is often part of the problem
    restatement or an intermediate step, not the answer.
    """
    matches = _NUMBER_RE.findall(text)
    if not matches:
        return None
    try:
        return float(matches[-1].replace(",", ""))
    except ValueError:
        return None


def is_correct(predicted: float | None, ground_truth: float, tolerance: float = 1e-4) -> bool:
    if predicted is None:
        return False
    return abs(predicted - ground_truth) < tolerance
