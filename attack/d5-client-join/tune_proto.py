#!/usr/bin/env python3
"""Parameter sweep of join_proto on one field (single thread): est. field seconds
and component times per (t,k,p). Appends to tune_proto.jsonl.
Usage: python3 tune_proto.py B S T:K:P ..."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
import os
J = os.environ.get("JOIN_PROTO", "/private/tmp/nice-rust/target/release/join_proto")
b, s = int(sys.argv[1]), int(sys.argv[2])
for spec in sys.argv[3:]:
    t, k, p = spec.split(":")
    d = json.loads(subprocess.run([J, "field", str(b), str(s), str(s + 10**14), t, k, p, "24", "5"],
                                  capture_output=True, text=True, check=True).stdout)
    sc = d["scale"]
    rec = {"binary": J, "base": b, "field_start": s, "t": int(t), "k": int(k), "p": int(p), "est_field_sec": d["est_field_sec"],
           "sec": {"tlay": d["sec_tlay"], "top_ext": d["sec_top_ext"] * sc, "bottom": d["sec_bottom"] * sc, "join": d["sec_join"] * sc},
           "ops": {x: d["est_" + x] for x in ("top_calls", "bottom_calls", "lookups", "matches", "survivors")},
           "bottoms_per_partition": d["bottoms"] / max(d["partitions"], 1)}
    with (HERE / "tune_proto.jsonl").open("a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec), flush=True)
