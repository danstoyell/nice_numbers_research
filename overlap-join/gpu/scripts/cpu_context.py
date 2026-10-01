#!/usr/bin/env python3
"""CPU-only context on the same 15 production fields, this machine, all 10
cores: the client's own CPU niceonly path (process_range_niceonly, stride
k = 3, MSD floor 8000) on NCHUNK random 1e9 chunks, and the CPU prototype
join (join-proto, copied as proto.rs) on NPART random partitions, one
partition per thread, same (t, k, p) as the GPU runs; interleaved per field.
The single-thread paired numbers of D5 (attack/d5-client-join/bench_pair.jsonl)
are quoted alongside by report_tables.py. Output: results/cpu_context.jsonl."""
import json, os, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
B = os.environ.get("JOIN_GPU_CPU", "/private/tmp/nice-rust/overlap_join_gpu.cpumodes")
OUT = HERE / "results" / "cpu_context.jsonl"
NCHUNK, NPART, NTH = int(os.environ.get("NCHUNK", "200")), int(os.environ.get("NPART", "40")), 10
FIELD = 10**14
FIELDS = {
    57: ((9, 6, 2), [79228699893042801193, 43926999893042801193, 65042299893042801193, 70427299893042801193, 64061199893042801193]),
    60: ((9, 6, 2), [793163612114824200908, 1901287712114824200908, 1801504012114824200908, 860689812114824200908, 1244055012114824200908]),
    64: ((10, 6, 2), [41242006262957161709568, 57785162662957161709568, 65552385962957161709568, 39399613562957161709568, 68936001062957161709568]),
}
done = set()
if OUT.exists():
    for l in OUT.read_text().splitlines():
        d = json.loads(l)
        done.add((d["mode"], d["base"], d["start"]))
for b, ((t, k, p), fields) in FIELDS.items():
    for i, s in enumerate(fields):
        e = s + FIELD
        runs = [("cpu-join", [str(b), str(s), str(e), str(t), str(k), str(p), str(NPART), str(s % 99991), str(NTH)]),
                ("cpu-client", [str(b), str(s), str(e), str(10**9), str(NCHUNK), str(s % 99989), str(NTH)])]
        if i % 2:
            runs.reverse()
        for mode, args in runs:
            if (mode, b, str(s)) in done:
                continue
            r = subprocess.run([B, mode] + args, capture_output=True, text=True)
            if r.returncode != 0:
                print("ERR", mode, b, s, r.stderr[-500:], flush=True)
                continue
            d = json.loads(r.stdout)
            with OUT.open("a") as f:
                f.write(json.dumps(d) + "\n")
            print(mode, b, s, f"{d['est_field_sec']:.0f} s/field wall on {NTH} threads, {d['est_field_cpu']:.0f} cpu-s/field, hits {d['hits']}", flush=True)
