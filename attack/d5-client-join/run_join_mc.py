#!/usr/bin/env python3
"""Run join_mc on bases 34, 38, 40 (validation against the exact join) and
57-64 (the comparison). Checkpointed per base into join_mc.json."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
from verify import candidate_intervals
OUT = HERE / "join_mc.json"
db = json.loads(OUT.read_text()) if OUT.exists() else {}
for b, ns in [(int(x.split(":")[0]), int(x.split(":")[1])) for x in sys.argv[1:]]:
    if str(b) in db and db[str(b)]["n"] >= ns:
        continue
    iv, = candidate_intervals(b)
    r = subprocess.run([str(HERE / "join_mc"), str(b), str(iv["lo"]), str(iv["hi"]), str(ns), "7", "2"],
                       capture_output=True, text=True, check=True)
    db[str(b)] = json.loads(r.stdout)
    OUT.write_text(json.dumps(db) + "\n")
    print(b, "done", db[str(b)]["n"], flush=True)
