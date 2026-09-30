#!/usr/bin/env python3
"""Step 4 measurement: the join prototype vs the client's own CPU path on
production-sized base-57 (and 60, 64) fields, single thread, same machine.

For each base, NFIELDS random production fields (lo + i*1e14, 1e14 wide):
  join  : join_proto field B S E T K P NPART SEED  -> per-field seconds and
          operation counts, extrapolated from NPART random partitions of b^P
          (the top layer is built once per field, as it would be)
  client: join_proto client B S E 1e9 NSAMP SEED    -> the client's own
          process_range_niceonly (nice_common, stride k = 3, floor 8000) on
          NSAMP random 1e9 chunks of the same field (the CPU chunk for 1e14 fields)
  client ops: client_count256 sample on the same field (exact client counting)
Checkpointed per (base, field) in bench_proto.jsonl.
Usage: python3 bench_proto.py B:T:K:P:NFIELDS ...
"""
import json, random, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
from verify import candidate_intervals
import os
J = os.environ.get("JOIN_PROTO", "/private/tmp/nice-rust/target/release/join_proto")
C = str(HERE / "client_count256")
LOG = HERE / "bench_proto.jsonl"
FIELD, NPART, NSAMP, NCOUNT = 10**14, 24, 40, 40
done = set()
if LOG.exists():
    for line in LOG.read_text().splitlines():
        d = json.loads(line); done.add((d["base"], d["field_start"], d["t"], d["k"], d["p"]))
for spec in sys.argv[1:]:
    b, t, k, p, nf = map(int, spec.split(":"))
    iv, = candidate_intervals(b)
    lo, hi = iv["lo"], iv["hi"]
    rng = random.Random(1000 + b)
    nfields = (hi - lo) // FIELD
    for fi in range(nf):
        s = lo + rng.randrange(nfields) * FIELD
        e = s + FIELD
        if (b, s, t, k, p) in done:
            continue
        seed = str(rng.randrange(1 << 30))
        jr = json.loads(subprocess.run([J, "field", str(b), str(s), str(e), str(t), str(k), str(p), str(NPART), seed],
                                       capture_output=True, text=True, check=True).stdout)
        cr = json.loads(subprocess.run([J, "client", str(b), str(s), str(e), str(10**9), str(NSAMP), seed],
                                       capture_output=True, text=True, check=True).stdout)
        cc = json.loads(subprocess.run([C, "sample", str(b), "1", str(s), str(e), str(s), str(10**9), "8000", "1", "0",
                                        str(NCOUNT), seed], capture_output=True, text=True, check=True).stdout)
        sc = FIELD / (int(cc["chunks"]) * 10**9)
        client_ops = {k2: int(cc[k2]) * sc for k2 in ("analyses", "visits", "full_checks")}
        rec = {"base": b, "field_start": s, "t": t, "k": k, "p": p, "npart": NPART, "nsamp": NSAMP,
               "join_sec": jr["est_field_sec"], "client_sec": cr["est_field_sec"],
               "join_ops": {x: jr["est_" + x] for x in ("top_calls", "bottom_calls", "lookups", "matches", "survivors")},
               "join_sec_parts": {x: jr[x] for x in ("sec_tlay", "sec_bottom", "sec_top_ext", "sec_join")},
               "join_tlay": jr["tlay"], "join_tlay_calls": jr["tlay_calls"],
               "client_ops": client_ops, "client_hits": cr["hits"], "join_hits": jr["hits"]}
        rec["join_ops_total"] = sum(rec["join_ops"].values())
        rec["client_ops_total"] = sum(client_ops.values())
        rec["sec_ratio"] = rec["client_sec"] / rec["join_sec"] if rec["join_sec"] else None
        rec["ops_ratio"] = rec["client_ops_total"] / rec["join_ops_total"] if rec["join_ops_total"] else None
        with LOG.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"b={b} field {s} (t,k,p)=({t},{k},{p}): join {rec['join_sec']:.0f}s {rec['join_ops_total']:.2e} ops | "
              f"client {rec['client_sec']:.0f}s {rec['client_ops_total']:.2e} ops | time ratio {rec['sec_ratio']}, ops ratio {rec['ops_ratio']}",
              flush=True)
