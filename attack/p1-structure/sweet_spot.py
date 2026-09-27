#!/usr/bin/env python3
"""The one rational class where the square can be distinct for free.

Sweet spot: d^2 in [0.4b, b], gcd(d, b) = 1, ord_{d^2}(b) >= 0.4b. Then the
square's structured digits floor(b*rho/d^2) are an injective image of
distinct remainders, so rep_sq can be 0. The cube (denominator d^3 > b) is
not injective. This measures, for family A members n = (a*b^m + r)/d with
sweet d: P(rep_sq = 0), and the cube's rep_cu / cross against the
random-digit prediction given a distinct square. Then it bounds the family's
expected nice count: E <= F * P(rep_sq=0) * (0.6b)!/b^(0.6b)-type factor,
computed exactly as c!/b^c with c = cube length (the cube must fill the
complement of the square's digit set).

usage: sweet_spot.py BMIN BMAX [measure bases...]
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify import candidate_intervals  # noqa: E402
from family_scan import digits_le, family_A  # noqa: E402
from split_stats import split  # noqa: E402


def order(b, q):
    x, k = b % q, 1
    while x != 1:
        x = x * b % q
        k += 1
    return k


def sweet(b):
    out = []
    for d in range(2, math.isqrt(b) + 1):
        q = d * d
        if 5 * q < 2 * b or math.gcd(d, b) != 1:
            continue
        if 5 * order(b, q) >= 2 * b:
            out.append(d)
    return out


def main():
    bmin, bmax = int(sys.argv[1]), int(sys.argv[2])
    measure = [int(x) for x in sys.argv[3:]]
    have, total, worst = 0, 0, -1e9
    for b in range(bmin, bmax + 1):
        if b % 5 == 1 or b % 4 == 3 or not candidate_intervals(b):
            continue
        total += 1
        ds = sweet(b)
        if not ds:
            continue
        have += 1
        iv = candidate_intervals(b)[0]
        m = len(digits_le(iv["hi"], b)) - 1
        # generous family size: every a, every |r| <= b^2 (len r^2 <= 4)
        F = sum(len(range(max(1, iv["lo"] * d // b ** m),
                          iv["hi"] * d // b ** m + 2)) * (2 * b * b // d + 1)
                for d in ds)
        c = iv["cube_digits"]
        log10E = (math.log(F) + math.lgamma(c + 1) - c * math.log(b)) / math.log(10)
        worst = max(worst, log10E)
    print(f"bases {bmin}-{bmax}: {total} admissible, {have} have a sweet d; "
          f"max over them of log10(F * c!/b^c) = {worst:.1f} "
          f"(upper bound on E even if every square were distinct)")
    for b in measure:
        ds = sweet(b)
        if not ds:
            print(f"b={b}: no sweet d")
            continue
        iv = candidate_intervals(b)[0]
        lo, hi = iv["lo"], iv["hi"]
        m = len(digits_le(hi, b)) - 1
        rng = random.Random(b)
        rows = []
        for d in ds:
            ns = list(family_A(b, lo, hi, m, [d], 30 * d * d))
            rows += [split(n, b) for n in rng.sample(ns, min(len(ns), 3000))]
        rows = [r for r in rows if r]
        s, c = iv["square_digits"], iv["cube_digits"]
        z = [r for r in rows if r[0] == 0]
        # random-digit prediction for the cube given s distinct square digits
        p_rep_cu = c - b * (1 - (1 - 1 / b) ** c)
        p_cross = s * (1 - (1 - 1 / b) ** c)
        rnd = [split(rng.randrange(lo, hi + 1), b) for _ in range(3000)]
        rnd = [r for r in rnd if r]
        mean = lambda xs, i: sum(x[i] for x in xs) / len(xs)  # noqa: E731
        print(f"b={b} sweet d={ds}: members={len(rows)} P(rep_sq=0)={len(z)/len(rows):.3f}; "
              f"given rep_sq=0: rep_cu={mean(z,1):.1f} (model {p_rep_cu:.1f}) "
              f"cross={mean(z,2):.1f} (model {p_cross:.1f}) def={sum(sum(x) for x in z)/len(z):.1f}, "
              f"min def={min(sum(x) for x in z)}; random def={sum(sum(x) for x in rnd)/len(rnd):.1f} "
              f"min {min(sum(x) for x in rnd)}" if z else f"b={b}: no member with rep_sq=0", flush=True)


if __name__ == "__main__":
    main()
