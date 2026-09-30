#!/usr/bin/env python3
"""Rerun P1's overlap join on the testbed with the client's digit-sum filter.

For every testbed case, each join configuration (t, k) that P1 ran
(attack/p1-algorithm/testbed.json) is rerun with join_ds (DS=1): the join
keyed additionally on the digit-sum class, as the client's stride table
filters. The partition depth p is raised if the (key x class) bucket array
would be too large. Every hit is re-verified exactly and must equal the
known list. Results are checkpointed per run in join_ds_runs.jsonl.

Usage: python3 run_join_testbed.py [--only case,case] [--threads 2]
Output: join_ds_testbed.json
"""
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BIN = HERE / "join_ds"
LOG = HERE / "join_ds_runs.jsonl"
OUT = HERE / "join_ds_testbed.json"


def is_k_nice(n, b, K):
    cnt = Counter()
    for x in (n * n, n ** 3):
        while x:
            x, d = divmod(x, b)
            cnt[d] += 1
    return len(cnt) == b and all(v == K for v in cnt.values())


def choose_p(b, o, p0):
    for p in range(p0, o + 1):
        if b ** (o - p) * (b - 1) <= 3e7:
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--threads", type=int, default=2)
    args = ap.parse_args()
    tb = json.loads((ROOT / "attack/p1-algorithm/testbed.json").read_text())
    done = {}
    if LOG.exists():
        for line in LOG.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                done[(d["case"], d["t"], d["k"], d["partition_digits"])] = d
    db = json.loads(OUT.read_text()) if OUT.exists() else {}
    order = {"thrice": 0, "twice": 1, "nice": 2}
    names = [n for n in tb if tb[n]["N"] >= 1e6 and (tb[n]["kind"] != "nice" or tb[n]["base"] >= 25)
             and (tb[n]["kind"] != "twice" or tb[n]["base"] >= 15) and (tb[n]["kind"] != "thrice" or tb[n]["base"] >= 13)]
    names.sort(key=lambda n: (order[tb[n]["kind"]], tb[n]["N"]))
    for name in names:
        if args.only and name not in args.only.split(","):
            continue
        r = tb[name]
        b, K, lo, hi = r["base"], r["mult"], r["lo"], r["hi"]
        runs = []
        for j in r["joins"]:
            t, k = j["t"], j["k"]
            p = choose_p(b, j["overlap"], j["partition_digits"])
            key = (name, t, k, p)
            if key not in done:
                res = subprocess.run([str(BIN), "join", str(b), str(K), str(lo), str(hi), str(r["square_digits"]),
                                      str(r["cube_digits"]), str(t), str(k), str(p), str(args.threads), "1"],
                                     capture_output=True, text=True)
                if res.returncode:
                    raise RuntimeError(res.stderr)
                d = json.loads(res.stdout)
                d["case"] = name
                with LOG.open("a") as f:
                    f.write(json.dumps(d) + "\n")
                done[key] = d
            d = done[key]
            sols = sorted(d["solutions"])
            for n in sols:
                assert is_k_nice(n, b, K), (name, n)
            assert sols == sorted(r["known_solutions"]), (name, sols)
            d["ops"] = d["top_calls"] + d["bottom_calls"] + d["lookups"] + d["matches"] + d["survivors"]
            d["p1_ops_no_ds"] = j["top_calls"] + j["bottom_calls"] + j["matches"] + j["survivors"]
            runs.append(d)
            print(f"{name} (t,k,p)=({t},{k},{p}) ds ops={d['ops']:.3e} [top {d['top_calls']:.2e} bot {d['bottom_calls']:.2e} "
                  f"look {d['lookups']:.2e} match {d['matches']:.2e} surv {d['survivors']:.2e}] vs no-ds {d['p1_ops_no_ds']:.3e}",
                  flush=True)
        best = min(runs, key=lambda x: x["ops"])
        db[name] = {"case": name, "base": b, "mult": K, "N": r["N"], "L": r["L"], "runs": runs,
                    "best": {k: best[k] for k in ("t", "k", "overlap", "partition_digits", "top_calls", "bottom_calls",
                                                  "lookups", "matches", "survivors", "ops", "hits")},
                    "solutions": sorted(best["solutions"]), "verified_exact": True}
        OUT.write_text(json.dumps(db, indent=1) + "\n")


if __name__ == "__main__":
    main()
