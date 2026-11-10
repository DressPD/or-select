"""MMLU-Pro answer extraction and grading.

data/mmlu_pro_sample.jsonl is a deterministic, evenly spaced 100-question sample of the MMLU-Pro
test split (Wang et al., "MMLU-Pro: A More Robust and Challenging Multi-Task Language
Understanding Benchmark", NeurIPS 2024 Datasets and Benchmarks, arXiv:2406.01574): up to ten answer
options (A-J) per question across 14 subjects (the sample covers 12), built to be harder and less guessable than MMLU.

Same contract as or_select.gpqa, with a wider letter range. One difference is deliberate: the
letter class is case-sensitive, so the prose fallback "the answer is a function ..." can never be
read as option A; only an upper-case option letter counts.
"""

from __future__ import annotations

import re

MMLU_PRO_SUFFIX = (
    "\n\nThink it through, then end your response on its own line in the "
    "exact form: ANSWER: X -- where X is the single upper-case letter (A through J) "
    "of the correct option. Keep your reasoning concise and decisive, and reach the "
    "ANSWER line well before you run out of space."
)

_ANSWER_RE = re.compile(r"(?i:answer):\s*\(?([A-J])\)?(?![A-Za-z])")
_BOXED_RE = re.compile(r"\\boxed\{\(?([A-J])\)?\}")
_ANSWER_PHRASE_RE = re.compile(r"(?i:answer)\s+is\s*:?\s*\(?([A-J])\)?(?![A-Za-z])")
_LAST_LINE_LETTER_RE = re.compile(r"^\(?([A-J])\)?\.?$")


def format_question(question: str, options: list[str]) -> str:
    """Question stem followed by lettered options, one per line."""
    lettered = "\n".join(f"{chr(ord('A') + i)}. {o}" for i, o in enumerate(options))
    return f"{question.strip()}\n\n{lettered}"


def extract_choice(text: str) -> str | None:
    """The model's chosen option letter (A-J), or None (an explicit ungraded failure, never a guess)."""
    for pattern in (_ANSWER_RE, _BOXED_RE, _ANSWER_PHRASE_RE):
        found = pattern.findall(text)
        if found:
            return found[-1]
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        m = _LAST_LINE_LETTER_RE.match(line)
        return m.group(1) if m else None
    return None


def is_correct(predicted: str | None, ground_truth: str) -> bool:
    if predicted is None:
        return False
    return predicted.strip().upper() == ground_truth.strip().upper()
