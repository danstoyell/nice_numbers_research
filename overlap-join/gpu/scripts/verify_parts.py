#!/usr/bin/env python3
"""GPU vs CPU prototype on random partitions of the production 1e14 fields
used by bench_pair.py (attack/d5-client-join/bench_pair.jsonl): 5 fields each
at bases 57, 60 (t,k,p = 9,6,2) and 64 (10,6,2). Per field NPART random
partition values (seeded); survivor sets, match counts, device-rebuilt n and
hits must be equal. Output: results/verify_parts.jsonl (one line per field,
checkpointed; rerun to resume)."""
import json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
B = os.environ.get("JOIN_GPU", "/private/tmp/nice-rust/target-gpu/release/overlap_join_gpu")
OUT = HERE / "results" / os.environ.get("VERIFY_OUT", "verify_parts.jsonl")
NPART = int(os.environ.get("NPART", "8"))
FIELD = 10**14
FIELDS = {
    57: ((9, 6, 2), [79228699893042801193, 43926999893042801193, 65042299893042801193, 70427299893042801193, 64061199893042801193]),
    60: ((9, 6, 2), [793163612114824200908, 1901287712114824200908, 1801504012114824200908, 860689812114824200908, 1244055012114824200908]),
    64: ((10, 6, 2), [41242006262957161709568, 57785162662957161709568, 65552385962957161709568, 39399613562957161709568, 68936001062957161709568]),
}
done = set()
if OUT.exists():
    for line in OUT.read_text().splitlines():
        d = json.loads(line)
        done.add((d["base"], d["start"]))
allok = True
for b, ((t, k, p), fields) in FIELDS.items():
    for s in fields:
        if (b, str(s)) in done:
            continue
        r = subprocess.run([B, "verify-parts", str(b), str(s), str(s + FIELD), str(t), str(k), str(p), str(NPART), str(s % 1000003)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("FAILED TO RUN", b, s, r.stderr[-2000:], flush=True)
            allok = False
            continue
        d = json.loads(r.stdout)
        with OUT.open("a") as f:
            f.write(json.dumps(d) + "\n")
        allok &= d["exact"]
        print("PASS" if d["exact"] else "FAIL", b, s, "parts", d["part_values"], "survivors", d["gpu_survivors"], d["cpu_survivors"],
              "matches", d["gpu_matches"], d["cpu_matches"], "hits", d["gpu_hits"], flush=True)
tot = [json.loads(l) for l in OUT.read_text().splitlines()]
print("fields", len(tot), "partitions", sum(d["parts"] for d in tot), "survivors", sum(d["gpu_survivors"] for d in tot),
      "matches", sum(d["gpu_matches"] for d in tot), "ALL EXACT" if all(d["exact"] for d in tot) else "MISMATCH")
sys.exit(0 if allok and all(d["exact"] for d in tot) else 1)
