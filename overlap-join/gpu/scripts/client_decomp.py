#!/usr/bin/env python3
"""Where does the client's GPU time go on this device? For one production
field per base: the client's CubeCL pipeline with the MSD floor PINNED
(NICE_GPU_MSD_FLOOR, which also disables the controller's clamp) at several
floors, same stratified pieces each time (100 strata x 1e11, fixed seed), and
the exact operation counts of the client's GPU pipeline at the same floors
from D5's validated counting reimplementation (client_count256, 1e6 chunks =
the GPU's PROCESSING_CHUNK_SIZE, FULL=0: full checks counted, not run).
Fit: device seconds per field = a * stride visits + c * full checks
(least squares over floors), giving per-operation device costs.
Also records the steered (production) run for comparison.
Output: results/client_decomp.jsonl (checkpointed)."""
import json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
B = os.environ.get("JOIN_GPU", "/private/tmp/nice-rust/target-gpu/release/overlap_join_gpu")
CC = str(HERE.parent.parent / "attack" / "d5-client-join" / "client_count256")
OUT = HERE / "results" / os.environ.get("DECOMP_OUT", "client_decomp.jsonl")
FIELD = 10**14
FIELDS = {57: 79228699893042801193, 60: 1801504012114824200908, 64: 41242006262957161709568}
FLOORS = [15625, 31250, 62500, 125000, 250000, 500000]
NCOUNT = int(os.environ.get("NCOUNT", "3000"))
bases = [int(x) for x in os.environ.get("BASES", "57,60,64").split(",")]
done = set()
if OUT.exists():
    for l in OUT.read_text().splitlines():
        d = json.loads(l)
        done.add((d["base"], d["kind"], d["floor"]))
for b in bases:
    s = FIELDS[b]
    e = s + FIELD
    for fl in FLOORS:
        if (b, "count", fl) not in done:
            r = subprocess.run([CC, "sample", str(b), "1", str(s), str(e), str(s), str(10**6), str(fl), "8", "0", str(NCOUNT), "11"],
                               capture_output=True, text=True, check=True)
            d = json.loads(r.stdout)
            sc = FIELD / (int(d["chunks"]) * 10**6)
            rec = {"base": b, "kind": "count", "floor": fl, "field_start": str(s), "scale": sc,
                   "per_field": {k: float(d[k]) * sc for k in ("analyses", "leaves", "visits", "mask_rejects", "full_checks")},
                   "leaf_n_per_field": float(d["leaf_n"]) * sc, "raw": d}
            with OUT.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            print(b, "count", fl, {k: f"{v:.3g}" for k, v in rec["per_field"].items()}, flush=True)
        if (b, "gpu", fl) not in done:
            env = dict(os.environ, NICE_GPU_MSD_FLOOR=str(fl))
            r = subprocess.run([B, "client-strat", str(b), str(s), str(e), "100", str(10**11), "4242"], capture_output=True, text=True, env=env)
            if r.returncode != 0:
                print("ERR", r.stderr[-800:])
                continue
            d = json.loads(r.stdout)
            rec = {"base": b, "kind": "gpu", "floor": fl, "field_start": str(s), "est_field_sec": d["est_field_sec"],
                   "est_field_cpu": d["est_field_cpu"], "device_wait": d["res"]["device_wait"], "cpu_wait": d["res"]["cpu_wait"], "raw": d}
            with OUT.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            print(b, "gpu", fl, f"{d['est_field_sec']:.1f} s/field, cpu {d['est_field_cpu']:.0f}, dev_wait {rec['device_wait']:.1f} cpu_wait {rec['cpu_wait']:.1f}", flush=True)
    if (b, "gpu", 0) not in done:
        r = subprocess.run([B, "client-strat", str(b), str(s), str(e), "100", str(10**11), "4242"], capture_output=True, text=True)
        d = json.loads(r.stdout)
        rec = {"base": b, "kind": "gpu", "floor": 0, "steered": True, "field_start": str(s), "est_field_sec": d["est_field_sec"],
               "est_field_cpu": d["est_field_cpu"], "device_wait": d["res"]["device_wait"], "cpu_wait": d["res"]["cpu_wait"], "raw": d}
        with OUT.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(b, "gpu steered", f"{d['est_field_sec']:.1f} s/field floors {d['res']['floor_min']}..{d['res']['floor_max']} end {d['res']['floor_end']}", flush=True)
# fit
recs = [json.loads(l) for l in OUT.read_text().splitlines()]
for b in bases:
    cnt = {r["floor"]: r["per_field"] for r in recs if r["base"] == b and r["kind"] == "count"}
    gpu = {r["floor"]: r for r in recs if r["base"] == b and r["kind"] == "gpu" and r["floor"] in cnt}
    xs = [(cnt[f]["visits"], cnt[f]["full_checks"], gpu[f]["est_field_sec"], f) for f in sorted(gpu) if gpu[f]["device_wait"] > 0.5 * gpu[f]["raw"]["res"]["wall"]]
    if len(xs) >= 2:
        # least squares for t = a v + c F (no intercept)
        svv = sum(v * v for v, F, t, _ in xs); sff = sum(F * F for v, F, t, _ in xs); svf = sum(v * F for v, F, t, _ in xs)
        svt = sum(v * t for v, F, t, _ in xs); sft = sum(F * t for v, F, t, _ in xs)
        det = svv * sff - svf * svf
        a = (svt * sff - sft * svf) / det
        c = (sft * svv - svt * svf) / det
        print(f"base {b}: device-bound floors {[x[3] for x in xs]}: {a*1e12:.2f} ps per stride visit, {c*1e9:.3f} ns per full check")
        for v, F, t, f in xs:
            print(f"   floor {f}: visits {v:.3g} full {F:.3g}: measured {t:.1f} s, model {a*v + c*F:.1f} s (visits {a*v:.1f} + full {c*F:.1f})")
