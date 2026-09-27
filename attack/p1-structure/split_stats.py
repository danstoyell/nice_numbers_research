#!/usr/bin/env python3
"""Where does a structured family's deficiency come from?

deficiency = rep_sq + rep_cu + cross, where rep_sq / rep_cu are repeated
digits inside the square / cube and cross = |set(sq) & set(cu)|.
Family A members n = (a*b^m + r)/d are grouped by the size of d:
  sq-inj : d^2 <= b      (square digits are an injective image of remainders)
  near   : b < d^2 <= 4b
  cu-inj : d^3 <= b      (subset of sq-inj; cube injective too)
  large  : d^2 > 4b
Random candidates give the baseline. Special bases b-1 = t^3 or b+1 = t^3
also get the class d = t^2 (cube expansions are digit rotations mod b-/+1).

usage: split_stats.py BASE [BASE ...]
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify import candidate_intervals  # noqa: E402
from family_scan import digits_le, family_A  # noqa: E402


def split(n, b):
    sq, cu = digits_le(n * n, b), digits_le(n ** 3, b)
    if len(sq) + len(cu) != b:
        return None
    S, C = set(sq), set(cu)
    return (len(sq) - len(S), len(cu) - len(C), len(S & C))


def summarize(rows):
    rows = [r for r in rows if r]
    if not rows:
        return "-"
    k = len(rows)
    m = [sum(r[i] for r in rows) / k for i in range(3)]
    tot = [sum(r) for r in rows]
    return (f"n={k:>5} rep_sq={m[0]:5.1f} rep_cu={m[1]:5.1f} cross={m[2]:5.1f} "
            f"def={sum(tot)/k:5.1f} min={min(tot)}")


def main():
    for a in sys.argv[1:]:
        b = int(a)
        rng = random.Random(b)
        iv = candidate_intervals(b)[0]
        lo, hi = iv["lo"], iv["hi"]
        m = len(digits_le(hi, b)) - 1
        groups = {"sq-inj": [], "cu-inj": [], "near": [], "large": [],
                  "special t^2": []}
        tcube = None
        for t in range(2, 20):
            if t ** 3 in (b - 1, b + 1):
                tcube = t
        for d in range(2, 3 * int(math.isqrt(b)) + 2):
            if math.gcd(d, b) != 1:
                continue
            ns = list(family_A(b, lo, hi, m, [d], 40 * d))
            if len(ns) > 600:
                ns = rng.sample(ns, 600)
            rows = [split(n, b) for n in ns]
            if d ** 3 <= b:
                groups["cu-inj"] += rows
            if d * d <= b:
                groups["sq-inj"] += rows
            elif d * d <= 4 * b:
                groups["near"] += rows
            else:
                groups["large"] += rows
        if tcube:
            d = tcube * tcube
            ns = list(family_A(b, lo, hi, m, [d], 200 * d))[:3000]
            groups["special t^2"] = [split(n, b) for n in ns]
        rand = [split(rng.randrange(lo, hi + 1), b) for _ in range(3000)]
        print(f"b={b} (square {iv['square_digits']}, cube {iv['cube_digits']} digits)")
        for g, rows in groups.items():
            print(f"  {g:>11}: {summarize(rows)}")
        print(f"  {'random':>11}: {summarize(rand)}", flush=True)


if __name__ == "__main__":
    main()
