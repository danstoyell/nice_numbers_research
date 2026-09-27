#!/usr/bin/env python3
"""Independently recompute public distinct-digit histograms, bin by bin.

Runs critique/scripts/histogram.c over exactly the interval the public
server reports for each base, compares every histogram bin with the dated
public snapshot, and re-verifies every reported near miss (at most two
missing digits) with scripts/verify.py. Also checks the one top-endpoint
candidate the public intervals omit in bases = 2, 3, 4 (mod 5).

Usage: python3 critique/scripts/recompute_histograms.py --bases 20 22 ... --threads 10
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals, verify  # noqa: E402

SCRATCH = Path(os.environ.get("NICE_SCRATCH", "/private/tmp/nice-critique"))


def build():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    binary = SCRATCH / "histogram"
    src = ROOT / "critique/scripts/histogram.c"
    subprocess.run(["clang", "-O3", "-march=native", "-o", str(binary), str(src), "-lpthread"], check=True)
    return binary


def run(binary, base, lo, hi, s, c, threads, report_def, mult=1):
    out = subprocess.run([str(binary), str(base), str(lo), str(hi), str(s), str(c),
                          str(threads), str(report_def), str(mult)],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bases", type=int, nargs="+", required=True)
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--snapshot", default=str(ROOT / "critique/results/public-bases-2026-09-26.json"))
    ap.add_argument("--output", default=str(ROOT / "critique/results/histogram-recompute.json"))
    args = ap.parse_args()
    binary = build()
    snap = {r["id"]: r for r in json.loads(Path(args.snapshot).read_text())["bases"]}
    try:
        report = json.loads(Path(args.output).read_text())
    except FileNotFoundError:
        report = {"scope": "Independent exact recomputation of public detailed histograms",
                  "snapshot": args.snapshot, "rows": []}
    done = {r["base"] for r in report["rows"]}
    for base in args.bases:
        if base in done:
            continue
        iv, = candidate_intervals(base)
        rec = snap[base]
        lo, hi = int(rec["range_start"]), int(rec["range_end"]) - 1
        started = time.monotonic()
        res = run(binary, base, lo, hi, iv["square_digits"], iv["cube_digits"], args.threads, 2)
        seconds = time.monotonic() - started
        assert not res["overflow"]
        public = {x["num_uniques"]: int(x["count"]) for x in rec["distribution"]}
        mismatches = {d: {"public": public.get(d, 0), "recomputed": res["histogram"][d]}
                      for d in range(1, base + 1) if public.get(d, 0) != res["histogram"][d]}
        near = []
        for n_str, distinct in res["reported"]:
            v = verify(int(n_str), base)
            assert v["distinct_digits"] == distinct and v["digit_count"] == base
            near.append({"n": n_str, "distinct": distinct, "missing": v["missing_digits"],
                         "repeated": v["repeated_digits"], "digit_sum_congruence": v["digit_sum_congruence"]})
        endpoint = None
        if iv["hi"] != hi:
            v = verify(iv["hi"], base)
            endpoint = {"n": str(iv["hi"]), "nice": v["nice"], "distinct": v["distinct_digits"]}
        row = {"base": base, "lo": str(lo), "hi": str(hi), "count": hi - lo + 1,
               "seconds": seconds, "threads": args.threads,
               "histogram": res["histogram"], "bins_differing_from_public": mismatches,
               "near_misses_at_most_two_missing": near, "omitted_public_endpoint": endpoint}
        report["rows"].append(row)
        report["rows"].sort(key=lambda r: r["base"])
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
        print(f"base {base}: {hi-lo+1:.3e} candidates in {seconds:.1f}s; "
              f"differing bins: {len(mismatches)}; near misses (<=2 missing): {len(near)}", flush=True)


if __name__ == "__main__":
    main()
