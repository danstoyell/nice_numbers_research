#!/usr/bin/env python3
"""Summarize results/bench_gpu*.jsonl: per field and per base, means over
rounds with the spread across rounds (the client's rounds are independent
stratified samples, so their standard error is the sampling error; the join
runs whole fields, so its spread is timing noise only).
Usage: summarize_bench.py [bench.jsonl ...]  -> prints tables, writes results/bench_summary.json"""
import json, statistics as S, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
files = sys.argv[1:] or [str(HERE / "results" / "bench_gpu.jsonl")]
recs = [json.loads(l) for f in files for l in open(f) if l.strip()]
recs = [r for r in recs if "error" not in r]


def ms(v):
    v = [x for x in v if x is not None]
    if not v:
        return None, None, 0
    m = S.mean(v)
    se = S.stdev(v) / len(v) ** 0.5 if len(v) > 1 else None
    return m, se, len(v)


per = defaultdict(lambda: defaultdict(list))
for r in recs:
    key = (r["base"], r["field_start"])
    m = r["method"]
    if m == "join":
        per[key]["join_wall"].append(r["field_wall"])
        per[key]["join_cpu"].append(r["field_cpu"])
        per[key]["join_dev"].append(r["est_device_sec"])
        per[key]["join_dev_nomid"].append(r.get("est_device_sec_nomid"))
        per[key]["join_host"].append(r["est_host_cpu_sec"])
        per[key]["join_surv"].append(r["field_survivors"])
        per[key]["join_pref"].append(r["field_prefilter_survivors"])
        per[key]["join_hits"].append(len(r["field_hits"]))
    elif m == "join-devtops":
        per[key]["dt_wall"].append(r["field_wall"])
        per[key]["dt_cpu"].append(r["field_cpu"])
        per[key]["dt_surv"].append(r["field_survivors"])
    elif m == "client":
        per[key]["client_sec"].append(r["est_field_sec"])
        per[key]["client_cpu"].append(r["est_field_cpu"])
        per[key]["client_hits"].append(len(r["hits"]))
    elif m == "client-metal":
        per[key]["clientm_sec"].append(r["est_field_sec"])
    elif m == "client-pinned":
        per[key]["clientp_sec"].append(r["est_field_sec"])
        per[key]["clientp_cpu"].append(r["est_field_cpu"])

out = {"fields": {}, "bases": {}}
print(f"{'base':>4} {'field':>24} | {'client s':>14} {'cl cpu':>7} | {'join wall':>9} {'j cpu':>6} {'j dev':>6} {'j dev0':>6} {'j host':>6} | {'dt wall':>7} | {'ratio':>6} {'ratio dt':>8}")
bybase = defaultdict(lambda: defaultdict(list))
for (b, f), d in sorted(per.items()):
    row = {k: ms(v) for k, v in d.items()}
    out["fields"][f"{b}:{f}"] = {k: {"mean": x[0], "se": x[1], "n": x[2]} for k, x in row.items()}
    c = row.get("client_sec", (None,))[0]
    jw = row.get("join_wall", (None,))[0]
    dtw = row.get("dt_wall", (None,))[0]
    ratio = c / jw if c and jw else None
    cp = row.get("clientp_sec", (None,))[0]
    if cp and jw:
        bybase[b]["ratio_pinned"].append(cp / jw)
    if cp and dtw:
        bybase[b]["ratio_pinned_dt"].append(cp / dtw)
    rdt = c / dtw if c and dtw else None
    for k, v in row.items():
        if v[0] is not None:
            bybase[b][k].append(v[0])
    if ratio:
        bybase[b]["ratio"].append(ratio)
    if rdt:
        bybase[b]["ratio_dt"].append(rdt)
    cse = row.get("client_sec", (None, None))[1]
    f2 = lambda x: f"{x:.1f}" if x is not None else "-"
    print(f"{b:>4} {f:>24} | {f2(c):>7}±{f2(cse):>5} {f2(row.get('client_cpu',(None,))[0]):>7} | {f2(jw):>9} {f2(row.get('join_cpu',(None,))[0]):>6} "
          f"{f2(row.get('join_dev',(None,))[0]):>6} {f2(row.get('join_dev_nomid',(None,))[0]):>6} {f2(row.get('join_host',(None,))[0]):>6} | {f2(dtw):>7} | "
          f"{f2(ratio):>6} {f2(rdt):>8}")
print()
for b, d in sorted(bybase.items()):
    agg = {k: {"mean": S.mean(v), "min": min(v), "max": max(v), "n": len(v)} for k, v in d.items()}
    out["bases"][b] = agg
    g = lambda k: agg[k]["mean"] if k in agg else float("nan")
    rr = agg.get("ratio", {})
    print(f"base {b}: client {g('client_sec'):.1f} s/field ({g('client_cpu'):.0f} cpu-s); join whole-field {g('join_wall'):.1f} s "
          f"({g('join_cpu'):.0f} cpu-s), device {g('join_dev'):.1f} s (no prefilter {g('join_dev_nomid'):.1f}), host {g('join_host'):.0f} thread-s; "
          f"ratio {rr.get('mean', float('nan')):.1f} ({rr.get('min', float('nan')):.1f}-{rr.get('max', float('nan')):.1f})"
          + (f"; devtops {g('dt_wall'):.1f} s, ratio {agg['ratio_dt']['mean']:.1f}" if "ratio_dt" in agg else "")
          + (f"; client pinned {g('clientp_sec'):.1f} s, ratio {agg['ratio_pinned']['mean']:.1f} (devtops {agg['ratio_pinned_dt']['mean']:.1f})" if "ratio_pinned" in agg else ""))
(HERE / "results" / "bench_summary.json").write_text(json.dumps(out, indent=1) + "\n")
