#!/usr/bin/env python3
"""D7 audit of directions/quasi_nice.c: for bases 6..15, enumerate every n >= 1 whose base-b
digit counts satisfy len(n) + len(n^2) = b (no band formula, no digit-sum filter), check
the set is exactly quasi_nice's [lo, hi] band, and find all (1,2)-nice n by brute force.
Compares with a fresh run of quasi_nice (bin/quasi_nice) and with results/quasi_nice_6_22.jsonl."""
import json, subprocess
from pathlib import Path
here = Path(__file__).resolve().parent
def digs(x, b):
    out = []
    while x: out.append(x % b); x //= b
    return out
fresh = {json.loads(l)["b"]: json.loads(l) for l in subprocess.run([str(here / "bin/quasi_nice"), "6", "15"], capture_output=True, text=True, check=True).stdout.splitlines()}
stored = {json.loads(l)["b"]: json.loads(l) for l in open(here.parent / "directions/results/quasi_nice_6_22.jsonl")}
allok = True
for b in range(6, 16):
    band, hits = [], []
    n = 1
    while True:
        dn = digs(n, b)
        if len(dn) > b // 3 + 1: break
        d2 = digs(n * n, b)
        if len(dn) + len(d2) == b:
            band.append(n)
            if len(set(dn + d2)) == b: hits.append(n)
        n += 1
    contiguous = band == list(range(band[0], band[-1] + 1)) if band else True
    r = fresh[b]
    if band:
        ok = contiguous and r.get("lo") == band[0] and r.get("hi") == band[-1] and r["hits"] == len(hits) and r["witnesses"] == hits[:64]
    else:
        ok = r.get("band", 0) is None and not hits
    same_as_stored = fresh[b] == stored[b]
    allok &= ok and same_as_stored
    print(f"b={b}: band {'[%d,%d]' % (band[0], band[-1]) if band else 'none'} contiguous={contiguous} hits={hits} | quasi_nice agrees: {ok} | stored jsonl identical: {same_as_stored}")
print("ALL OK" if allok else "DISCREPANCY")
