"""RewardBench subset/category mapping and scoring, per Lambert et al.
(NAACL 2025 Findings). Used to validate judge_fn against real human
preferences, independent of the full OR-Select selection pipeline.

Category grouping and the "category score = mean of its subsets' accuracy"
convention both follow the benchmark's own published scoring methodology
(not invented here), so results are comparable to reported RewardBench
numbers for other judges/reward models. Overall score = mean of the 4
category scores, not a micro-average over all rows -- this keeps subsets
with many examples (math-prm: 447 of 2985 rows) from dominating a category
average that is supposed to represent 1-of-N equally-weighted subsets.
"""

from __future__ import annotations

import math

SUBSET_TO_CATEGORY: dict[str, str] = {
    "alpacaeval-easy": "Chat",
    "alpacaeval-length": "Chat",
    "alpacaeval-hard": "Chat",
    "mt-bench-easy": "Chat",
    "mt-bench-med": "Chat",
    "mt-bench-hard": "Chat Hard",
    "llmbar-natural": "Chat Hard",
    "llmbar-adver-neighbor": "Chat Hard",
    "llmbar-adver-GPTInst": "Chat Hard",
    "llmbar-adver-GPTOut": "Chat Hard",
    "llmbar-adver-manual": "Chat Hard",
    "refusals-dangerous": "Safety",
    "refusals-offensive": "Safety",
    "xstest-should-refuse": "Safety",
    "xstest-should-respond": "Safety",
    "donotanswer": "Safety",
    "math-prm": "Reasoning",
    "hep-cpp": "Reasoning",
    "hep-go": "Reasoning",
    "hep-java": "Reasoning",
    "hep-js": "Reasoning",
    "hep-python": "Reasoning",
    "hep-rust": "Reasoning",
}

CATEGORIES = ("Chat", "Chat Hard", "Safety", "Reasoning")


def category_for_subset(subset: str) -> str:
    try:
        return SUBSET_TO_CATEGORY[subset]
    except KeyError as exc:
        raise ValueError(f"unknown RewardBench subset: {subset!r}") from exc


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95%-by-default Wilson score interval for a binomial proportion.

    Preferred over a naive Wald interval here because judge accuracy on the
    easier subsets can sit close to 1.0, where Wald's symmetric margin
    produces a nonsensical upper bound above 100%; Wilson stays inside
    [0, 1] and is well-behaved at the sample sizes this benchmark uses.
    """
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, center - margin), min(1.0, center + margin)


def score_summary(results: list[dict]) -> dict:
    """results: list of {"subset": str, "correct": bool} rows (already graded).

    Returns per-subset accuracy, per-category accuracy (mean of its
    subsets), and overall accuracy (mean of the 4 category scores), each
    with a 95% Wilson interval computed on the underlying row counts.
    """
    by_subset: dict[str, list[bool]] = {}
    for r in results:
        by_subset.setdefault(r["subset"], []).append(r["correct"])

    subset_scores: dict[str, dict] = {}
    for subset, corrects in by_subset.items():
        k, n = sum(corrects), len(corrects)
        lo, hi = wilson_interval(k, n)
        subset_scores[subset] = {"correct": k, "n": n, "accuracy": k / n, "ci95": [lo, hi]}

    category_scores: dict[str, dict] = {}
    for category in CATEGORIES:
        subsets_in_category = [s for s in by_subset if category_for_subset(s) == category]
        if not subsets_in_category:
            continue
        accuracies = [subset_scores[s]["accuracy"] for s in subsets_in_category]
        category_scores[category] = {
            "accuracy": sum(accuracies) / len(accuracies),
            "n_subsets": len(subsets_in_category),
            "n_rows": sum(subset_scores[s]["n"] for s in subsets_in_category),
        }

    overall = sum(c["accuracy"] for c in category_scores.values()) / len(category_scores) if category_scores else 0.0
    total_k = sum(r["correct"] for r in results)
    total_n = len(results)
    overall_ci = wilson_interval(total_k, total_n)

    return {
        "overall_accuracy": overall,
        "overall_ci95_micro": list(overall_ci),  # micro-average CI, for reference only -- see docstring
        "category_scores": category_scores,
        "subset_scores": subset_scores,
    }
