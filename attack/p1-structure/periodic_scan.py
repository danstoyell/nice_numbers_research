#!/usr/bin/env python3
"""Periodic roots whose cube is a linear digit ramp (the one escape found
from the sqrt(b)-vs-cbrt(b) tension).

n = floor(c * b^L / M) + e, M = b^j - 1, so n's base-b digits repeat the
j-digit block c. In base B = b^j, n^2 = c^2 * (ramp) has local denominator
M^2 (a digit rotation, i.e. arithmetic-progression B-digits), while n^3 has
local denominator M^3 (quadratic ramp, collides like random) UNLESS
M | c^3, in which case the cube is also a rotation. Writing
M = prod p^e, M | c^3 iff g | c with g = prod p^ceil(e/3). The square's
B-digit period is then at most M^(1/3).

For each admissible base and j, enumerate every c = g*a whose n lies in
the candidate interval, offsets |e| <= E, and record deficiencies; also a
same-size control of arbitrary c (general periodic roots, same j).

usage: periodic_scan.py BMIN BMAX [--j 2,3] [--E 2] [--control]
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify import candidate_intervals, verify  # noqa: E402
from family_scan import digits_le  # noqa: E402


def factor(x):
    f, p = {}, 2
    while p * p <= x:
        while x % p == 0:
            f[p] = f.get(p, 0) + 1
            x //= p
        p += 1 if p == 2 else 2
    if x > 1:
        f[x] = f.get(x, 0) + 1
    return f


def cube_gate(M):
    g = 1
    for p, e in factor(M).items():
        g *= p ** (-(-e // 3))
    return g


def deficiency(n, b):
    sq, cu = digits_le(n * n, b), digits_le(n ** 3, b)
    if len(sq) + len(cu) != b:
        return None
    return b - len(set(sq) | set(cu))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bmin", type=int)
    ap.add_argument("bmax", type=int)
    ap.add_argument("--j", default="2,3")
    ap.add_argument("--E", type=int, default=2)
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    js = [int(x) for x in args.j.split(",")]
    rng = random.Random(7)
    rows, found = [], []
    for b in range(args.bmin, args.bmax + 1):
        if b % 5 == 1 or b % 4 == 3:
            continue
        ivs = candidate_intervals(b)
        if not ivs:
            continue
        lo, hi = ivs[0]["lo"], ivs[0]["hi"]
        L = len(digits_le(hi, b))
        bL = b ** L
        for j in js:
            M = b ** j - 1
            g = cube_gate(M)
            amin = max(1, (lo * M) // (bL * g) - 1)
            amax = (hi * M) // (bL * g) + 1
            defs = []
            for a in range(amin, amax + 1):
                c = a * g
                if c >= M:
                    break
                base_n = (c * bL) // M
                for e in range(-args.E, args.E + 1):
                    n = base_n + e
                    if not lo <= n <= hi:
                        continue
                    dfc = deficiency(n, b)
                    if dfc is None:
                        continue
                    defs.append(dfc)
                    if dfc == 0:
                        v = verify(n, b)
                        found.append((b, j, n, v["distinct_digits"]))
                        print("NICE?", b, j, n, v, flush=True)
            row = {"base": b, "j": j, "g": g, "M_over_g": M // g,
                   "members": len(defs),
                   "min_def": min(defs) if defs else None,
                   "mean_def": sum(defs) / len(defs) if defs else None}
            if args.control and defs:
                cdefs = []
                cmin = (lo * M) // bL + 1
                cmax = min(M - 1, (hi * M) // bL)
                for _ in range(min(len(defs), 400)):
                    n = (rng.randrange(cmin, cmax + 1) * bL) // M
                    dfc = deficiency(n, b)
                    if dfc is not None:
                        cdefs.append(dfc)
                if cdefs:
                    row["control_mean"] = sum(cdefs) / len(cdefs)
                    row["control_min"] = min(cdefs)
            rows.append(row)
            if defs:
                print(json.dumps(row), flush=True)
    out = args.out or str(Path(__file__).parent / "results" / (
        f"periodic_scan_{args.bmin}_{args.bmax}_j{args.j.replace(',', '')}.json"))
    Path(out).write_text(json.dumps({"rows": rows, "nice": found}, indent=1))
    tot = sum(r["members"] for r in rows)
    print(f"bases {args.bmin}-{args.bmax} j={js}: {tot} members tested, "
          f"{sum(1 for r in rows if r['members'])} (base,j) pairs nonempty, "
          f"nice found: {found}")


if __name__ == "__main__":
    main()
