#!/usr/bin/env python3
"""Paired wall-time comparison, join prototype vs the client's own CPU path,
on the same production-sized fields (1e14), single thread each, interleaved
J C J C ... so that machine load affects both alike.

For each field: ROUNDS rounds; in each round one join_proto `field` run on
NPART random partitions (fresh seed) and one join_proto `client` run on
NSAMP random 1e9 chunks (the client's own process_range_niceonly, fresh seed).
Per-field estimates: join = top layer + mean partition cost x b^p; client =
mean seconds per n x 1e14. Client operation counts from client_count256
(exact client counting, NCOUNT stratified chunks of the field).
Binary: $JOIN_PROTO (default: the Div64 build). Checkpoint: bench_pair.jsonl.
Usage: python3 bench_pair.py B:T:K:P:FIELD_START[,FIELD_START...] ...
"""
import json, os, random, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
J = os.environ.get("JOIN_PROTO", "/private/tmp/nice-rust/target2/release/join_proto")
C = str(HERE / "client_count256")
LOG = HERE / os.environ.get("BENCH_LOG", "bench_pair.jsonl")
FIELD, ROUNDS, NPART, NSAMP, NCOUNT = 10**14, 3, 12, 40, 100


def run(args):
    return json.loads(subprocess.run(args, capture_output=True, text=True, check=True).stdout)


done = set()
if LOG.exists():
    for line in LOG.read_text().splitlines():
        d = json.loads(line)
        done.add((d["base"], d["field_start"], d["t"], d["k"], d["p"]))
for spec in sys.argv[1:]:
    head, fields = spec.rsplit(":", 1)
    b, t, k, p = map(int, head.split(":"))
    for fs in fields.split(","):
        s = int(fs)
        e = s + FIELD
        if (b, s, t, k, p) in done:
            continue
        rng = random.Random(s % (1 << 61))
        jsec, jparts, csec, cn, jops = [], 0, 0.0, 0, None
        tlay_sec = None
        acc = {x: 0.0 for x in ("top_calls", "bottom_calls", "lookups", "matches", "survivors")}
        part_sec = 0.0
        for r in range(ROUNDS):
            jr = run([J, "field", str(b), str(s), str(e), str(t), str(k), str(p), str(NPART), str(rng.randrange(1 << 30))])
            tlay_sec = jr["sec_tlay"] if tlay_sec is None else min(tlay_sec, jr["sec_tlay"])
            part_sec += jr["sec_bottom"] + jr["sec_top_ext"] + jr["sec_join"]
            jparts += jr["npart"]
            for x in acc:
                acc[x] += jr["est_" + x] / ROUNDS
            cr = run([J, "client", str(b), str(s), str(e), str(10**9), str(NSAMP), str(rng.randrange(1 << 30))])
            csec += cr["sec"]
            cn += cr["nsamp"] * 10**9
        nv = b ** p
        join_field = tlay_sec + part_sec / jparts * nv
        client_field = csec / cn * FIELD
        cc = run([C, "sample", str(b), "1", str(s), str(e), str(s), str(10**9), "8000", "1", "0", str(NCOUNT), "3"])
        sc = FIELD / (int(cc["chunks"]) * 10**9)
        cops = {x: int(cc[x]) * sc for x in ("analyses", "visits", "full_checks")}
        rec = {"binary": J, "base": b, "field_start": s, "t": t, "k": k, "p": p, "rounds": ROUNDS, "npart_total": jparts,
               "client_chunks_total": cn // 10**9, "join_field_sec": join_field, "client_field_sec": client_field,
               "time_ratio": client_field / join_field if join_field > 1 else None,
               "join_ops": acc, "join_ops_total": sum(acc.values()), "client_ops": cops, "client_ops_total": sum(cops.values())}
        rec["ops_ratio"] = rec["client_ops_total"] / rec["join_ops_total"] if rec["join_ops_total"] > 1e6 else None
        with LOG.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"b={b} {s} ({t},{k},{p}): join {join_field:.0f}s client {client_field:.0f}s time ratio {rec['time_ratio']} | "
              f"ops join {rec['join_ops_total']:.2e} client {rec['client_ops_total']:.2e} ratio {rec['ops_ratio']}", flush=True)
