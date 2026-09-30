#!/usr/bin/env python3
"""Testbed comparison table: client pipeline vs P1's overlap join.

Inputs: client_testbed.json (run_client_testbed.py), ../p1-algorithm/testbed.json
(P1's join, no digit-sum filter), join_ds_testbed.json (run_join_testbed.py,
join with the digit-sum filter). Operation counts:
  client = MSD analyses + stride visits + full checks
  join   = top calls + bottom calls + (digit-sum lookups) + matches + survivors
"Gain" = client ops / join ops (> 1: the join does fewer operations).
Output: comparison.json and a markdown table on stdout.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = json.loads((HERE.parents[0] / "p1-algorithm/testbed.json").read_text())
CL = json.loads((HERE / "client_testbed.json").read_text())
JD = json.loads((HERE / "join_ds_testbed.json").read_text()) if (HERE / "join_ds_testbed.json").exists() else {}

order = {"nice": 0, "twice": 1, "thrice": 2}
rows = []
for key, c in CL.items():
    name, floor = key.split("@")
    if floor != "8000":
        continue
    p = P1[name]
    j_best = p["best_join"]
    p1_best_ops = j_best["top_calls"] + j_best["bottom_calls"] + j_best["matches"] + j_best["survivors"]
    p1_min = min(p["joins"], key=lambda j: j["top_calls"] + j["bottom_calls"] + j["matches"] + j["survivors"])
    p1_min_ops = p1_min["top_calls"] + p1_min["bottom_calls"] + p1_min["matches"] + p1_min["survivors"]
    jd = JD.get(name)
    row = {"case": name, "kind": p["kind"], "base": p["base"], "N": p["N"], "L": p["L"],
           "solutions_found": len(c["solutions"]), "solutions_known": len(c["known_solutions"]),
           "client": {k: c[k] for k in ("analyses", "visits", "mask_rejects", "full_checks", "full_digits", "ops",
                                         "cert_per_visit", "doms_per_visit", "leaf_n")},
           "p1_join_best": {"t": j_best["t"], "k": j_best["k"], "o": j_best["overlap"], "ops": p1_best_ops,
                            "matches": j_best["matches"], "survivors": j_best["survivors"]},
           "p1_join_min_ops": {"t": p1_min["t"], "k": p1_min["k"], "ops": p1_min_ops},
           "gain_vs_p1_best": c["ops"] / p1_best_ops, "gain_vs_p1_min": c["ops"] / p1_min_ops,
           "full_check_ratio_vs_p1_best": c["full_checks"] / max(j_best["survivors"], 1)}
    if jd:
        b = jd["best"]
        row["join_ds_best"] = b
        row["gain_vs_join_ds"] = c["ops"] / b["ops"]
        row["full_check_ratio_vs_join_ds"] = c["full_checks"] / max(b["survivors"], 1)
    rows.append(row)
rows.sort(key=lambda r: (order[r["kind"]], r["base"]))
(HERE / "comparison.json").write_text(json.dumps(rows, indent=1) + "\n")

print("| Case | N | Solutions | Client: MSD analyses | stride visits | full checks | client ops | "
      "P1 join (t,k,o): ops | client / P1 join | join + digit-sum (t,k): ops | client / join+ds | full checks client / join+ds |")
print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for r in rows:
    c, j = r["client"], r["p1_join_best"]
    jd = r.get("join_ds_best")
    jds = f"({jd['t']},{jd['k']}): {jd['ops']:.2e}" if jd else "–"
    g2 = f"{r['gain_vs_join_ds']:.2f}×" if jd else "–"
    f2 = f"{r['full_check_ratio_vs_join_ds']:.1f}×" if jd else "–"
    print(f"| {r['case']} | {r['N']:.2e} | {r['solutions_found']}/{r['solutions_known']} | {c['analyses']:.2e} | "
          f"{c['visits']:.2e} | {c['full_checks']:.2e} | {c['ops']:.2e} | ({j['t']},{j['k']},{j['o']}): {j['ops']:.2e} | "
          f"{r['gain_vs_p1_best']:.2f}× | {jds} | {g2} | {f2} |")
