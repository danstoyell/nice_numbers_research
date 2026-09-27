#!/usr/bin/env python3
"""How much does the digit-sum identity shift near-pandigital rates?

For every n, digitsum(n^2) + digitsum(n^3) = n^2 + n^3 (mod b-1). The
random-digit models in tail_validation.py ignore this coupling between a
string's digit multiset and n mod (b-1). A deficiency-r multiset is the full
alphabet plus r extra copies minus r missing values, so its digit sum is
T + sum(extras) - sum(missing), with T = b(b-1)/2. Weighting each multiset by
its number of arrangements, the coupled rate relative to the uncoupled one is

    sum_delta rho(delta) * w_r(delta) / (sum_delta w_r(delta) / (b-1)),

where rho is the distribution of n^2(n+1) - T mod (b-1) over n (the interval
is long, so n mod (b-1) is uniform) and w_r(delta) is the arrangement weight
of deficiency-r multisets with excess sum = delta mod (b-1).

Usage: python3 critique/scripts/digit_sum_coupling.py
"""
import json
from itertools import combinations
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def coupling_ratio(b, r):
    m = b - 1
    target = b * (b - 1) // 2
    rho = [0] * m
    for n in range(m):
        rho[(n * n * (n + 1) - target) % m] += 1
    rho = [x / m for x in rho]
    w = [0.0] * m
    vals = range(b)
    if r == 1:
        for d in vals:
            for miss in vals:
                if d != miss:
                    w[(d - miss) % m] += factorial(b) / 2
    elif r == 2:
        for d in vals:  # one value three times, two missing
            for m1, m2 in combinations([v for v in vals if v != d], 2):
                w[(2 * d - m1 - m2) % m] += factorial(b) / 6
        for d1, d2 in combinations(vals, 2):  # two values twice, two missing
            rest = [v for v in vals if v not in (d1, d2)]
            for m1, m2 in combinations(rest, 2):
                w[(d1 + d2 - m1 - m2) % m] += factorial(b) / 4
    else:
        raise ValueError("r must be 1 or 2")
    total = sum(w)
    return sum(rho[i] * w[i] for i in range(m)) / (total / m)


def main():
    rows = []
    for b in range(20, 49):
        rows.append({"base": b, "deficiency_1_ratio": coupling_ratio(b, 1),
                     "deficiency_2_ratio": coupling_ratio(b, 2)})
        print(b, round(rows[-1]["deficiency_1_ratio"], 4), round(rows[-1]["deficiency_2_ratio"], 4))
    out = ROOT / "critique/results/digit-sum-coupling.json"
    out.write_text(json.dumps({
        "scope": "Exact effect of the digit-sum identity on deficiency-1 and -2 rates, relative to uncoupled random strings",
        "rows": rows,
        "summary": {"deficiency_1_min": min(r["deficiency_1_ratio"] for r in rows),
                    "deficiency_1_max": max(r["deficiency_1_ratio"] for r in rows),
                    "deficiency_2_min": min(r["deficiency_2_ratio"] for r in rows),
                    "deficiency_2_max": max(r["deficiency_2_ratio"] for r in rows)}}, indent=1) + "\n")


if __name__ == "__main__":
    main()
