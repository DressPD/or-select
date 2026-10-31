"""Opt-in second pass for rows that exhausted the output-token cap.

The main benchmark pass runs every problem under one fixed cap
(providers.MAX_OUTPUT_TOKENS, 32768). A row whose draws all hit that cap is
stored as a settled truncation. This module re-runs only those rows with a
higher cap and keeps the two protocols apart in the data: the extended result
carries `extended_cap_pass`/`extended_cap_requested`, and the original failure
is preserved in `main_protocol`, so an accuracy under the main protocol alone
(truncated rows counted as failures) can always be recomputed.

Nothing here runs unless a benchmark script is given --extended-cap.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from . import providers

# 65536 tokens at the free tier's measured 17-30 tokens/s is up to ~64 min per
# draw; the default 3600 s stream deadline would cut it off.
EXTENDED_STREAM_TIMEOUT_SECONDS = 7200.0

_MAIN_PROTOCOL_KEYS = ("error", "truncated_at_tokens", "truncation_attempts")


def configure(cap: int) -> None:
    """Raise the global output cap (per-model limits in
    providers.MODEL_OUTPUT_LIMITS still clamp it) and the stream deadline."""
    providers.MAX_OUTPUT_TOKENS = cap
    providers.STREAM_TIMEOUT_SECONDS = max(providers.STREAM_TIMEOUT_SECONDS, EXTENDED_STREAM_TIMEOUT_SECONDS)


def failing_model(row: dict, provider: str, models: list[str]) -> str | None:
    """The model whose slot failed in a stored failed row. The heterogeneous
    pool is round-robin (slot i -> models[i % len]) and ValidityExhausted names
    the failing seed in the error text; a homogeneous track has one model."""
    if provider == "openrouter":
        return providers.OPENROUTER_MODEL
    if provider == "openrouter_mixed" and models:
        match = re.search(r"seed=(\d+)", row.get("error", ""))
        if match:
            return models[int(match.group(1)) % len(models)]
    return None


def select_targets(results: list[dict], provider: str, models: list[str]) -> list[dict]:
    """Stored rows an extended pass can still help: failed by truncation at a
    cap below what their failing model now allows. A row already truncated at
    that model's maximum (laguna at 32768, or any row after an extended
    attempt) is not selected again. Call after configure()."""
    targets = []
    for row in results:
        if "error" not in row or not row.get("truncated"):
            continue
        model = failing_model(row, provider, models)
        if model is None:
            continue
        if row.get("truncated_at_tokens", 0) < providers._output_cap(model):
            targets.append(row)
    return targets


def main_protocol_record(row: dict) -> dict:
    """What the main pass stored for this row, copied before it is replaced."""
    return row.get("main_protocol") or {k: row[k] for k in _MAIN_PROTOCOL_KEYS if k in row}


def mark_extended(new_row: dict, old_row: dict, cap_requested: int) -> dict:
    new_row["extended_cap_pass"] = True
    new_row["extended_cap_requested"] = cap_requested
    new_row["main_protocol"] = main_protocol_record(old_row)
    return new_row


def note_failed_attempt(old_row: dict, exc: Exception, cap_requested: int) -> dict:
    """An extended attempt that failed for a reason other than truncation (API
    or infrastructure): keep the stored row as it was, and record the attempt,
    so the row stays selectable and nothing about it is lost."""
    old_row["extended_attempt_error"] = f"{type(exc).__name__}: {exc}"[:300]
    old_row["extended_cap_requested"] = cap_requested
    return old_row


def run_extended_pass(
    results: list[dict],
    problems: list[dict],
    provider: str,
    models: list[str],
    cap: int,
    *,
    grade_one: Callable[[dict], dict],
    failed_row: Callable[[dict, Exception], dict],
    persist: Callable[[list[dict]], None],
) -> list[dict]:
    """Re-run the selected truncated rows at `cap`, replacing each stored row
    in place (so a kill mid-pass loses nothing) and persisting after every row.
    Refuses to run while any problem is untried: the extended cap must never
    leak into the main pass."""
    done = {r["query"] for r in results}
    untried = [p for p in problems if p["query"] not in done]
    if untried:
        raise RuntimeError(
            f"{len(untried)} problems are untried; finish the main pass before the extended-cap pass"
        )
    configure(cap)
    by_query = {p["query"]: p for p in problems}
    targets = [t for t in select_targets(results, provider, models) if t["query"] in by_query]
    print(f"extended-cap pass: {len(targets)} truncated rows to re-run at cap {cap}", flush=True)
    for k, old in enumerate(targets, start=1):
        problem = by_query[old["query"]]
        idx = next(j for j, r in enumerate(results) if r is old)
        print(f"[ext {k}/{len(targets)}] {problem['query'][:70]!r}...", flush=True)
        try:
            row = grade_one(problem)
        except Exception as exc:  # noqa: BLE001 -- one row's failure must not kill the pass
            failed = failed_row(problem, exc)
            if failed.get("truncated"):
                failed["truncation_attempts"] = old.get("truncation_attempts", 1) + 1
                results[idx] = mark_extended(failed, old, cap)
            else:
                results[idx] = note_failed_attempt(old, exc, cap)
            print(f"    FAILED: {failed['error']}", flush=True)
        else:
            results[idx] = mark_extended(row, old, cap)
            print("    graded under the extended cap", flush=True)
        persist(results)
    return results
