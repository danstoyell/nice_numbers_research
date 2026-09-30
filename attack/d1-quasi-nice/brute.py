#!/usr/bin/env python3
"""Independent brute force for (1,2)-nice numbers: n and n^2 together use every
base-b digit exactly once. No filters: every n >= 1 whose digit counts add to b is
checked with exact integer arithmetic. Also records the band and the deficiency
histogram (b - #distinct digits) over the band.

Usage: python3 brute.py bmin bmax  -> prints one JSON line per base
"""
import json
import sys


def digits(x, b):
    out = []
    while x:
        x, d = divmod(x, b)
        out.append(d)
    return out


def band(b):
    """All n with len(n) + len(n^2) == b, found by scanning lengths with exact integer roots."""
    from math import isqrt
    res = []
    for s in range(1, b):
        c = b - s
        lo1, hi1 = b ** (s - 1), b ** s - 1
        lo2 = isqrt(b ** (c - 1) - 1) + 1  # smallest n with n^2 >= b^(c-1)
        hi2 = isqrt(b ** c - 1)             # largest n with n^2 < b^c
        lo, hi = max(lo1, lo2), min(hi1, hi2)
        if lo <= hi:
            res.append((s, c, lo, hi))
    return res


def main():
    bmin, bmax = int(sys.argv[1]), int(sys.argv[2])
    for b in range(bmin, bmax + 1):
        bands = band(b)
        if not bands:
            print(json.dumps({"b": b, "band": None}), flush=True)
            continue
        assert len(bands) == 1, bands
        s, c, lo, hi = bands[0]
        hits, hist = [], {}
        for n in range(lo, hi + 1):
            ds = digits(n, b) + digits(n * n, b)
            assert len(ds) == b
            k = len(set(ds))
            hist[b - k] = hist.get(b - k, 0) + 1
            if k == b:
                hits.append(n)
        print(json.dumps({"b": b, "s": s, "c": c, "lo": lo, "hi": hi, "N": hi - lo + 1,
                          "hits": len(hits), "witnesses": hits,
                          "deficiency_hist": {str(k): v for k, v in sorted(hist.items())}}), flush=True)


if __name__ == "__main__":
    main()
