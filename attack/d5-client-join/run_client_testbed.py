#!/usr/bin/env python3
"""Run the client reimplementation (client_count.c) on the exact testbed.

Cases are exactly those of attack/p1-algorithm/testbed.json: nice bases 25-40,
twice-nice 15-22, thrice-nice 13-14. Each interval [lo, hi] is processed as the
CPU client does (1e6 chunks aligned at lo, MSD floor 8000, stride k = 3), cut
into segments that are checkpointed to client_segments.jsonl, so an
interrupted run resumes. Every reported hit is re-verified with exact Python
integers and the hit list must equal the known complete solution list.

Usage: python3 run_client_testbed.py [nice|twice|thrice|all] [--floor F] [--threads T]
Output: client_testbed.json (merged per case).
"""
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals  # noqa: E402

BIN = HERE / "client_count"
SEG_LOG = HERE / "client_segments.jsonl"
OUT = HERE / "client_testbed.json"
CHUNK = 10 ** 6
SEG_CHUNKS = 50_000          # 5e10 numbers per checkpointed segment


def is_k_nice(n, b, K):
    cnt = Counter()
    for x in (n * n, n ** 3):
        while x:
            x, d = divmod(x, b)
            cnt[d] += 1
    return len(cnt) == b and all(v == K for v in cnt.values())


def cases(kind):
    tb = json.loads((ROOT / "attack/p1-algorithm/testbed.json").read_text())
    if kind == "nice":
        for b in range(25, 41):
            ivs = candidate_intervals(b)
            if not ivs or b % 4 == 3 or f"nice-{b}" not in tb:
                continue
            iv, = ivs
            yield f"nice-{b}", b, 1, iv["lo"], iv["hi"], []
        return
    K = {"twice": 2, "thrice": 3}[kind]
    rng = {"twice": (15, 22), "thrice": (13, 14)}[kind]
    rows = json.loads((ROOT / f"critique/results/{kind}-nice.json").read_text())["rows"]
    for r in rows:
        if r.get("searched") and rng[0] <= r["base"] <= rng[1] and f"{kind}-{r['base']}" in tb:
            yield (f"{kind}-{r['base']}", r["base"], K, int(r["lo"]), int(r["hi"]),
                   sorted(int(x) for x in r["solutions"]))


def load_segments():
    done = {}
    if SEG_LOG.exists():
        for line in SEG_LOG.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                done[(d["case"], d["floor"], d["seg"])] = d
    return done


SUM_KEYS = ["chunks", "analyses", "rejected_nodes", "leaves", "rejected_n", "leaf_n", "msd_digits",
            "hall_calls", "visits", "mask_rejects", "full_checks", "full_digits", "hits"]


def run_case(name, b, K, lo, hi, known, floor, threads):
    done = load_segments()
    hix = hi + 1
    nchunks = (hix - lo + CHUNK - 1) // CHUNK
    nseg = (nchunks + SEG_CHUNKS - 1) // SEG_CHUNKS
    tot = {k: 0 for k in SUM_KEYS}
    cert = dom = 0.0
    sols = []
    for s in range(nseg):
        key = (name, floor, s)
        if key not in done:
            a = lo + s * SEG_CHUNKS * CHUNK
            e = min(hix, a + SEG_CHUNKS * CHUNK)
            res = subprocess.run([str(BIN), "range", str(b), str(K), str(a), str(e), str(lo), str(CHUNK),
                                  str(floor), str(threads), "1"], capture_output=True, text=True)
            if res.returncode:
                raise RuntimeError(res.stderr)
            d = json.loads(res.stdout)
            d.update({"case": name, "floor": floor, "seg": s})
            with SEG_LOG.open("a") as f:
                f.write(json.dumps(d) + "\n")
            done[key] = d
            print(f"  {name} seg {s + 1}/{nseg} visits={d['visits']:.3e} full={d['full_checks']:.3e}", flush=True)
        d = done[key]
        for k in SUM_KEYS:
            tot[k] += int(d[k])
        cert += d["cert_per_visit"] * d["visits"]
        dom += d["doms_per_visit"] * d["visits"]
        sols += d["solutions"]
    sols = sorted(sols)
    for n in sols:
        assert is_k_nice(n, b, K), (name, n)
    assert sols == known, (name, sols, known)
    tot.update({"case": name, "base": b, "mult": K, "lo": lo, "hi": hi, "N": hi - lo + 1, "floor": floor,
                "chunk": CHUNK, "stride_residues": d["stride_residues"], "stride_modulus": d["stride_modulus"],
                "cert_per_visit": cert / max(tot["visits"], 1), "doms_per_visit": dom / max(tot["visits"], 1),
                "solutions": sols, "known_solutions": known, "verified_exact": True,
                "ops": tot["analyses"] + tot["visits"] + tot["full_checks"]})
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", nargs="?", default="all")
    ap.add_argument("--floor", type=int, default=8000)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--only", default=None, help="comma-separated case names")
    args = ap.parse_args()
    kinds = ["thrice", "twice", "nice"] if args.kind == "all" else [args.kind]
    db = json.loads(OUT.read_text()) if OUT.exists() else {}
    for kind in kinds:
        for name, b, K, lo, hi, known in cases(kind):
            if args.only and name not in args.only.split(","):
                continue
            row = run_case(name, b, K, lo, hi, known, args.floor, args.threads)
            db[f"{name}@{args.floor}"] = row
            OUT.write_text(json.dumps(db, indent=1) + "\n")
            print(f"{name} floor={args.floor} N={row['N']:.3e} analyses={row['analyses']:.3e} visits={row['visits']:.3e} "
                  f"full={row['full_checks']:.3e} ops={row['ops']:.3e} sols={len(row['solutions'])}/{len(known)}", flush=True)


if __name__ == "__main__":
    main()
