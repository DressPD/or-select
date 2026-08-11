"""MATH (Level 5) answer extraction and grading.

data/math_level5_sample.jsonl is the full Level-5 subset (134 problems) of
MATH-500 (Lightman et al., "Let's Verify Step by Step", 2023), a public,
widely-used 500-problem sample of the Hendrycks MATH test set, fetched via
the Hugging Face datasets-server API (HuggingFaceH4/MATH-500). Unlike
GSM8K -- saturated for the model used in this repo, see
docs/hypothesis_validation.md sub-claim 5 -- Level-5 MATH problems are
harder competition-style problems (algebra, number theory, geometry,
combinatorics) chosen specifically because agreement/correctness is a
weaker signal for strong models on this difficulty tier
(Ding, 2026; Wang et al., 2023's own MATH-vs-GSM8K comparison).

Grading MATH answers is harder than GSM8K's "last number in the text":
answers are LaTeX expressions (fractions, coordinates, symbolic terms,
intervals), not just numbers. This module implements a heuristic string
normalizer, not a full computer-algebra equivalence checker -- it will
mark some correct-but-differently-formatted answers as wrong (e.g. an
un-simplified fraction). This is a known limitation, not an oversight;
see docs/hypothesis_validation.md.
"""

from __future__ import annotations

import re

MATH_SUFFIX = (
    "\n\nSolve step by step, then end your response with the final answer "
    "in a LaTeX \\boxed{} expression, e.g. \\boxed{42} or \\boxed{\\frac{1}{2}}."
)

_WHITESPACE_RE = re.compile(r"\s+")
_LATEX_SPACING_RE = re.compile(r"\\[!,;:]")
_TEXT_WRAP_RE = re.compile(r"\\text\{([^{}]*)\}")
_LEFT_RIGHT_RE = re.compile(r"\\left|\\right")
_DOLLAR_RE = re.compile(r"\$")
_TRAILING_PERIOD_RE = re.compile(r"\.$")


def extract_boxed(text: str) -> str | None:
    """Extract the contents of the LAST \\boxed{...} in text, handling
    nested braces (regex alone can't balance them, e.g. \\boxed{\\frac{1}{2}}).
    Falls back to None if no \\boxed{} is present -- callers should treat
    that as an ungraded/failed extraction, not silently guess.
    """
    marker = "\\boxed{"
    start = text.rfind(marker)
    if start == -1:
        return None
    i = start + len(marker)
    depth = 1
    content_start = i
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    if depth != 0:
        return None  # unbalanced braces -- truncated/malformed output
    return text[content_start : i - 1].strip()


def normalize(expr: str) -> str:
    """Canonicalize a LaTeX math expression for string comparison.

    Strips formatting that doesn't change meaning (spacing commands,
    \\left/\\right, $ delimiters, \\text{} wrappers, \\dfrac/\\tfrac ->
    \\frac, trailing period, all whitespace) so that e.g.
    "\\dfrac{1}{2}" and "\\frac{1}{2}" compare equal. Does not attempt
    algebraic simplification (e.g. "2/4" vs "1/2" are NOT normalized to
    equal) -- see module docstring.
    """
    s = expr.strip()
    s = _DOLLAR_RE.sub("", s)
    s = _LEFT_RIGHT_RE.sub("", s)
    s = _LATEX_SPACING_RE.sub("", s)
    s = _TEXT_WRAP_RE.sub(r"\1", s)
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = s.replace("\\!", "").replace("\\,", "")
    s = s.replace("^\\circ", "").replace("^{\\circ}", "")
    s = _WHITESPACE_RE.sub("", s)
    s = _TRAILING_PERIOD_RE.sub("", s)
    return s.lower()


def is_correct(predicted: str | None, ground_truth: str) -> bool:
    if predicted is None:
        return False
    return normalize(predicted) == normalize(ground_truth)
