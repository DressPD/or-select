"""Paid judges on the stored candidate pools: pairwise judging (both orders) and universal self-consistency (USC).

    python3 scripts/strong_judges.py --run anthropic/claude-haiku-5.5 --cap 1.2 [--rows 5]   # live, resumable
    python3 scripts/strong_judges.py                                                          # offline analysis, writes manuscript/Strong_data.tex

The same prompts as the free-judge audit are used (prompts/judge_prompt.txt; the USC prompt of scripts/usc_baseline.py),
with reasoning switched off and a short reply. Each model writes outputs/strong_judge_<slug>.json. A run stops when the
account's measured spend since the start of the run reaches --cap dollars (checked against OpenRouter's usage counter).
Pools are not regenerated: every judge sees exactly the stored candidates, so selectors are compared on identical pools.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import judge_threshold_theory as th  # noqa: E402
from hybrid_rule import mcnemar_p, select  # noqa: E402
from usc_baseline import build_prompt, parse_choice, rows  # noqa: E402

MODELS = {"anthropic/claude-haiku-5.5": "Haiku 5.5", "openai/gpt-5.6-luna": "GPT Luna"}
DEST = ROOT / "manuscript" / "Strong_data.tex"


def slug(model: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", model.lower()).strip("_")


def store_path(model: str) -> Path:
    return ROOT / "outputs" / f"strong_judge_{slug(model)}.json"


def usage_dollars() -> float:
    from dotenv import load_dotenv

    load_dotenv()
    req = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
    return float(json.load(urllib.request.urlopen(req, timeout=30))["data"]["usage"])


def run(model: str, cap: float, max_rows: int | None, het_stride: int = 1) -> None:
    from or_select import providers

    path = store_path(model)
    store = json.loads(path.read_text()) if path.exists() else {"pair": {}, "usc": {}}
    lock = threading.Lock()
    start = usage_dollars()
    stop = threading.Event()
    units = []
    seen_rows = 0
    het_seen = 0
    for key, label, kind, het, row in rows():
        seen_rows += 1
        if max_rows is not None and seen_rows > max_rows:
            break
        texts = [c["text"] for c in row["candidates"]]
        if key not in store["usc"]:
            units.append(("usc", key, row["query"], texts, None, None))
        if het:
            het_seen += 1
            if (het_seen - 1) % het_stride != 0:
                continue  # budget: pairwise judging on every het_stride-th heterogeneous problem only
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                if f"{key}|{i}|{j}" not in store["pair"] and texts[i].strip() != texts[j].strip():
                    units.append(("pair", key, row["query"], texts, i, j))
    print(f"{model}: {len(units)} units to run, starting usage ${start:.4f}, cap ${cap}", flush=True)
    done = [0]

    def save() -> None:
        path.write_text(json.dumps(store))

    def work(unit) -> None:
        if stop.is_set():
            return
        kind, key, query, texts, i, j = unit
        try:
            if kind == "pair":
                f = providers.openrouter_judge(query, texts[i], texts[j], model=model)
                b = providers.openrouter_judge(query, texts[j], texts[i], model=model)
                with lock:
                    store["pair"][f"{key}|{i}|{j}"] = [f, b]
            else:
                prompt = build_prompt(query, texts)
                choice, reply = None, ""
                for attempt in range(3):
                    try:
                        reply = providers._short_answer_text(prompt, model=model, seed_offset=attempt * 3)
                    except Exception as exc:  # noqa: BLE001 -- recorded
                        reply = f"ERROR {type(exc).__name__}: {exc}"
                        continue
                    choice = parse_choice(reply, len(texts))
                    if choice is not None:
                        break
                with lock:
                    store["usc"][key] = {"choice": choice, "reply": reply[:200], "n": len(texts)}
        except Exception as exc:  # noqa: BLE001 -- one failed unit must not kill the run; it stays unrun and is retried on resume
            print("unit failed:", type(exc).__name__, str(exc)[:80], flush=True)
            return
        with lock:
            done[0] += 1
            n = done[0]
        if n % 100 == 0:
            with lock:
                save()
            spent = usage_dollars() - start
            print(f"{n}/{len(units)} units, spent ${spent:.4f}", flush=True)
            if spent >= cap:
                print("spend cap reached, stopping", flush=True)
                stop.set()

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(work, units))
    save()
    print(f"finished: {done[0]} units this run, spent ${usage_dollars() - start:.4f}", flush=True)


def analyze() -> None:
    lines = ["% Generated by scripts/strong_judges.py -- do not hand-edit."]
    for model, name in MODELS.items():
        path = store_path(model)
        if not path.exists():
            continue
        store = json.loads(path.read_text())
        tag = "Haiku" if "haiku" in model else "Luna"
        ug: dict = {}
        for key, label, kind, het, row in rows():
            if key not in store["usc"]:
                continue
            u = store["usc"][key]["choice"]
            okc = [bool(th.CORRECT[kind](th.EXTRACT[kind](c["text"]), row["ground_truth"])) for c in row["candidates"]]
            ug.setdefault(het, []).append((okc[0 if u is None else u], bool(row["self_consistency"]["correct"]), u is None))
        for het, v in sorted(ug.items()):
            n = len(v)
            b = sum(1 for a, s, _ in v if a and not s)
            c = sum(1 for a, s, _ in v if s and not a)
            p = mcnemar_p(b, c)
            print(f"   USC all stored rows {'het' if het else 'hom'}: n={n} USC={100 * sum(a for a, _, _ in v) / n:.1f} SC={100 * sum(s for _, s, _ in v) / n:.1f} "
                  f"({b}/{c} p={p}) failed replies={sum(f for _, _, f in v)}")
            tg = f"{tag}{'Het' if het else 'Hom'}"
            fpu = "=\\mathrm{n/a}" if p is None else ("<0.001" if p < 0.001 else f"={p:.3f}")
            lines += [rf"\def\St{tg}UN{{{n}}}", rf"\def\St{tg}UAcc{{{100 * sum(a for a, _, _ in v) / n:.1f}}}", rf"\def\St{tg}USC{{{100 * sum(s for _, s, _ in v) / n:.1f}}}",
                      rf"\def\St{tg}UB{{{b}}}", rf"\def\St{tg}UC{{{c}}}", rf"\def\St{tg}UP{{{fpu}}}", rf"\def\St{tg}UFail{{{sum(f for _, _, f in v)}}}"]
        groups: dict = {}
        for key, label, kind, het, row in rows():
            if key not in store["usc"]:
                continue
            texts = [c["text"] for c in row["candidates"]]
            n = len(texts)
            pairwise, complete = {}, True
            for i in range(n):
                for j in range(i + 1, n):
                    if texts[i].strip() == texts[j].strip():
                        w = 0.5
                    else:
                        rec = store["pair"].get(f"{key}|{i}|{j}")
                        if rec is None:
                            complete = False
                            break
                        w = (rec[0] + (1 - rec[1])) / 2
                    pairwise[f"c{i}|c{j}"] = w
                    pairwise[f"c{j}|c{i}"] = 1 - w
                if not complete:
                    break
            if not complete:
                continue
            ok = [bool(th.CORRECT[kind](th.EXTRACT[kind](c["text"]), row["ground_truth"])) for c in row["candidates"]]
            synth = dict(row)
            synth["judgments"] = {"pairwise": pairwise}
            hyb, cop, tie, _, _ = select(synth, kind)
            u = store["usc"][key]["choice"]
            hit = tot = 0
            for i in range(n):
                for j in range(i + 1, n):
                    if ok[i] != ok[j]:
                        w = pairwise[f"c{i}|c{j}"]
                        hit += w if ok[i] else 1 - w
                        tot += 1
            r = {"cop": ok[cop], "hyb": ok[hyb], "usc": ok[0 if u is None else u], "sc": bool(row["self_consistency"]["correct"]),
                 "uscfail": u is None, "hit": hit, "tot": tot, "pick": u}
            for k in ((het, label), (het, "All")):
                groups.setdefault(k, []).append(r)
        print(f"\n== {name}")
        for (het, label), r in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] == "All", kv[0][1])):
            n = len(r)
            pct = lambda f: 100 * sum(f(x) for x in r) / n  # noqa: E731

            def disc(a, b):
                x = sum(1 for v in r if v[a] and not v[b])
                y = sum(1 for v in r if v[b] and not v[a])
                return x, y, mcnemar_p(x, y)

            cb, cc, cp = disc("cop", "sc")
            ub, uc, up = disc("usc", "sc")
            q = sum(x["hit"] for x in r) / max(1, sum(x["tot"] for x in r))
            print(f"{'het' if het else 'hom'} {label:10} n={n:3} SC={pct(lambda x: x['sc']):.1f} Cop={pct(lambda x: x['cop']):.1f} ({cb}/{cc} p={cp}) "
                  f"H={pct(lambda x: x['hyb']):.1f} USC={pct(lambda x: x['usc']):.1f} ({ub}/{uc} p={up}) q^={q:.2f}")
            if label == "All":
                tg = f"{tag}{'Het' if het else 'Hom'}"
                fp = lambda p: "=\\mathrm{n/a}" if p is None else ("<0.001" if p < 0.001 else f"={p:.3f}")  # noqa: E731
                lines += [rf"\def\St{tg}N{{{n}}}", rf"\def\St{tg}SC{{{pct(lambda x: x['sc']):.1f}}}", rf"\def\St{tg}Cop{{{pct(lambda x: x['cop']):.1f}}}",
                          rf"\def\St{tg}Hyb{{{pct(lambda x: x['hyb']):.1f}}}", rf"\def\St{tg}Usc{{{pct(lambda x: x['usc']):.1f}}}",
                          rf"\def\St{tg}CopB{{{cb}}}", rf"\def\St{tg}CopC{{{cc}}}", rf"\def\St{tg}CopP{{{fp(cp)}}}",
                          rf"\def\St{tg}UscB{{{ub}}}", rf"\def\St{tg}UscC{{{uc}}}", rf"\def\St{tg}UscP{{{fp(up)}}}", rf"\def\St{tg}Q{{{q:.2f}}}"]
    DEST.write_text("\n".join(lines) + "\n")
    print("wrote", DEST)


if __name__ == "__main__":
    if "--run" in sys.argv:
        model = sys.argv[sys.argv.index("--run") + 1]
        cap = float(sys.argv[sys.argv.index("--cap") + 1]) if "--cap" in sys.argv else 1.0
        max_rows = int(sys.argv[sys.argv.index("--rows") + 1]) if "--rows" in sys.argv else None
        run(model, cap, max_rows, int(sys.argv[sys.argv.index("--het-stride") + 1]) if "--het-stride" in sys.argv else 1)
    else:
        analyze()
