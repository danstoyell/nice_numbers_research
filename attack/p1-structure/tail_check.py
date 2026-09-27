#!/usr/bin/env python3
"""Which family members populate the low-deficiency tail?

Resamples families A/B/C exactly as family_scan.py does and prints, for
every member whose deficiency is at or below the random sample's minimum,
its denominator class and (rep_sq, rep_cu, cross). usage: tail_check.py B...
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify import candidate_intervals  # noqa: E402
from family_scan import digits_le, divisors, deficiency  # noqa: E402
from split_stats import split  # noqa: E402
from sweet_spot import sweet  # noqa: E402

for arg in sys.argv[1:]:
    b = int(arg)
    rng = random.Random(b)
    iv = candidate_intervals(b)[0]
    lo, hi = iv["lo"], iv["hi"]
    m = len(digits_le(hi, b)) - 1
    B = b ** m
    rmin = min(x for x in (deficiency(rng.randrange(lo, hi + 1), b)
                           for _ in range(3000)) if x is not None)
    sw = set(sweet(b))
    rot = set()
    for j in (1, 2, 3):
        for x in (b ** j - 1, b ** j + 1):
            rot.update(divisors(x, b ** 3))
    classes = {}
    for fam, dl, R, blocks in (("A", list(range(2, 201)), 600, 1),
                               ("B", list(range(2, 13)), 6, 2),
                               ("C", sorted(rot), 50, 1)):
        dl = [d for d in dl if d >= 2 and math.gcd(d, b) == 1]
        got = 0
        while got < 3000:
            d = rng.choice(dl)
            a = rng.randrange(max(1, lo * d // B), hi * d // B + 2)
            if math.gcd(a, d) != 1:
                continue
            N0 = a * B
            if blocks == 2:
                N0 += (rng.randrange(-(d - 1), d) or 1) * b ** rng.randrange(1, m)
            r = rng.randrange(-R, R + 1)
            r -= (N0 + r) % d
            n = (N0 + r) // d
            if not lo <= n <= hi:
                continue
            got += 1
            s = split(n, b)
            if s and sum(s) <= rmin:
                cls = "sweet" if d in sw else ("d^2<=b" if d * d <= b else "other")
                classes.setdefault((fam, cls), []).append((d,) + s)
    print(f"b={b} random min deficiency={rmin}")
    for k, v in sorted(classes.items()):
        print(f"  {k}: {len(v)} members; rep_sq values {sorted(x[1] for x in v)[:12]}"
              f" d values {sorted(set(x[0] for x in v))[:10]}")
