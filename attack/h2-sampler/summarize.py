#!/usr/bin/env python3
"""Tabulate the H2 sampler results (results/smc.jsonl) against the uniform-sampling control.

Every method records the DISTINCT witnesses found per run at a fixed evaluation budget
(the witness set of a case is small, so repeats are not informative). For uniform
sampling of B roots from N, the expected number of distinct witnesses is
H * (1 - (1 - 1/N)^B) with H witnesses in the interval; that expectation is printed
next to the observed control as a check and used as the reference for every method.
"""
import json, math, sys
from collections import defaultdict
from pathlib import Path
here = Path(__file__).resolve().parent
path = here / (sys.argv[1] if len(sys.argv) > 1 else "results/smc.jsonl")
rows = []; case = None
for l in path.open():
    if l.startswith("#"):
        case = dict(p.split("=") for p in l[1:].split())
    elif l.startswith("{"):
        try:
            r = json.loads(l)
        except json.JSONDecodeError:
            continue   # a line still being written
        r["case"] = case["case"]; r["thin"] = int(case["thin"]); rows.append(r)
known = {"thrice10": (535841, 10), "twice15": (6771952, 1), "thrice13": (120679425, 16), "twice17": (60063526, 1), "thrice14": (2081072521, 38)}
agg = defaultdict(lambda: {"evals": 0, "wit": 0, "distinct": set(), "runs": 0, "runs_with": 0, "episodes": 0, "tau0": 0, "stalled": 0,
                           "anc_final": [], "acc_final": []})
for r in rows:
    a = agg[(r["case"], r["mode"], r["thin"])]
    a["evals"] += r["evals"]; a["wit"] += r["distinct_witnesses"]; a["distinct"] |= set(r["witnesses"]); a["runs"] += 1
    a["runs_with"] += 1 if r["distinct_witnesses"] else 0
    a["episodes"] += r.get("episodes", 0); a["tau0"] += r.get("episodes_reaching_tau0", 0); a["stalled"] += r.get("episodes_stalled", 0)
    lv = r["levels"]
    if lv:
        a["anc_final"].append(lv[-1]["distinct_ancestors_seeds"])
        accs = [x["accept"] for x in lv if x["accept"] is not None]
        if accs: a["acc_final"].append(accs[-1])
mode_name = {9: "uniform random (control)", 0: "SMC, any digit", 1: "SMC, top two digits", 2: "SMC, mixed"}
print("| Case | Roots N | Witnesses H | Method | thin | Runs | Budget per run | Distinct witnesses per run, observed | Expected for uniform | Observed / expected | Runs with a witness | Episodes per run | Episodes reaching φ = 0 | Final-level seeds' distinct ancestors (of 2000) | Final acceptance |")
print("|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for k in sorted(agg, key=lambda k: (known[k[0]][0], k[1] if k[1] != 9 else -1, k[2])):
    a = agg[k]; N, H = known[k[0]]
    B = a["evals"] / a["runs"]
    exp_uniform = H * (1 - math.exp(B * math.log1p(-1.0 / N)))
    obs = a["wit"] / a["runs"]
    anc = sum(a["anc_final"]) / len(a["anc_final"]) if a["anc_final"] else None
    acc = sum(a["acc_final"]) / len(a["acc_final"]) if a["acc_final"] else None
    smc = k[1] != 9
    print(f"| {k[0]} | {N:,} | {H} | {mode_name[k[1]]} | {k[2] if smc else '—'} | {a['runs']} | {B:,.3g} | {obs:.2f} | {exp_uniform:.2f} | {obs/exp_uniform:.2f} | "
          f"{a['runs_with']}/{a['runs']} | {a['episodes']/a['runs']:.0f} | {a['tau0']}/{a['episodes']} | {f'{anc:.0f}' if anc is not None else '—'} | {f'{acc:.4f}' if acc is not None else '—'} |"
          if smc else
          f"| {k[0]} | {N:,} | {H} | {mode_name[k[1]]} | — | {a['runs']} | {B:,.3g} | {obs:.2f} | {exp_uniform:.2f} | {obs/exp_uniform:.2f} | {a['runs_with']}/{a['runs']} | — | — | — | — |")
