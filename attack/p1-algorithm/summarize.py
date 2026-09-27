#!/usr/bin/env python3
"""Print the testbed table used in REPORT.md from testbed.json."""
import json
from pathlib import Path

d = json.loads((Path(__file__).with_name("testbed.json")).read_text())
order = {"nice": 0, "twice": 1, "thrice": 2}
rows = sorted(d.values(), key=lambda r: (order[r["kind"]], r["base"]))
print("| case | N | sols found / known | edge (t,k): leaves = full checks | join (t,k,o) | matches (O(1)) | full checks | full-check ratio | total-ops ratio |")
print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for r in rows:
    if r["N"] < 1e6:
        continue
    e, j = r["edge"], r["best_join"]
    ops_e = e["top_calls"] + e["bottom_calls"] + e["trie_visits"] + e["leaves"]
    ops_j = j["top_calls"] + j["bottom_calls"] + j["matches"] + j["survivors"]
    found = len(next(x for x in r["joins"] if x["t"] == j["t"] and x["k"] == j["k"])["solutions"])
    print(f"| {r['kind']}-{r['base']} | {r['N']:.2e} | {found} / {len(r['known_solutions'])} | "
          f"({e['t']},{e['k']}): {e['leaves']:.2e} | ({j['t']},{j['k']},{j['overlap']}) | {j['matches']:.2e} | "
          f"{j['survivors']:.2e} | {e['leaves'] / max(j['survivors'], 1):.0f}x | {ops_e / ops_j:.2f}x |")
