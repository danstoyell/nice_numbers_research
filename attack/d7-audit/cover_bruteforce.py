#!/usr/bin/env python3
"""D7 audit: cover.c against brute force over all permutations (small b), including word
lengths 1 and 2 and moduli that are multiples of 64 (row-rotation edge case).
Usage: python3 cover_bruteforce.py   (expects bin/cover built from ../h3-covering/cover.c)"""
import itertools, json, math, subprocess, sys
from pathlib import Path
here = Path(__file__).resolve().parent
COVER = str(here / "bin/cover")
MODS = [2, 3, 5, 7, 11, 13, 17, 63, 64, 65, 127, 128, 129, 191, 192, 193, 256, 320]

def brute(b, s, Ms):
    c = b - s
    pairs = set()
    for p in itertools.permutations(range(b)):
        X = p[:s]; Y = p[s:]
        if X[-1] == 0 or Y[-1] == 0:       # leading digit = highest position
            continue
        x = sum(d * b ** i for i, d in enumerate(X)); y = sum(d * b ** i for i, d in enumerate(Y))
        pairs.add((x, y))
    out = {}
    T = b * (b - 1) // 2
    for M in Ms:
        img = {(x % M, y % M) for x, y in pairs}
        g = math.gcd(M, b - 1)
        out[M] = (len(img), sum(1 for (x, y) in img if (x + y - T) % g))
    return out

bad = 0; tested = 0
for b in range(4, 10):
    for s in range(1, b):
        ref = brute(b, s, MODS)
        res = subprocess.run([COVER, str(b), str(s), str(b - s)] + [str(M) for M in MODS], capture_output=True, text=True, check=True).stdout
        for line in res.splitlines():
            r = json.loads(line); M = r["M"]; tested += 1
            if (r["image"], r["outside_prediction"]) != ref[M]:
                bad += 1; print("MISMATCH", b, s, M, r["image"], ref[M])
    print(f"b={b} done", flush=True)
print(f"tested {tested} (b, s, M) cases, mismatches {bad}")
