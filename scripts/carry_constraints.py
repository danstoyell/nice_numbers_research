#!/usr/bin/env python3
"""Exact carry/sparsity bounds and deterministic checks; no full search."""
import argparse
import json
import math
import random
from pathlib import Path


def digits(n, b):
    result = []
    while n:
        n, digit = divmod(n, b)
        result.append(digit)
    return result or [0]


def convolve(a, b):
    result = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i + j] += x * y
    return result


def normalize(raw, b):
    output, incoming = [], []
    carry = 0
    j = 0
    while j < len(raw) or carry:
        incoming.append(carry)
        carry, digit = divmod((raw[j] if j < len(raw) else 0) + carry, b)
        output.append(digit)
        j += 1
    return output, incoming


def lengths(b):
    q, r = divmod(b - 2, 5)
    if r == 4:
        return None
    return [(2*q+1, 3*q+1), (2*q+1, 3*q+2),
            (2*q+2, 3*q+2), (2*q+2, 3*q+3)][r]


def smallest_subset_popcount(bit_width, count):
    total = 0
    for weight in range(bit_width + 1):
        taken = min(count, math.comb(bit_width, weight))
        total += taken * weight
        count -= taken
    assert count == 0
    return total


def binary_power_popcount_upper(t):
    return t * (t + 1) // 2, t + 2*t*(t-1) + 2*math.comb(t, 3)


def base_constraints(b):
    shape = lengths(b)
    if shape is None or b % 4 == 3:
        return {"base": b, "excluded_by_known_length_or_parity": True}
    square_length, cube_length = shape
    k = (b - 2) // 5
    forced_nonzero_edges = max(0, 2*k - (b + 2)//3)
    carry_lower = max(1, forced_nonzero_edges if b % 3 == 0
                      else (forced_nonzero_edges + 1)//2)
    sparsity_lower = next(t for t in range(1, k + 2)
                          if 3*t*(t+1)//2 >= square_length - 1)
    target = b*(b-1)//2
    s = 1
    while (s*s*(s+1) - target < (b-1)*carry_lower
           or (s*s*(s+1)-target) % (b-1)):
        s += 1
    result = {"base": b, "input_digit_length": k+1,
              "square_length": square_length, "cube_length": cube_length,
              "minimum_nonzero_base_digits": sparsity_lower,
              "minimum_cube_residue_breaking_edges": forced_nonzero_edges,
              "minimum_total_carry_mass": carry_lower,
              "minimum_input_digit_sum": s,
              "minimum_largest_input_digit": (s+k)//(k+1)}
    if b & (b-1) == 0:
        width = b.bit_length() - 1
        minimum_square = smallest_subset_popcount(width, square_length)
        minimum_cube = smallest_subset_popcount(width, cube_length)
        total = width*b//2
        t = 1
        while True:
            square_upper, cube_upper = binary_power_popcount_upper(t)
            if (square_upper >= minimum_square and cube_upper >= minimum_cube
                    and square_upper + cube_upper >= total):
                break
            t += 1
        result.update({"binary_digit_width": width,
                       "minimum_square_popcount": minimum_square,
                       "minimum_cube_popcount": minimum_cube,
                       "required_total_output_popcount": total,
                       "minimum_input_popcount": t})
    return result


def check_identities(n, b):
    a = digits(n, b)
    k = len(a)-1
    raw_square = convolve(a, a)
    raw_cube = convolve(raw_square, a)
    square, sc = normalize(raw_square, b)
    cube, cc = normalize(raw_cube, b)
    assert square == digits(n*n, b)
    assert cube == digits(n*n*n, b)
    assert sum(square) + sum(cube) == sum(a)**2 + sum(a)**3 - (b-1)*(sum(sc)+sum(cc))
    for j, digit in enumerate(cube):
        outgoing = cc[j+1] if j+1 < len(cc) else 0
        raw = raw_cube[j] if j < len(raw_cube) else 0
        if j % 3:
            assert raw % 3 == 0
            assert digit % 3 == (cc[j] - b*outgoing) % 3
    if b % 2 == 0:
        for j, digit in enumerate(square):
            source = a[j//2] if j % 2 == 0 and j//2 < len(a) else 0
            assert digit % 2 == (source + sc[j]) % 2
    support = {i for i, ai in enumerate(a) if ai}
    sumset2 = {i+j for i in support for j in support}
    sumset3 = {i+j for i in sumset2 for j in support}
    if k+1 < b:
        assert max(sc, default=0) <= (k+1)*(b-1) < b*b
        assert max(cc, default=0) <= (k+1)**2*(b-1)**2 < b**4
        covered_square = {i+offset for i in sumset2 for offset in range(3)}
        covered_cube = {i+offset for i in sumset3 for offset in range(5)}
        assert all(not digit or j in covered_square for j, digit in enumerate(square))
        assert all(not digit or j in covered_cube for j, digit in enumerate(cube))
    binary_weight = n.bit_count()
    upper_square, upper_cube = binary_power_popcount_upper(binary_weight)
    assert (n*n).bit_count() <= upper_square
    assert (n*n*n).bit_count() <= upper_cube


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-base", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260924)
    parser.add_argument("--output", type=Path, default=Path("results/carry-constraints.json"))
    args = parser.parse_args()
    bases = [10, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
    random_source = random.Random(args.seed)
    checks = []
    check_identities(69, 10)
    for b in [10, 32, 64, 128, 512]:
        k = (b-2)//5
        for _ in range(args.samples_per_base):
            n = random_source.randrange(b**k, b**(k+1))
            check_identities(n, b)
        checks.append({"base": b, "random_input_digit_length": k+1,
                       "identity_checks": args.samples_per_base})
    result = {"scope": "Necessary bounds and arithmetic identity checks, not a full search",
              "seed": args.seed,
              "constraints": [base_constraints(b) for b in bases],
              "random_identity_checks": checks,
              "known_nice_identity_check": {"n": 69, "base": 10}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
