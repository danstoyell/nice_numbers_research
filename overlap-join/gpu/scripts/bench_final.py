#!/usr/bin/env python3
"""GPU benchmark on this machine's GPU (Apple M4, wgpu/Metal): the overlap
join's device stage against the client's own CubeCL niceonly pipeline, on the
production 1e14 fields of bench_pair.py (attack/d5-client-join/bench_pair.jsonl;
field bounds [S, S + 1e14) as there), interleaved per field (J C / C J
alternating by round), ROUNDS rounds.

Per field and round:
  join   field-full   every partition of the field through the pipelined
                      run (9 host threads certifying tops + 1 dispatcher):
                      end-to-end wall, process CPU seconds, survivors, hits.
         field        512 random partitions (fresh seed per round): host-only
                      phase and device-only phase measured separately ->
                      per-field device seconds and host core-seconds.
         field MID=0  256 random partitions without the middle-digit
                      prefilter (the join exactly as designed in D5).
  client client-strat the client's begin/finish_niceonly_cubecl on one random
                      1e11 piece from each of 100 equal strata of the field
                      (10% of the field, fresh seed per round) after two
                      untimed warm-up pieces; wall and process CPU seconds
                      scaled to the field. The three rounds are independent
                      stratified estimates; their spread gives the sampling
                      error.
  join-devtops field-full with JOIN_DEVTOPS=1: tops certified on the device
                      too (the host only launches); whole field.
  client-pinned       as client, with the MSD floor pinned (NICE_GPU_MSD_FLOOR)
                      at the best floor per base from client_decomp.py
                      (env PINNED="57:15625,60:...,64:..."): the client's
                      best case on this device, not the fleet default.
  client-metal        as client, but the binary built with the client's
                      experimental `cubecl-metal` feature (MSL emitted directly
                      instead of WGSL through naga), if JOIN_GPU_METAL is set.
METHODS (env) selects and orders the methods; the order rotates by round.
Output: results/$BENCH_OUT (default bench_gpu.jsonl), one record per
(round, method, base, field); rerun to resume.
"""
import json, os, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
B = os.environ.get("JOIN_GPU", "/private/tmp/nice-rust/target-gpu/release/overlap_join_gpu")
OUT = HERE / "results" / os.environ.get("BENCH_OUT", "bench_gpu.jsonl")
ROUNDS = int(os.environ.get("ROUNDS", "3"))
FIELD = 10**14
FIELDS = {
    57: ((9, 6, 2), [79228699893042801193, 43926999893042801193, 65042299893042801193, 70427299893042801193, 64061199893042801193]),
    60: ((9, 6, 2), [793163612114824200908, 1901287712114824200908, 1801504012114824200908, 860689812114824200908, 1244055012114824200908]),
    64: ((10, 6, 2), [41242006262957161709568, 57785162662957161709568, 65552385962957161709568, 39399613562957161709568, 68936001062957161709568]),
}
bases = [int(x) for x in os.environ.get("BASES", "57,60,64").split(",")]
METHODS = os.environ.get("METHODS", "join,client").split(",")
BM = os.environ.get("JOIN_GPU_METAL")
PINNED = {int(k): v for k, v in (x.split(":") for x in os.environ.get("PINNED", "").split(",") if x)}


def run(args, env=None, binary=None):
    e = dict(os.environ, **(env or {}))
    r = subprocess.run([binary or B] + [str(a) for a in args], capture_output=True, text=True, env=e)
    if r.returncode != 0:
        raise RuntimeError(f"{args}: {r.stderr[-1500:]}")
    return json.loads(r.stdout)


done = set()
if OUT.exists():
    for line in OUT.read_text().splitlines():
        d = json.loads(line)
        done.add((d["round"], d["method"], d["base"], d["field_start"]))
for r in range(ROUNDS):
    for b in bases:
        (t, k, p), fields = FIELDS[b]
        for s in fields:
            e = s + FIELD
            seed = (s % 1000003) * 7 + r
            rot = (r + list(FIELDS[b][1]).index(s)) % len(METHODS)
            order = METHODS[rot:] + METHODS[:rot]
            for m in order:
                if (r, m, b, str(s)) in done:
                    continue
                t0 = time.time()
                rec = {"round": r, "method": m, "base": b, "field_start": str(s), "t": t, "k": k, "p": p,
                       "loadavg_before": os.getloadavg(), "time": time.strftime("%Y-%m-%d %H:%M:%S")}
                try:
                    if m == "join":
                        full = run(["field-full", b, s, e, t, k, p, 9, 4])
                        split = run(["field", b, s, e, t, k, p, 512, seed, 9, 4])
                        nomid = run(["field", b, s, e, t, k, p, 256, seed + 1000, 9, 4], {"JOIN_MID": "0"})
                        for d in (full, split, nomid):
                            d.pop("pipelined", None) if False else None
                        rec.update({
                            "field_wall": full["est_field_pipelined_sec"], "field_cpu": full["est_field_pipelined_cpu"],
                            "field_survivors": full["pipelined"]["survivors"], "field_prefilter_survivors": full["pipelined"]["mid_survivors"],
                            "field_tops": full["pipelined"]["tops"], "field_top_calls": full["pipelined"]["top_calls"],
                            "field_hits": full["pipelined"]["hits"], "field_device_wait": full["pipelined"]["device_wait"],
                            "field_host_wait": full["pipelined"]["host_wait"],
                            "est_device_sec": split["est_field_device_sec"], "est_host_cpu_sec": split["est_field_host_cpu_sec"],
                            "est_device_sec_nomid": nomid["est_field_device_sec"],
                            "raw_full": full, "raw_split": split, "raw_nomid": nomid})
                    elif m == "join-devtops":
                        full = run(["field-full", b, s, e, t, k, p, 9, 4], {"JOIN_DEVTOPS": "1"})
                        rec.update({
                            "field_wall": full["est_field_pipelined_sec"], "field_cpu": full["est_field_pipelined_cpu"],
                            "field_survivors": full["pipelined"]["survivors"], "field_prefilter_survivors": full["pipelined"]["mid_survivors"],
                            "field_tops": full["pipelined"]["tops"], "field_hits": full["pipelined"]["hits"], "raw_full": full})
                    else:
                        cenv = {"NICE_GPU_MSD_FLOOR": PINNED[b]} if m == "client-pinned" else None
                        c = run(["client-strat", b, s, e, 100, 10**11, seed], cenv, binary=BM if m == "client-metal" else None)
                        rec["pinned_floor"] = PINNED.get(b) if m == "client-pinned" else None
                        rec.update({"est_field_sec": c["est_field_sec"], "est_field_cpu": c["est_field_cpu"],
                                    "device_wait": c["res"]["device_wait"], "cpu_wait": c["res"]["cpu_wait"],
                                    "hits": c["res"]["hits"], "raw": c})
                except RuntimeError as err:
                    rec["error"] = str(err)
                rec["elapsed"] = time.time() - t0
                with OUT.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
                if "error" in rec:
                    print("ERROR", r, m, b, s, rec["error"][-500:], flush=True)
                elif m == "join-devtops":
                    print(f"r{r} join-devtops b{b} {s}: whole field {rec['field_wall']:.1f}s wall, {rec['field_cpu']:.0f} cpu-s; "
                          f"surv {rec['field_survivors']:.3g} tops {rec['field_tops']:.3g} hits {rec['field_hits']}", flush=True)
                elif m == "join":
                    print(f"r{r} join   b{b} {s}: whole field {rec['field_wall']:.1f}s wall, {rec['field_cpu']:.0f} cpu-s; "
                          f"device {rec['est_device_sec']:.1f}s (no prefilter {rec['est_device_sec_nomid']:.1f}s), host {rec['est_host_cpu_sec']:.0f} core-s; "
                          f"surv {rec['field_survivors']:.3g} hits {rec['field_hits']}", flush=True)
                else:
                    print(f"r{r} {m} b{b} {s}: {rec['est_field_sec']:.1f}s/field, {rec['est_field_cpu']:.0f} cpu-s/field, "
                          f"dev_wait {rec['device_wait']:.1f} cpu_wait {rec['cpu_wait']:.1f} hits {rec['hits']}", flush=True)
print("DONE")
