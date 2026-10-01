#!/usr/bin/env python3
"""Markdown tables for the report from results/bench_final.jsonl (final,
fixed build), results/client_fullfield.jsonl, results/client_decomp.jsonl and
the CPU context runs (results/cpu_context.jsonl, D5 bench_pair.jsonl).
Sampling error: the client's three rounds are independent stratified 10%
samples of the field; per field we report the mean and the standard error
across rounds; per base the mean over the 5 fields with the range of the
per-field ratios."""
import json, statistics as S
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
R = HERE / "results"
recs = [json.loads(l) for l in open(R / "bench_final.jsonl") if l.strip()]
bad = [r for r in recs if "error" in r]
recs = [r for r in recs if "error" not in r]
per = defaultdict(lambda: defaultdict(list))
for r in recs:
    k = (r["base"], r["field_start"])
    m = r["method"]
    if m == "join":
        per[k]["jw"].append(r["field_wall"]); per[k]["jc"].append(r["field_cpu"]); per[k]["jd"].append(r["est_device_sec"])
        per[k]["jd0"].append(r["est_device_sec_nomid"]); per[k]["jh"].append(r["est_host_cpu_sec"])
        per[k]["surv"].append(r["field_survivors"]); per[k]["pref"].append(r["field_prefilter_survivors"]); per[k]["jhits"].append(len(r["field_hits"]))
    elif m == "join-devtops":
        per[k]["dw"].append(r["field_wall"]); per[k]["dc"].append(r["field_cpu"]); per[k]["dsurv"].append(r["field_survivors"])
    elif m == "client":
        per[k]["cw"].append(r["est_field_sec"]); per[k]["cc"].append(r["est_field_cpu"]); per[k]["chits"].append(len(r["hits"]))
    elif m == "client-pinned":
        per[k]["pw"].append(r["est_field_sec"]); per[k]["pc"].append(r["est_field_cpu"])
mean = lambda v: S.mean(v) if v else float("nan")
se = lambda v: S.stdev(v) / len(v) ** 0.5 if len(v) > 1 else float("nan")
print(f"records {len(recs)}, errors {len(bad)}")
print("\n| b | field start | client, fleet default (s) | client, best pinned floor (s) | join, host tops (s) | join, device tops (s) | join device only (s) | ratio default / join | ratio pinned / join | ratio default / join-devtops |")
print("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|")
bb = defaultdict(lambda: defaultdict(list))
for (b, f), d in sorted(per.items()):
    cw, pw, jw, dw, jd = mean(d["cw"]), mean(d["pw"]), mean(d["jw"]), mean(d["dw"]), mean(d["jd"])
    row = dict(cw=cw, pw=pw, jw=jw, dw=dw, jd=jd, jd0=mean(d["jd0"]), jc=mean(d["jc"]), dc=mean(d["dc"]), cc=mean(d["cc"]), pc=mean(d["pc"]), jh=mean(d["jh"]),
               r=cw / jw, rp=pw / jw, rd=cw / dw, rpd=pw / dw, cse=se(d["cw"]) / cw, pse=se(d["pw"]) / pw, jse=se(d["jw"]) / jw, surv=mean(d["surv"]), pref=mean(d["pref"]))
    for x, v in row.items():
        bb[b][x].append(v)
    print(f"| {b} | {f} | {cw:.0f} ± {se(d['cw']):.0f} | {pw:.0f} ± {se(d['pw']):.0f} | {jw:.1f} ± {se(d['jw']):.1f} | {dw:.1f} ± {se(d['dw']):.1f} | {jd:.1f} | "
          f"{cw/jw:.1f}× | {pw/jw:.1f}× | {cw/dw:.1f}× |")
print("\nPer base (mean over 5 fields; ratio = mean of per-field ratios, range in brackets):\n")
print("| b | client default (s) | client pinned (s) | join host tops (s) | join device tops (s) | join device only (s) / no prefilter | default / join | pinned / join | default / devtops | pinned / devtops |")
print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
out = {}
for b, d in sorted(bb.items()):
    g = lambda x: mean(d[x])
    rng = lambda x: f"{g(x):.1f}× ({min(d[x]):.1f}–{max(d[x]):.1f})"
    print(f"| {b} | {g('cw'):.0f} | {g('pw'):.0f} | {g('jw'):.1f} | {g('dw'):.1f} | {g('jd'):.1f} / {g('jd0'):.1f} | {rng('r')} | {rng('rp')} | {rng('rd')} | {rng('rpd')} |")
    out[b] = {x: {"mean": g(x), "min": min(d[x]), "max": max(d[x])} for x in d}
print("\nHost CPU per field (process CPU-seconds, all threads) and cores to keep the GPU fed:\n")
print("| b | client default: cpu-s / wall s = cores | client pinned: cpu-s / wall s = cores | join host tops: cpu-s / device s = cores | join device tops: cpu-s / wall s = cores |")
print("|---:|---|---|---|---|")
for b, d in sorted(bb.items()):
    g = lambda x: mean(d[x])
    print(f"| {b} | {g('cc'):.0f} / {g('cw'):.0f} = {g('cc')/g('cw'):.1f} | {g('pc'):.0f} / {g('pw'):.0f} = {g('pc')/g('pw'):.1f} | "
          f"{g('jc'):.0f} / {g('jd'):.1f} = {g('jc')/g('jd'):.1f} | {g('dc'):.1f} / {g('dw'):.1f} = {g('dc')/g('dw'):.2f} |")
print("\nRelative sampling/timing error (mean over fields of per-field SE/mean): ")
for b, d in sorted(bb.items()):
    print(f"  b{b}: client default {100*mean(d['cse']):.1f}%, client pinned {100*mean(d['pse']):.1f}%, join (timing noise only) {100*mean(d['jse']):.1f}%")
print("\nHits: client", sum(sum(v["chits"]) for v in per.values()), "join", sum(sum(v["jhits"]) for v in per.values()))
(R / "report_tables.json").write_text(json.dumps(out, indent=1) + "\n")
# whole-field validation
ff = [json.loads(l) for l in open(R / "client_fullfield.jsonl")]
print("\nWhole-field client runs vs stratified estimate (same field):")
for x in ff:
    k = (x["base"], x["field_start"])
    print(f"  b{x['base']} {x['field_start']}: whole field {x['wall']:.1f} s; stratified (final bench, 3 rounds) {mean(per[k]['cw']):.1f} ± {se(per[k]['cw']):.1f} s")

# ---- headline: whole-field client (one run per field, default steered config) vs whole-field join (3 rounds)
print("\nHEADLINE (no sampling on either side): whole-field client run vs whole-field join (mean of 3 interleaved rounds)\n")
print("| b | field start | client whole field (s) | client stratified est. (s) | bias of estimate | join host tops (s) | join device tops (s) | ratio vs join | ratio vs join-devtops |")
print("|---:|---|---:|---:|---:|---:|---:|---:|---:|")
ffd = {(x["base"], x["field_start"]): x for x in ff if x["build"] == "wgsl"}
hb = defaultdict(lambda: defaultdict(list))
for (b, f), d in sorted(per.items()):
    if (b, f) not in ffd:
        continue
    cw = ffd[(b, f)]["wall"]
    st, jw, dw = mean(d["cw"]), mean(d["jw"]), mean(d["dw"])
    pin_rel = mean(d["pw"]) / st
    hb[b]["r"].append(cw / jw); hb[b]["rd"].append(cw / dw); hb[b]["bias"].append(st / cw - 1)
    hb[b]["rp"].append(cw * pin_rel / jw); hb[b]["rpd"].append(cw * pin_rel / dw)
    hb[b]["cw"].append(cw); hb[b]["jw"].append(jw); hb[b]["dw"].append(dw); hb[b]["ccpu"].append(ffd[(b, f)]["cpu"])
    print(f"| {b} | {f} | {cw:.1f} | {st:.0f} | {100*(st/cw-1):+.0f}% | {jw:.1f} | {dw:.1f} | {cw/jw:.1f}× | {cw/dw:.1f}× |")
print("\n| b | fields | client whole field, mean (s) | join (s) | join devtops (s) | client / join | client / join-devtops | client best-floor (scaled) / join | client best-floor / join-devtops | stratified bias |")
print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for b, d in sorted(hb.items()):
    m = lambda k: mean(d[k])
    r = lambda k: f"{m(k):.1f}× ({min(d[k]):.1f}–{max(d[k]):.1f}, sd {S.stdev(d[k]) if len(d[k])>1 else float('nan'):.1f})"
    print(f"| {b} | {len(d['r'])} | {m('cw'):.0f} | {m('jw'):.1f} | {m('dw'):.1f} | {r('r')} | {r('rd')} | {r('rp')} | {r('rpd')} | {100*m('bias'):+.0f}% ({100*min(d['bias']):+.0f}…{100*max(d['bias']):+.0f}%) |")
