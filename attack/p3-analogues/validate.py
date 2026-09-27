#!/usr/bin/env python3
"""Validate knice.c against every searched row of the critique's k-nice results.

For each known (k, base): run the enumerator with filters on, for several J
(low-digit depth), and compare the solution set with the JSON exactly. Where
the interval is small, also run with filters off (plain enumeration of every
residue) and an independent Python brute force.

Usage: python3 validate.py [--threads 5] [--max-count 3e11]
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from run import choose_j, interval, is_k_nice  # noqa: E402


def run(k, b, j, filters, threads, tag):
    cmd = [sys.executable, str(HERE / "run.py"), "--k", str(k), "--base", str(b), "--j", str(j),
           "--threads", str(threads), "--filters", str(filters), "--tag", tag]
    log_glob = f"k{k}_b{b}_j{j}_c*{'' if filters else '_nofilter'}_{tag}.log"
    for old in (HERE / "logs").glob(log_glob):
        old.unlink()  # validation always starts fresh
    t0 = time.monotonic()
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    res = json.loads(out.strip().splitlines()[-1])
    res["wall"] = time.monotonic() - t0
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--max-count", type=float, default=3e11)
    ap.add_argument("--output", default=str(HERE / "results" / "validation.json"))
    args = ap.parse_args()
    rows = []
    for k, fname in ((2, "twice-nice.json"), (3, "thrice-nice.json")):
        known = json.loads((ROOT / "critique" / "results" / fname).read_text())
        for r in known["rows"]:
            if not r.get("searched"):
                continue
            b = r["base"]
            lo, hi, s, c = interval(b, k)
            assert (str(lo), str(hi)) == (r["lo"], r["hi"])
            if hi - lo + 1 > args.max_count:
                continue
            want = sorted(int(x) for x in r["solutions"])
            jdef = choose_j(b, k, lo, hi, s, 20000)
            js = sorted({j for j in (1, 2, 3) if j < s and (b - 1) * b ** j <= 100 * (hi - lo + 1)}
                        | {1, jdef})
            for j in js:
                for filters in ((1, 0) if hi - lo < 5e8 else (1,)):
                    res = run(k, b, j, filters, args.threads, "val")
                    got = sorted(int(x) for x in res["solutions"])
                    ok = got == want and res["complete"]
                    row = {"k": k, "base": b, "J": j, "filters": filters, "count": hi - lo + 1,
                           "want": len(want), "got": len(got), "match": ok,
                           "lane_steps": res["lane_steps"], "hash_survivors": res["hash_survivors"],
                           "wall": round(res["wall"], 3)}
                    print(json.dumps(row), flush=True)
                    rows.append(row)
                    assert ok, (k, b, j, filters, want, got)
            if hi - lo < 3_000_000:
                brute = [n for n in range(lo, hi + 1) if is_k_nice(n, b, k)]
                assert brute == want, (k, b, brute, want)
                rows.append({"k": k, "base": b, "python_bruteforce": len(brute), "match": True})
    Path(args.output).write_text(json.dumps({"rows": rows}, indent=1) + "\n")
    print("ALL MATCH", len(rows))


if __name__ == "__main__":
    main()
