#!/usr/bin/env python3
"""Searchable analogues: n^2 and n^3 jointly use every digit exactly k times.

Same exponents (2, 3), same carries, same congruence structure as nice
numbers (k = 1), but the total length is k*b, which moves the predicted onset
of solutions down to bases where exhaustive search is cheap (about 15 for
k = 2, about 10 for k = 3). This tests the conditional random-digit model at
exact hits (not near misses), for the algebra that actually matters.

Model: condition on the exact last digits (x, y) of n^2, n^3 and on the digit
sum class; the other k*b-2 digits are uniform among legal strings (both
leading digits nonzero) with that class. Same construction as the nice-number
model in research/existence-counting.md.

Usage: python3 critique/scripts/twice_nice.py --max-base 22 --threads 10
       python3 critique/scripts/twice_nice.py --mult 3 --max-base 15 \
           --output critique/results/thrice-nice.json
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import ceil_root, floor_root, digits  # noqa: E402

SCRATCH = Path(os.environ.get("NICE_SCRATCH", "/private/tmp/nice-critique"))


def intervals_total_length(base, total):
    out = []
    for s in range(1, total):
        c = total - s
        if c < s or 3 * s < 2 * c - 2 or 3 * s > 2 * c + 3:
            continue
        lo = max(ceil_root(base ** (s - 1), 2), ceil_root(base ** (c - 1), 3), 1)
        hi = min(floor_root(base ** s - 1, 2), floor_root(base ** c - 1, 3))
        if lo <= hi:
            out.append((lo, hi, s, c))
    return out


def is_k_nice(n, b, k):
    cnt = Counter(digits(n * n, b) + digits(n ** 3, b))
    return len(cnt) == b and all(v == k for v in cnt.values())


def model_expectation(b, lo, hi, k=2):
    """Exact-rational expectation in the conditional model (as a float)."""
    m = b - 1
    target = (k * b * (b - 1) // 2) % m  # k times the full digit sum
    roots = [s for s in range(m) if (s * s * (s + 1) - target) % m == 0]
    modulus = b * m
    rest = k * b - 2
    legal_same_class = (b - 1) * b ** (rest - 2)
    fact = math.factorial(rest)
    total = Fraction(0)
    for r in range(b):
        x, y = r * r % b, r ** 3 % b
        left = [k] * b
        left[x] -= 1
        left[y] -= 1
        if min(left) < 0:
            continue
        denom_mult = 1
        for v in left:
            denom_mult *= math.factorial(v)
        zeros = left[0]
        arrangements = Fraction(fact, denom_mult)
        # both leading positions avoid the remaining zeros:
        # C(rest-2, zeros) / C(rest, zeros)
        lead_ok = Fraction(math.comb(rest - 2, zeros), math.comb(rest, zeros))
        p = arrangements * lead_ok / legal_same_class
        for s in roots:
            res = (r + b * ((s - r) % m)) % modulus
            first = lo + (res - lo) % modulus
            count = (hi - first) // modulus + 1 if first <= hi else 0
            total += count * p
    return float(total), len(roots)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mult", type=int, default=2, help="required multiplicity k")
    ap.add_argument("--min-base", type=int, default=5)
    ap.add_argument("--max-base", type=int, default=22)
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--model-only-max-base", type=int, default=40)
    ap.add_argument("--output", default=str(ROOT / "critique/results/twice-nice.json"))
    args = ap.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    binary = SCRATCH / "histogram"
    subprocess.run(["clang", "-O3", "-march=native", "-o", str(binary),
                    str(ROOT / "critique/scripts/histogram.c"), "-lpthread"], check=True)
    try:
        report = json.loads(Path(args.output).read_text())
    except FileNotFoundError:
        report = {"scope": f"Analogue: every digit exactly {args.mult} times across n^2 and n^3",
                  "mult": args.mult, "rows": []}
    done = {r["base"] for r in report["rows"] if r.get("searched")}
    for b in range(args.min_base, args.model_only_max_base + 1):
        if b in done:
            continue
        ivs = intervals_total_length(b, args.mult * b)
        if not ivs:
            continue
        (lo, hi, s, c), = ivs
        expected, classes = model_expectation(b, lo, hi, args.mult)
        row = {"base": b, "lo": str(lo), "hi": str(hi), "square_digits": s, "cube_digits": c,
               "count": hi - lo + 1, "digit_sum_classes": classes, "model_expected": expected,
               "searched": False}
        fits = float(hi) ** 3 < 3.4e38
        if b <= args.max_base and fits:
            started = time.monotonic()
            out = subprocess.run([str(binary), str(b), str(lo), str(hi), str(s), str(c),
                                  str(args.threads), "0", str(args.mult)],
                                 check=True, capture_output=True, text=True).stdout
            res = json.loads(out)
            assert not res["overflow"]
            hits = [int(h) for h in res["hits"]]
            assert len(hits) == res["exact_hits"]
            for n in hits:
                assert is_k_nice(n, b, args.mult), (b, n)
            row.update({"searched": True, "seconds": time.monotonic() - started,
                        "observed": res["exact_hits"], "solutions": [str(h) for h in hits]})
            if hi - lo < 3_000_000:  # independent brute-force cross-check
                brute = [n for n in range(lo, hi + 1) if is_k_nice(n, b, args.mult)]
                row["python_bruteforce_agrees"] = brute == sorted(hits)
                assert row["python_bruteforce_agrees"], (b, brute, hits)
        report["rows"] = [r for r in report["rows"] if r["base"] != b] + [row]
        report["rows"].sort(key=lambda r: r["base"])
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
        print(json.dumps({k: row.get(k) for k in ("base", "count", "model_expected", "searched",
                                                   "observed", "solutions", "seconds")}), flush=True)
    searched = [r for r in report["rows"] if r.get("searched")]
    obs = sum(r["observed"] for r in searched)
    exp = sum(r["model_expected"] for r in searched)
    report["totals_searched"] = {"observed": obs, "expected": exp,
                                 "poisson_p_at_most_observed": poisson_cdf(obs, exp),
                                 "poisson_p_at_least_observed": 1 - poisson_cdf(obs - 1, exp) if obs else 1.0}
    Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
    print(report["totals_searched"])


def poisson_cdf(k, lam):
    """P(X <= k) for X ~ Poisson(lam), summed in log space (no overflow)."""
    if k < 0:
        return 0.0
    return min(1.0, sum(math.exp(i * math.log(lam) - lam - math.lgamma(i + 1)) for i in range(k + 1)))


if __name__ == "__main__":
    main()
