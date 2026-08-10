"""Ablation: does permutation self-consistency (bidirectional judging) change the winner?

    python3 scripts/ablation_permutation.py outputs/runs/*/selection.json --provider openrouter

Uses forward-only (single-direction) judge calls against already-saved
candidate texts, compared against the existing bidirectional (forward +
backward, averaged) result already saved in each selection.json. New
live judge calls are needed -- half the volume of a fresh pairwise
computation, since only one direction is called per pair -- but
candidates are reused from prior runs, not regenerated.
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
from or_select.selection import aggregate_quality, select_best  # noqa: E402


def _load(path: Path) -> tuple[str, list[Candidate], str]:
    payload = json.loads(path.read_text())
    candidates = [
        Candidate(
            id=c["id"], text=c["text"], source_model=c["source_model"],
            confidence=c["confidence"], cost=c["cost"], metadata=c["metadata"],
        )
        for c in payload["candidates"]
    ]
    return payload["query"], candidates, payload["winner_id"]


def build_single_direction_matrix(query: str, candidates: list[Candidate], judge_fn) -> dict:
    """Forward-only judge, no backward averaging -- the position-bias ablation."""
    weights: dict[tuple[str, str], float] = {}
    for i, a in enumerate(candidates):
        for b in candidates[i + 1 :]:
            if a.text.strip() == b.text.strip():
                weights[(a.id, b.id)] = 0.5
                weights[(b.id, a.id)] = 0.5
                continue
            forward = judge_fn(query, a.text, b.text)
            weights[(a.id, b.id)] = forward
            weights[(b.id, a.id)] = 1.0 - forward
    return weights


def ablate_one(path: Path, judge_fn) -> dict:
    query, candidates, original_winner = _load(path)
    print(f"judging (forward-only): {query[:60]!r} (N={len(candidates)})", flush=True)
    single_matrix = build_single_direction_matrix(query, candidates, judge_fn)
    quality = aggregate_quality(candidates, single_matrix)
    consistency = compute_consistency(candidates)
    ablated_winner_id, _ = select_best(candidates, quality, consistency)
    result = {
        "query": query,
        "bidirectional_winner": original_winner,
        "forward_only_winner": ablated_winner_id,
        "winner_changed": original_winner != ablated_winner_id,
    }
    tag = "CHANGED" if result["winner_changed"] else "same"
    print(f"  -> {tag} (bidirectional={original_winner}, forward-only={ablated_winner_id})", flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection_json", type=Path, nargs="+")
    parser.add_argument("--provider", default="openrouter", choices=("openai", "gemini", "openrouter"))
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "ablation_permutation.json")
    args = parser.parse_args()

    from or_select import providers

    judge_fn = {
        "openai": providers.openai_judge,
        "gemini": providers.gemini_judge,
        "openrouter": providers.openrouter_judge,
    }[args.provider]

    rows = [ablate_one(p, judge_fn) for p in args.selection_json]

    n_changed = sum(1 for r in rows if r["winner_changed"])
    print(f"\n{n_changed}/{len(rows)} winners changed when backward-direction judging was removed.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"provider": args.provider, "n_changed": n_changed, "results": rows}, indent=2))
    print(f"written: {args.output}")


if __name__ == "__main__":
    main()
