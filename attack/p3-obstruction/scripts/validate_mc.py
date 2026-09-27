#!/usr/bin/env python3
"""Validate model_mc.py: (1) closed-form valid-middle counts equal the
critique's exact occupancy formula; (2) at small bases, the exact conditional
sampler matches brute-force rejection sampling from the unconditioned model
on the statistics used later (triple share, duplicate placement, edge
involvement, zero missing).

Usage: python3 attack/p3-obstruction/scripts/validate_mc.py
"""
import random
import sys

sys.dont_write_bytecode = True  # never write caches into critique/ or scripts/
from collections import Counter
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "critique/scripts"))
import model_mc as M  # noqa: E402
from common import shape  # noqa: E402
from tail_validation import middle_new_values  # noqa: E402
from verify import candidate_intervals  # noqa: E402


def stats(sq, cu, b, s, c):
    allv = list(sq) + list(cu)
    cnt = Counter(allv)
    reps = [d for d, k in cnt.items() if k > 1]
    triple = any(k == 3 for k in cnt.values())
    place = []
    edge = 0
    for d in reps:
        ps = [i for i, x in enumerate(sq) if x == d]
        pc = [i for i, x in enumerate(cu) if x == d]
        place.append("sq" if not pc else "cu" if not ps else "split")
        edge += sum(1 for i in ps if i < 2 or i >= s - 3) + sum(1 for i in pc if i < 2 or i >= c - 3)
    return {"triple": triple, "place": tuple(sorted(place)), "edge_copies": edge,
            "zero_missing": 0 not in cnt}


def main():
    for b in (20, 30, 45):
        m = b - 10
        for u in range(6, 11):
            for r in (1, 2, 3):
                v = b - r - u
                row = middle_new_values(b, m, u)
                exact = row[v] if 0 <= v < len(row) else 0
                mine = Fraction(M.valid_middles(b, m, u, r)[0], b ** m)
                assert exact == mine, (b, u, r)
    print("closed-form weights agree with tail_validation.middle_new_values")
    rng = random.Random(7)
    for b in (13, 15):
        s, c = shape(b)
        iv, = candidate_intervals(b)
        ivs = [(iv["lo"], iv["hi"], iv["hi"] - iv["lo"] + 1)]
        M.intervals = lambda bb, ivs=ivs: ivs  # noqa: E731
        cond = M.sample_base(b, 2, 20000, rng)
        # brute force: n uniform, middle uniform, keep deficiency 2 and congruence
        brute = []
        tries = 0
        while len(brute) < 4000:
            tries += 1
            n = rng.randint(iv["lo"], iv["hi"])
            t2, b2, t3, b3 = M.edge_digits(n, b, s, c)
            mid = [rng.randrange(b) for _ in range(b - 10)]
            sq = t2 + mid[:s - 5] + b2
            cu = t3 + mid[s - 5:] + b3
            if len(set(sq + cu)) != b - 2 or (sum(sq) + sum(cu) - n * n - n ** 3) % (b - 1):
                continue
            brute.append((n, sq, cu))
        A = [stats(x[1], x[2], b, s, c) for x in cond["samples"]]
        B = [stats(x[1], x[2], b, s, c) for x in brute]
        for key in ("triple", "place", "edge_copies", "zero_missing"):
            ca, cb = Counter(a[key] for a in A), Counter(x[key] for x in B)
            keys = sorted(set(ca) | set(cb), key=str)
            print(f"base {b} {key} (conditional/brute): " + ", ".join(f"{k}: {ca[k]/len(A):.3f}/{cb[k]/len(B):.3f}" for k in keys), flush=True)
        print(f"base {b}: brute-force def-2+congruence rate {len(brute)/tries:.4e}")


if __name__ == "__main__":
    main()
