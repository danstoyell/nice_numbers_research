#!/usr/bin/env python3
"""Where do the repeated digits of deficiency-2 near misses sit?

Uses the near-miss lists from recompute_histograms.py (bases 20-35, every
candidate with exactly two missing digits). For each value that appears
twice, record whether both copies are in n^2, both in n^3, or split. If
middle digits were exchangeable across positions, the expected shares are
C(s,2), C(c,2), and s*c over C(b,2). A correlation between the square's and
the cube's digit sets would show up as a distorted split share. Also counts
how often 0 or b-1 is among the missing digits (naive rate 2/b each).

Usage: python3 critique/scripts/near_miss_placement.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals, digits  # noqa: E402


def main():
    rec = json.loads((ROOT / "critique/results/histogram-recompute.json").read_text())
    observed = {"square": 0, "cube": 0, "split": 0}
    expected = {"square": 0.0, "cube": 0.0, "split": 0.0}
    events = zero_missing = top_missing = 0
    naive_zero = naive_top = 0.0
    for row in rec["rows"]:
        b = row["base"]
        if b < 20:
            continue
        iv, = candidate_intervals(b)
        s, c = iv["square_digits"], iv["cube_digits"]
        pairs = math.comb(b, 2)
        for nm in row["near_misses_at_most_two_missing"]:
            if nm["distinct"] != b - 2:
                continue
            n = int(nm["n"])
            sq, cu = digits(n * n, b), digits(n ** 3, b)
            events += 1
            for d, count in nm["repeated"].items():
                if count != 2:
                    continue
                d = int(d)
                where = "square" if sq.count(d) == 2 else "cube" if cu.count(d) == 2 else "split"
                observed[where] += 1
                expected["square"] += math.comb(s, 2) / pairs
                expected["cube"] += math.comb(c, 2) / pairs
                expected["split"] += s * c / pairs
            zero_missing += 0 in nm["missing"]
            top_missing += (b - 1) in nm["missing"]
            naive_zero += 2 / b
            naive_top += 2 / b
    out = {"scope": "Deficiency-2 near misses in bases 20-35 (exhaustive lists)",
           "events": events, "duplicate_placement_observed": observed,
           "duplicate_placement_exchangeable_expectation": expected,
           "zero_missing": {"observed": zero_missing, "naive_expected": naive_zero},
           "top_digit_missing": {"observed": top_missing, "naive_expected": naive_top}}
    (ROOT / "critique/results/near-miss-placement.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
