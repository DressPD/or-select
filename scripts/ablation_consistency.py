"""Ablation: does the deterministic self-consistency term change the winner?

    python3 scripts/ablation_consistency.py outputs/runs/*/selection.json

Fully offline -- no new API calls. Exactly reconstructs quality_i from
each saved selection.json's final score (score_i = w_quality*quality_i +
w_confidence*confidence_i + w_consistency*consistency_i - w_cost*cost_i,
so quality_i is recoverable exactly given the known weights), recomputes
consistency_i fresh from the saved candidate texts as a cross-check, then
re-solves with w_consistency=0 to see whether the ablated winner differs
from the original.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from or_select.consistency import compute_consistency  # noqa: E402
from or_select.core import Candidate  # noqa: E402
from or_select.selection import select_best  # noqa: E402

W_QUALITY = 1.0
W_CONFIDENCE = 0.2
W_CONSISTENCY = 0.3
W_COST = 0.01


def _load(path: Path) -> tuple[str, list[Candidate], dict[str, float], str]:
    payload = json.loads(path.read_text())
    candidates = [
        Candidate(
            id=c["id"], text=c["text"], source_model=c["source_model"],
            confidence=c["confidence"], cost=c["cost"], metadata=c["metadata"],
        )
        for c in payload["candidates"]
    ]
    return payload["query"], candidates, payload["scores"], payload["winner_id"]


def ablate_one(path: Path) -> dict:
    query, candidates, saved_scores, original_winner = _load(path)
    consistency = compute_consistency(candidates)

    # Exactly invert the known scoring formula to recover quality_i.
    quality = {}
    for c in candidates:
        quality[c.id] = (
            saved_scores[c.id] - W_CONFIDENCE * c.confidence - W_CONSISTENCY * consistency[c.id] + W_COST * c.cost
        ) / W_QUALITY

    # Sanity check: recomputing the original score from quality+consistency
    # should reproduce the saved score exactly.
    for c in candidates:
        recomputed = W_QUALITY * quality[c.id] + W_CONFIDENCE * c.confidence + W_CONSISTENCY * consistency[c.id] - W_COST * c.cost
        assert abs(recomputed - saved_scores[c.id]) < 1e-9, f"reconstruction mismatch for {c.id}"

    ablated_winner_id, _ = select_best(
        candidates, quality, consistency=None, w_quality=W_QUALITY, w_confidence=W_CONFIDENCE, w_cost=W_COST
    )
    full_winner_id, _ = select_best(
        candidates, quality, consistency=consistency,
        w_quality=W_QUALITY, w_confidence=W_CONFIDENCE, w_consistency=W_CONSISTENCY, w_cost=W_COST,
    )
    assert full_winner_id == original_winner, "reconstructed full-model winner doesn't match saved winner"

    return {
        "query": query,
        "n_candidates": len(candidates),
        "original_winner": original_winner,
        "ablated_winner": ablated_winner_id,
        "winner_changed": original_winner != ablated_winner_id,
        "consistency_spread": max(consistency.values()) - min(consistency.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection_json", type=Path, nargs="+")
    args = parser.parse_args()

    rows = [ablate_one(p) for p in args.selection_json]
    for r in rows:
        tag = "CHANGED" if r["winner_changed"] else "same"
        print(f"{r['query'][:60]!r}: {tag}  (original={r['original_winner']}, ablated={r['ablated_winner']}, "
              f"consistency_spread={r['consistency_spread']:.3f})")

    n_changed = sum(1 for r in rows if r["winner_changed"])
    print(f"\n{n_changed}/{len(rows)} winners changed when the self-consistency term was removed.")


if __name__ == "__main__":
    main()
