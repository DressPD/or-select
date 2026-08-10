"""Compare OR-Select's winner against non-OR baselines on an existing run.

    python3 scripts/compare_baselines.py outputs/runs/<query_id>/selection.json

Reads a selection.json already written by or_select.pipeline/runner and
recomputes the self-consistency and greedy-single-sample baselines from
the same candidate set -- no new API calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from or_select.baselines import greedy_single_sample, self_consistency_winner  # noqa: E402
from or_select.core import Candidate  # noqa: E402


def _load_candidates(path: Path) -> tuple[str, dict, list[Candidate]]:
    payload = json.loads(path.read_text())
    candidates = [
        Candidate(
            id=c["id"],
            text=c["text"],
            source_model=c["source_model"],
            confidence=c["confidence"],
            cost=c["cost"],
            metadata=c["metadata"],
        )
        for c in payload["candidates"]
    ]
    return payload["query"], payload, candidates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection_json", type=Path)
    args = parser.parse_args()

    query, payload, candidates = _load_candidates(args.selection_json)
    unique_texts = len({c.text.strip() for c in candidates})

    print(f"query: {query!r}")
    print(f"N = {len(candidates)}, {unique_texts} unique candidate texts")
    print()

    print(f"OR-Select winner:        {payload['winner_text']!r}")

    sc_winner, had_majority = self_consistency_winner(candidates)
    tag = "" if had_majority else "  (no true majority -- arbitrary tie-break)"
    print(f"Self-consistency winner: {sc_winner.text!r}{tag}")

    greedy_winner = greedy_single_sample(candidates)
    print(f"Greedy single-sample:    {greedy_winner.text!r}")

    print()
    scores = payload["scores"]
    print("OR-Select scores (sorted):")
    for cid, score in sorted(scores.items(), key=lambda kv: -kv[1]):
        marker = " <- winner" if cid == payload["winner_id"] else ""
        marker += " <- greedy pick" if cid == greedy_winner.id else ""
        print(f"  {cid}: {score:.4f}{marker}")

    print()
    or_select_agrees_with_sc = payload["winner_text"].strip() == sc_winner.text.strip()
    or_select_agrees_with_greedy = payload["winner_text"].strip() == greedy_winner.text.strip()
    print(f"OR-Select == self-consistency baseline: {or_select_agrees_with_sc}")
    print(f"OR-Select == greedy-single-sample baseline: {or_select_agrees_with_greedy}")


if __name__ == "__main__":
    main()
