#!/usr/bin/env python3
"""Exact nice-number verification and candidate bounds; standard library only.

Usage: python3 scripts/verify.py 69 10
       python3 scripts/verify.py --bounds 150
"""
import argparse
import json
from collections import Counter


def digits(n, base):
    if n < 0 or base < 2:
        raise ValueError("n must be nonnegative and base >= 2")
    if n == 0:
        return [0]
    out = []
    while n:
        n, digit = divmod(n, base)
        out.append(digit)
    return out[::-1]


def floor_root(n, exponent):
    """Integer root using exact arithmetic, including perfect powers."""
    if n < 0 or exponent < 1:
        raise ValueError("invalid root")
    if n < 2 or exponent == 1:
        return n
    lo, hi = 0, 1 << ((n.bit_length() + exponent - 1) // exponent)
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if mid ** exponent <= n:
            lo = mid
        else:
            hi = mid
    return hi if hi ** exponent <= n else lo


def ceil_root(n, exponent):
    r = floor_root(n, exponent)
    return r + (r ** exponent != n)


def candidate_intervals(base):
    """List [lo, hi] inclusive with length(n²)+length(n³)=base.

    Enumerate square length s and cube length c=base-s, intersecting
    b^(s-1)<=n²<b^s and b^(c-1)<=n³<b^c. No floating-point bounds.
    """
    if base < 2:
        raise ValueError("base must be >= 2")
    out = []
    for s in range(1, base):
        c = base - s
        if c < s or 3 * s < 2 * c - 2 or 3 * s > 2 * c + 3:
            continue
        lo = max(ceil_root(base ** (s - 1), 2),
                 ceil_root(base ** (c - 1), 3), 1)
        hi = min(floor_root(base ** s - 1, 2),
                 floor_root(base ** c - 1, 3))
        if lo <= hi:
            out.append({"lo": lo, "hi": hi, "square_digits": s,
                        "cube_digits": c, "count": hi - lo + 1})
    return out


def verify(n, base):
    if n <= 0 or base < 2:
        raise ValueError("n must be a positive integer and base >= 2")
    square, cube = digits(n*n, base), digits(n*n*n, base)
    counts = Counter(square + cube)
    missing = [d for d in range(base) if not counts[d]]
    repeated = {d: count for d, count in sorted(counts.items()) if count > 1}
    return {
        "n": str(n), "base": base,
        "square": str(n*n), "cube": str(n*n*n),
        "square_digits": square, "cube_digits": cube,
        "digit_count": len(square)+len(cube),
        "distinct_digits": len(counts), "missing_digits": missing,
        "repeated_digits": repeated,
        "nice": len(square)+len(cube) == base and not missing and not repeated,
        "digit_sum_congruence": (n*n+n*n*n-base*(base-1)//2) % (base-1) == 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("n", type=int, nargs="?")
    parser.add_argument("base", type=int, nargs="?")
    parser.add_argument("--bounds", type=int)
    args = parser.parse_args()
    if args.bounds is not None:
        result = {"base": args.bounds, "intervals": candidate_intervals(args.bounds)}
    elif args.n is not None and args.base is not None:
        result = verify(args.n, args.base)
    else:
        parser.error("provide n and base, or --bounds base")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
