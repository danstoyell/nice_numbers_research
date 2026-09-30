#!/usr/bin/env python3
"""Re-verify every reported (1,2)-nice hit with exact Python integer arithmetic,
independently of the C code: n and n^2 written in base b must together be a permutation
of 0..b-1 (so len(n) + len(n^2) = b and no leading zeros by construction).
Also checks that each base's reported hit count equals the number of distinct witnesses.

Usage: python3 verify_hits.py results/hits_by_base.json
"""
import json
import sys

from brute import digits


def is_12_nice(n, b):
    ds = digits(n, b) + digits(n * n, b)
    return len(ds) == b and sorted(ds) == list(range(b))


def main():
    data = json.load(open(sys.argv[1]))
    total = 0
    bad = []
    for key, row in data.items():
        b = int(key)
        w = row["witnesses"]
        assert len(set(w)) == len(w) == row["hits"], (b, len(w), row["hits"])
        for n in w:
            if not is_12_nice(n, b):
                bad.append((b, n))
        total += len(w)
        print(f"base {b}: {len(w)} witnesses, all verified" if not any(x[0] == b for x in bad)
              else f"base {b}: FAILURES {[x for x in bad if x[0] == b]}")
    print(f"total {total} witnesses re-verified, {len(bad)} failures")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
