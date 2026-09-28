#!/usr/bin/env python3
"""Tabulate H5: SAT time to first witness (results/knice_sat.jsonl) against the enumerator
baseline (results/first_hit.jsonl)."""
import json
from collections import defaultdict
from pathlib import Path
here = Path(__file__).resolve().parent
sat = defaultdict(list)
for l in (here / "results/knice_sat.jsonl").open():
    r = json.loads(l); sat[(r["K"], r["base"])].append(r)
enum = defaultdict(list)
for l in (here / "results/first_hit.jsonl").open():
    r = json.loads(l); enum[(r["K"], r["b"])].append(r)
N = {(3, 9): (63778, 7), (3, 10): (535841, 10), (2, 14): (716121, 1), (2, 15): (6771952, 1), (2, 16): (25498720, 1), (3, 13): (120679425, 16)}
print("| Case | Roots N | Witnesses | CNF variables / clauses | SAT: result per variant | SAT: seconds to first witness | Enumerator: full checks to first hit (mean of 6 starts) | Enumerator: seconds (mean, max) | SAT / enumerator (seconds) |")
print("|---|---:|---:|---|---|---|---:|---|---:|")
for k in sorted(set(sat) | set(enum), key=lambda k: N.get(k, (0, 0))[0]):
    n, h = N.get(k, (0, 0)); K, b = k
    s = sat.get(k, []); e = enum.get(k, [])
    res = ", ".join(r["result"] + ("" if r.get("verified", True) else "(!)") for r in s) or "not run"
    secs = ", ".join(f"{r['solve_seconds']:.0f}" + ("+" if r["result"] == "TIMEOUT" else "") for r in s if r.get("solve_seconds") is not None) or "—"
    vc = f"{s[0]['variables']:,} / {s[0]['clauses']:,}" if s and s[0].get("variables") else "—"
    if e:
        mean_checks = sum(r["full_checks"] for r in e) / len(e); mean_s = sum(r["seconds"] for r in e) / len(e); max_s = max(r["seconds"] for r in e)
        es = f"{mean_s:.4f}, {max_s:.4f}"
    else:
        mean_checks = None; es = "—"; mean_s = None
    sat_secs = [r["solve_seconds"] for r in s if r.get("solve_seconds") is not None]
    ratio = f"{(sum(sat_secs)/len(sat_secs))/mean_s:,.0f}" + ("+" if any(r["result"] == "TIMEOUT" for r in s) else "") if sat_secs and mean_s else "—"
    name = {2: "twice", 3: "thrice"}[K] + f"-{b}"
    print(f"| {name} | {n:,} | {h} | {vc} | {res} | {secs} | {f'{mean_checks:,.0f}' if mean_checks is not None else '—'} | {es} | {ratio} |")
