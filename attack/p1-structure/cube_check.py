#!/usr/bin/env python3
"""Given a (near-)distinct square, is the cube still random?

Samples family A (d <= 200) and C (d | b^j +- 1, j <= 3) members, keeps
those with rep_sq <= 1, and compares their mean rep_cu and cross with the
random-digit model for c uniform digits against s fixed distinct digits.
usage: cube_check.py B...
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify import candidate_intervals  # noqa: E402
from family_scan import digits_le, divisors, sample_family  # noqa: E402
from split_stats import split  # noqa: E402

for arg in sys.argv[1:]:
    b = int(arg)
    rng = random.Random(b + 1)
    iv = candidate_intervals(b)[0]
    lo, hi = iv["lo"], iv["hi"]
    m = len(digits_le(hi, b)) - 1
    s, c = iv["square_digits"], iv["cube_digits"]
    q = 1 - (1 - 1 / b) ** c
    rot = set()
    for j in (1, 2, 3):
        for x in (b ** j - 1, b ** j + 1):
            rot.update(divisors(x, b ** 3))
    for fam, dl, R in (("A", range(2, 201), 600), ("C", sorted(rot), 50)):
        ns = sample_family(b, lo, hi, m, dl, R, 1, 6000, rng)
        rows = [x for x in (split(n, b) for n in ns) if x and x[0] <= 1]
        if not rows:
            continue
        k = len(rows)
        rc = sum(x[1] for x in rows) / k
        cr = sum(x[2] for x in rows) / k
        print(f"b={b} fam {fam}: {k}/{len(ns)} members with rep_sq<=1; "
              f"rep_cu={rc:.1f} (model {c - b * q:.1f}), cross={cr:.1f} "
              f"(model {s * q:.1f}), min rep_cu={min(x[1] for x in rows)}")
