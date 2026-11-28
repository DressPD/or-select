"""Universal self-consistency (USC, Chen et al. 2023) on the stored candidate pools.

    python3 scripts/usc_baseline.py --run        # live: one judge call per problem (resumable, writes outputs/usc_baseline.json)
    python3 scripts/usc_baseline.py              # offline analysis of the stored USC outputs, writes manuscript/Usc_data.tex

The live run asks the same free-tier judge model used everywhere else (reasoning off, short reply) to read all stored
responses of a problem at once and name the most consistent one. The candidate pools are NOT regenerated: USC is applied
to the stored candidates, so it is compared with plurality and Rule H on identical pools. One call per problem; a reply
without a valid response index is re-sampled with a new seed (up to three attempts); if none parses, the first candidate
is used and the problem is flagged. The prompt follows the paper's free-form prompt with the final-answer format changed
to a bare index so the short-reply path can be used.
"""

from __future__ import annotations

import json
import re
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import judge_threshold_theory as th  # noqa: E402
from hybrid_rule import TRACKS, mcnemar_p  # noqa: E402

OUT = ROOT / "outputs" / "usc_baseline.json"
DEST = ROOT / "manuscript" / "Usc_data.tex"
MAX_CALLS = 900  # stay below the daily free-tier counter (about 1000)

PROMPT = (
    "I have generated the following responses to the question: {query}\n\n{responses}\n\n"
    "Evaluate these responses.\nSelect the most consistent response based on majority consensus.\n"
    "Start your answer with \"The most consistent response is Response X\" where X is the response number."
)


def build_prompt(query: str, texts: list[str]) -> str:
    responses = "\n\n".join(f"Response {i}: {t.strip()}" for i, t in enumerate(texts))
    return PROMPT.format(query=query, responses=responses)


def parse_choice(reply: str, n: int):
    m = re.search(r"Response\s*(\d+)", reply)
    if m and 0 <= int(m.group(1)) < n:
        return int(m.group(1))
    return None


def rows():
    for label, fname, kind, het in TRACKS:
        path = th.OUT / fname
        if not path.exists():
            continue
        for idx, row in enumerate(json.loads(path.read_text())["results"]):
            if "error" in row or not row.get("candidates"):
                continue
            yield f"{'het' if het else 'hom'}|{label}|{idx}", label, kind, het, row


def run() -> None:
    from or_select import providers  # imported lazily: needs credentials

    store = json.loads(OUT.read_text()) if OUT.exists() else {}
    calls = 0
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    started = len(store)
    for key, label, kind, het, row in rows():
        if key in store:
            continue
        if limit is not None and len(store) - started >= limit:
            break
        texts = [c["text"] for c in row["candidates"]]
        prompt = build_prompt(row["query"], texts)
        choice, reply, attempts = None, "", 0
        for attempt in range(3):
            attempts += 1
            calls += 1
            try:
                reply = providers._short_answer_text(prompt, seed_offset=attempt * 3)
            except Exception as exc:  # noqa: BLE001 -- recorded, never silently dropped
                reply = f"ERROR {type(exc).__name__}: {exc}"
                continue
            choice = parse_choice(reply, len(texts))
            if choice is not None:
                break
        store[key] = {"choice": choice, "reply": reply[:300], "attempts": attempts, "n": len(texts)}
        OUT.write_text(json.dumps(store, indent=0))
        if calls >= MAX_CALLS:
            print("call budget reached; resume later with --run")
            break
        if len(store) % 25 == 0:
            print(f"{len(store)} problems done, {calls} calls", flush=True)
    print(f"done: {len(store)} stored, {calls} calls this run")


def analyze() -> None:
    store = json.loads(OUT.read_text())
    groups: dict = {}
    for key, label, kind, het, row in rows():
        rec = store.get(key)
        if rec is None:
            continue
        ok = [bool(th.CORRECT[kind](th.EXTRACT[kind](c["text"]), row["ground_truth"])) for c in row["candidates"]]
        choice = rec["choice"]
        failed = choice is None
        usc = ok[0 if failed else choice]
        judged = row.get("judge_version") == "short-answer" and bool(row.get("judgments"))
        r = {"usc": usc, "sc": bool(row["self_consistency"]["correct"]), "fail": failed, "judged": judged, "choice": choice,
             "unique_best": sum(ok) >= 1 and sum(ok) < len(ok),
             "any": any(ok), "ors": bool(row["or_select"]["correct"]) if isinstance(row.get("or_select"), dict) and "correct" in row["or_select"] else None}
        for k in ((het, label), (het, "All")):
            groups.setdefault(k, []).append(r)
    lines = ["% Generated by scripts/usc_baseline.py -- do not hand-edit."]
    print("track | n | fail | USC | plurality | USC-only/plurality-only (p) | OR-Select")
    for (het, label), r in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] == "All", kv[0][1])):
        n = len(r)
        pct = lambda f: 100 * sum(f(x) for x in r) / n  # noqa: E731
        b = sum(1 for x in r if x["usc"] and not x["sc"])
        c = sum(1 for x in r if x["sc"] and not x["usc"])
        p = mcnemar_p(b, c)
        fp = "=\\mathrm{n/a}" if p is None else ("<0.001" if p < 0.001 else f"={p:.3f}")
        print(f"{'het' if het else 'hom'} {label:10} n={n:3} fail={sum(x['fail'] for x in r):2} USC={pct(lambda x: x['usc']):.1f} "
              f"SC={pct(lambda x: x['sc']):.1f} | {b}/{c} p={fp}")
        if label == "All":
            tag = "Het" if het else "Hom"
            picks = [x["choice"] for x in r if x["choice"] is not None]
            top = max(set(picks), key=picks.count)
            share = 100 * picks.count(top) / len(picks)
            mixed = [x for x in r if x["unique_best"]]
            mixed_acc = 100 * sum(x["usc"] for x in mixed) / max(1, len(mixed))
            mixed_sc = 100 * sum(x["sc"] for x in mixed) / max(1, len(mixed))
            print(f"   most-picked response index {top} in {share:.1f}% of picks; on {len(mixed)} problems with mixed pools USC {mixed_acc:.1f}% vs plurality {mixed_sc:.1f}%")
            lines += [rf"\def\Usc{tag}TopPos{{{top}}}", rf"\def\Usc{tag}TopShare{{{share:.1f}}}", rf"\def\Usc{tag}MixedN{{{len(mixed)}}}",
                      rf"\def\Usc{tag}MixedAcc{{{mixed_acc:.1f}}}", rf"\def\Usc{tag}MixedSC{{{mixed_sc:.1f}}}"]
            lines += [rf"\def\Usc{tag}N{{{n}}}", rf"\def\Usc{tag}Fail{{{sum(x['fail'] for x in r)}}}",
                      rf"\def\Usc{tag}Acc{{{pct(lambda x: x['usc']):.1f}}}", rf"\def\Usc{tag}SC{{{pct(lambda x: x['sc']):.1f}}}",
                      rf"\def\Usc{tag}B{{{b}}}", rf"\def\Usc{tag}C{{{c}}}", rf"\def\Usc{tag}P{{{fp}}}"]
    DEST.write_text("\n".join(lines) + "\n")
    print("wrote", DEST)


if __name__ == "__main__":
    run() if "--run" in sys.argv else analyze()
