"""Shared types, constants, and I/O for the OR-Select pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "runs"
DEFAULT_N_CANDIDATES = 10


@dataclass
class Candidate:
    """One sampled LLM answer for a given query."""

    id: str
    text: str
    source_model: str
    confidence: float = 0.0
    cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SelectionResult:
    """Deterministic output of the OR-Select pipeline for one query."""

    query: str
    winner_id: str
    winner_text: str
    scores: dict[str, float]
    candidates: list[Candidate]
    pairwise: dict[tuple[str, str], float] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "winner_id": self.winner_id,
            "winner_text": self.winner_text,
            "scores": self.scores,
            "candidates": [c.__dict__ for c in self.candidates],
            "pairwise": {f"{a}|{b}": w for (a, b), w in self.pairwise.items()},
        }


def run_dir(query_id: str) -> Path:
    path = DEFAULT_OUTPUTS_DIR / query_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
