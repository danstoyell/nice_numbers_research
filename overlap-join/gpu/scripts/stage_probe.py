#!/usr/bin/env python3
"""Device time per stage (unsynced): run `field` with stages cut off / kernel
experiments via env, print device-phase wall. Usage: stage_probe.py B S T K P NPART SLOTS [rep]"""
import json, os, subprocess, sys
B = os.environ.get("JOIN_GPU", "/private/tmp/nice-rust/target-gpu/release/overlap_join_gpu")
b, s, t, k, p, npart, slots = sys.argv[1:8]
reps = int(sys.argv[8]) if len(sys.argv) > 8 else 1
e = str(int(s) + 10**14)
confs = [("bottoms", {"JOIN_STAGES": "1"}), ("+join no-AND", {"JOIN_STAGES": "2", "JOIN_EXP": "1"}),
         ("+join no-walk", {"JOIN_STAGES": "2", "JOIN_EXP": "2"}), ("+join", {"JOIN_STAGES": "2"}),
         ("+prefilter", {"JOIN_STAGES": "3"}), ("+check (all)", {"JOIN_STAGES": "4"})]
for r in range(reps):
    for name, env in confs:
        envx = dict(os.environ, JOIN_NOFENCE="1", **env)
        out = subprocess.run([B, "field", b, s, e, t, k, p, npart, "7", "9", slots], capture_output=True, text=True, env=envx)
        try:
            d = json.loads(out.stdout)
            print(f"{name:16s} devphase {d['device_phase']['device_wall']:.3f}s  est/field {d['est_field_device_sec']:.1f}s  pipelined {d['pipelined']['wall']:.3f}s", flush=True)
        except Exception:
            print(name, "ERR", out.stderr[-300:], flush=True)
