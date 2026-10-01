#!/usr/bin/env python3
"""Validation of the client's stratified per-field estimate: the client's
own CubeCL pipeline on one WHOLE 1e14 production field per base (a single
contiguous field, exactly as a fleet client receives it), default settings,
and, if JOIN_GPU_METAL is set, the same with the binary built with the
client's experimental `cubecl-metal` feature (MSL emitted directly instead of
WGSL through naga). Output: results/client_fullfield.jsonl (checkpointed)."""
import json, os, subprocess, time
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
B = os.environ.get("JOIN_GPU", "/private/tmp/nice-rust/target-gpu/release/overlap_join_gpu")
BM = os.environ.get("JOIN_GPU_METAL")
OUT = HERE / "results" / "client_fullfield.jsonl"
FIELD = 10**14
FIELDS = {57: [79228699893042801193], 60: [1801504012114824200908], 64: [41242006262957161709568]}
if os.environ.get("ALLFIELDS") == "1":
    FIELDS = {57: [79228699893042801193, 43926999893042801193, 65042299893042801193, 70427299893042801193, 64061199893042801193],
              60: [793163612114824200908, 1901287712114824200908, 1801504012114824200908, 860689812114824200908, 1244055012114824200908],
              64: [41242006262957161709568, 57785162662957161709568, 65552385962957161709568, 39399613562957161709568, 68936001062957161709568]}
bases = [int(x) for x in os.environ.get("BASES", "57,60,64").split(",")]
done = set()
if OUT.exists():
    for l in OUT.read_text().splitlines():
        d = json.loads(l)
        done.add((d["base"], d["build"], d["field_start"]))
for b, s in [(b, s) for b in bases for s in FIELDS[b]]:
    for build, binary in [("wgsl", B)] + ([("msl", BM)] if BM else []):
        if (b, build, str(s)) in done:
            continue
        # warm-up piece (kernel JIT, floor controller) in the same process is
        # not possible with client-range; use a separate short run first.
        subprocess.run([binary, "client-range", str(b), str(s - 10**11), str(s)], capture_output=True, text=True)
        t0 = time.time()
        r = subprocess.run([binary, "client-range", str(b), str(s), str(s + FIELD)], capture_output=True, text=True)
        if r.returncode != 0:
            print("ERR", b, build, r.stderr[-800:])
            continue
        d = json.loads(r.stdout)
        rec = {"base": b, "build": build, "field_start": str(s), "wall": d["res"]["wall"], "cpu": d["res"]["cpu_secs"],
               "device_wait": d["res"]["device_wait"], "cpu_wait": d["res"]["cpu_wait"], "floor_end": d["res"]["floor_end"],
               "hits": d["res"]["hits"], "valid_numbers": d["res"]["valid_numbers"], "ranges": d["res"]["ranges"], "raw": d}
        with OUT.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(b, build, f"whole field {rec['wall']:.1f} s, cpu {rec['cpu']:.0f} s, dev_wait {rec['device_wait']:.1f}, "
              f"floor_end {rec['floor_end']}, hits {rec['hits']}", flush=True)
