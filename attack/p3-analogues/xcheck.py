#!/usr/bin/env python3
"""Cross-checks of a production run in its own configuration.

1. Sub-interval, different J: rerun [LO, LO + frac*(HI-LO)] with another low-digit
   depth J' (different residue classes, chunking and lane packing) and compare
   hits with the production log restricted to that sub-interval.
2. Filters off: rerun the first N chunks of the production residue order with
   the digit-sum and low-digit filters disabled (every residue walked) and
   compare hits chunk by chunk.

Usage: python3 xcheck.py --k 3 --base 18 --j 5 --alt-j 4 --frac 0.1 --nochunks 20
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run import binary_for, interval, is_k_nice, parse_log, perm_a  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--base", type=int, required=True)
    ap.add_argument("--j", type=int, required=True, help="J of the production run")
    ap.add_argument("--chunks", type=int, default=2000)
    ap.add_argument("--alt-j", type=int, required=True)
    ap.add_argument("--frac", type=float, default=0.1)
    ap.add_argument("--nochunks", type=int, default=20)
    ap.add_argument("--threads", type=int, default=5)
    args = ap.parse_args()
    k, b = args.k, args.base
    lo, hi, s, c = interval(b, k)
    _, prod = parse_log(HERE / "logs" / f"k{k}_b{b}_j{args.j}_c{args.chunks}.log")
    assert len(prod) == args.chunks, "production run incomplete"
    prod_hits = sorted({h for r in prod.values() for h in r["hits"]})
    out = {"k": k, "base": b, "production_J": args.j}

    # 1. sub-interval with another J
    sub_hi = lo + int((hi - lo) * args.frac)
    exe = binary_for(b, k, s, c, args.alt_j)
    log = HERE / "logs" / f"xcheck_k{k}_b{b}_altj{args.alt_j}_frac{args.frac}.log"
    log.unlink(missing_ok=True)
    m = b ** args.alt_j
    nch = min(m, 500)
    subprocess.run([str(exe), str(lo), str(sub_hi), str(args.threads), str(nch), str(perm_a(b, args.alt_j)),
                    str(log), "1"], check=True)
    _, alt = parse_log(log)
    assert len(alt) == nch
    alt_hits = sorted({h for r in alt.values() for h in r["hits"]})
    want = [h for h in prod_hits if lo <= h <= sub_hi]
    for h in alt_hits:
        assert is_k_nice(h, b, k)
    out["subinterval"] = {"lo": str(lo), "hi": str(sub_hi), "alt_J": args.alt_j,
                          "production_hits_in_range": len(want), "alt_hits": len(alt_hits),
                          "identical": alt_hits == want}
    print(json.dumps(out["subinterval"]), flush=True)

    # 2. filters off on the first chunks of the production order
    exe = binary_for(b, k, s, c, args.j)
    log = HERE / "logs" / f"xcheck_k{k}_b{b}_j{args.j}_nofilter_first{args.nochunks}.log"
    log.unlink(missing_ok=True)
    subprocess.run([str(exe), str(lo), str(hi), str(args.threads), str(args.chunks), str(perm_a(b, args.j)),
                    str(log), "0", "0", str(args.nochunks)], check=True)
    _, nof = parse_log(log)
    same = all(sorted(nof[ci]["hits"]) == sorted(prod[ci]["hits"]) for ci in range(args.nochunks))
    out["filters_off"] = {"chunks": args.nochunks,
                          "hits_filtered": sum(prod[ci]["nhits"] for ci in range(args.nochunks)),
                          "hits_unfiltered": sum(nof[ci]["nhits"] for ci in range(args.nochunks)),
                          "lane_steps_unfiltered": sum(nof[ci]["steps"] for ci in range(args.nochunks)),
                          "identical": same}
    print(json.dumps(out["filters_off"]), flush=True)
    path = HERE / "results" / "xcheck.json"
    allx = json.loads(path.read_text()) if path.exists() else {}
    allx[f"k{k}_b{b}"] = out
    path.write_text(json.dumps(allx, indent=1) + "\n")


if __name__ == "__main__":
    main()
