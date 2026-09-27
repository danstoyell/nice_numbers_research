#!/usr/bin/env python3
"""Exact necessary-condition experiments for square--cube nice numbers.

No external dependencies. This checks congruence formulas and enumerates *local*
suffix residues; a surviving residue is not claimed to be a nice number.
"""

import argparse
import json
from math import isqrt
from pathlib import Path


def factor(n):
    out = []
    p = 2
    while p * p <= n:
        exponent = 0
        while n % p == 0:
            n //= p
            exponent += 1
        if exponent:
            out.append((p, exponent))
        p += 1
    if n > 1:
        out.append((n, 1))
    return out


def digit_sum_root_count(b):
    answer = 1
    for p, exponent in factor(b - 1):
        if p == 2:
            if exponent == 1:
                return 0
            answer *= 1 + (2 ** ((exponent - 1) // 2) if exponent % 2 else 0)
        else:
            answer *= 1 + p ** (exponent // 2)
    return answer


def last_digit_collision_count(b):
    answer = 1
    for p, exponent in factor(b):
        answer *= 1 + p ** (exponent // 2)
    return answer


def valid_suffix(n, b, depth):
    seen = 0
    for value in (n * n, n * n * n):
        for _ in range(depth):
            value, digit = divmod(value, b)
            mask = 1 << digit
            if seen & mask:
                return False
            seen |= mask
    return True


def suffix_count(b, depth):
    if b < 2 * depth:
        return {"base": b, "depth": depth, "survivors": 0, "first": None}
    first = None
    count = 0
    for n in range(b ** depth):
        if valid_suffix(n, b, depth):
            count += 1
            if first is None:
                first = n
    return {"base": b, "depth": depth, "survivors": count, "first": first}


def convolution(a, b):
    c = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            c[i + j] += ai * bj
    return c


def compact_constructive_coefficients(depth):
    """Greedily avoid equal coefficients up to the requested suffix depth.

    At each new index, only one new square and one new cube coefficient appear.
    Each is linear in the new coefficient, with slopes 2*a0 and 3*a0**2.
    Taking a0=2 makes those slopes different, so only finitely many values fail.
    """
    a = [2]
    while len(a) < depth:
        for next_coefficient in range(1, 100000):
            trial = a + [next_coefficient]
            square = convolution(trial, trial)
            cube = convolution(square, trial)
            digits = square[:len(trial)] + cube[:len(trial)]
            if len(digits) == len(set(digits)):
                a = trial
                break
        else:
            raise RuntimeError("Unexpectedly large greedy coefficient")
    square = convolution(a, a)[:depth]
    cube = convolution(convolution(a, a), a)[:depth]
    assert len(set(square + cube)) == 2 * depth
    return {"depth": depth, "coefficients_low_to_high": a,
            "square_suffix_low_to_high": square,
            "cube_suffix_low_to_high": cube,
            "valid_for_all_bases_above": max(square + cube)}


def ceil_root(n, degree):
    lo, hi = 0, 1 << ((n.bit_length() + degree - 1) // degree)
    while lo < hi:
        mid = (lo + hi) // 2
        if mid ** degree < n:
            lo = mid + 1
        else:
            hi = mid
    return lo


def length_interval(b):
    q, rem = divmod(b - 2, 5)
    if rem == 0:
        return b ** q, ceil_root(b ** (3 * q + 1), 3)
    if rem == 1:
        return ceil_root(b ** (3 * q + 1), 3), ceil_root(b ** (2 * q + 1), 2)
    if rem == 2:
        return ceil_root(b ** (2 * q + 1), 2), ceil_root(b ** (3 * q + 2), 3)
    if rem == 3:
        return ceil_root(b ** (3 * q + 2), 3), b ** (q + 1)
    raise ValueError("Impossible base modulo 5")


def local_condition_witness(b, depth):
    construction = compact_constructive_coefficients(depth)
    assert b > construction["valid_for_all_bases_above"]
    a = construction["coefficients_low_to_high"]
    r = sum(ai * b ** i for i, ai in enumerate(a))
    target = b * (b - 1) // 2
    s = next(s for s in range(b - 1)
             if (s * s * (s + 1) - target) % (b - 1) == 0)
    modulus = b ** depth * (b - 1)
    crt = r + b ** depth * ((s - r) % (b - 1))
    lo, hi = length_interval(b)
    n = crt + ((lo - crt + modulus - 1) // modulus) * modulus
    assert lo <= n < hi
    assert valid_suffix(n, b, depth)
    assert (n * n * (n + 1) - target) % (b - 1) == 0
    digits = []
    for value in (n * n, n * n * n):
        while value:
            value, digit = divmod(value, b)
            digits.append(digit)
    assert len(digits) == b
    return {"base": b, "depth": depth, "n": str(n),
            "total_digits": len(digits), "distinct_digits": len(set(digits)),
            "is_nice": len(set(digits)) == b}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-limit", type=int, default=2000)
    parser.add_argument("--suffix-base-limit", type=int, default=64)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--carry-free-sum-limit", type=int, default=2000000)
    parser.add_argument("--output", type=Path,
                        default=Path("results/obstructions.json"))
    args = parser.parse_args()
    for b in range(2, args.root_limit + 1):
        target = b * (b - 1) // 2
        actual = sum((n * n * (n + 1) - target) % (b - 1) == 0
                     for n in range(b - 1))
        assert actual == digit_sum_root_count(b), (b, actual)
        collisions = sum(n * n % b == n * n * n % b for n in range(b))
        assert collisions == last_digit_collision_count(b), (b, collisions)
    suffixes = [suffix_count(b, args.depth)
                for b in range(max(2, 2 * args.depth), args.suffix_base_limit + 1)]
    data = {
        "scope": "Necessary conditions only; no full nice-number search",
        "root_formulas_verified_for_bases": [2, args.root_limit],
        "suffix_depth": args.depth,
        "suffix_enumeration": suffixes,
        "bases_with_no_suffix_survivors":
            [r["base"] for r in suffixes if not r["survivors"]],
        "compact_suffix_constructions":
            [compact_constructive_coefficients(k) for k in range(1, 21)],
        "local_condition_witnesses":
            [local_condition_witness(b, k)
             for b, k in [(100, 5), (257, 10), (1000, 20)]],
        "carry_free_digit_sum_limit": args.carry_free_sum_limit,
        "carry_free_sum_equation_solutions": [],
        "digit_sum_roots_selected_bases":
            [{"base": b, "roots": digit_sum_root_count(b),
              "modulus": b - 1,
              "last_digit_survivors": b - last_digit_collision_count(b)}
             for b in [10, 45, 54, 57, 58, 60, 64, 80, 100, 120, 125, 128]],
    }
    for digit_sum in range(1, args.carry_free_sum_limit + 1):
        discriminant = 1 + 8 * digit_sum * digit_sum * (digit_sum + 1)
        root = isqrt(discriminant)
        if root * root == discriminant:
            data["carry_free_sum_equation_solutions"].append(
                {"digit_sum": digit_sum, "base": (root + 1) // 2})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: v for k, v in data.items()
                      if k not in ("suffix_enumeration", "compact_suffix_constructions")},
                     indent=2))
    print(f"Wrote exact experiment output to {args.output}")


if __name__ == "__main__":
    main()
