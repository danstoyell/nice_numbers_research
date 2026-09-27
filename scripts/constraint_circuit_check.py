#!/usr/bin/env python3
"""Reproduce exact arithmetic checks for the experimental SMT circuits."""
import itertools
import json
import random
import z3
from constraint_search import karatsuba_product, sorted_digit_constraints


def main():
    rng = random.Random(20260924)
    results = []
    for aw, bw in [(1, 1), (3, 8), (8, 8), (9, 10), (17, 17), (23, 47),
                   (64, 65), (179, 179), (357, 179), (921, 921)]:
        a, b = z3.BitVec("a", aw), z3.BitVec("b", bw)
        expression = karatsuba_product(a, b, 4 if max(aw, bw) <= 17 else 16)
        for _ in range(10):
            av, bv = rng.getrandbits(aw), rng.getrandbits(bw)
            value = z3.simplify(z3.substitute(expression,
                (a, z3.BitVecVal(av, aw)), (b, z3.BitVecVal(bv, bw)))).as_long()
            assert value == av*bv, (aw, bw, av, bv, value)
        results.append({"widths": [aw, bw], "random_exact_products": 10})
    for aw, bw in [(3, 4), (5, 5), (6, 7)]:
        a, b = z3.BitVec("a", aw), z3.BitVec("b", bw)
        solver = z3.Solver()
        solver.set(timeout=10000)
        solver.add(karatsuba_product(a, b, 3) != z3.ZeroExt(bw, a)*z3.ZeroExt(aw, b))
        status = str(solver.check())
        assert status == "unsat", status
        results.append({"widths": [aw, bw], "symbolic_equivalence": status})
    checks = 0
    for base in [2, 3, 4]:
        width = (base-1).bit_length()
        for ds in itertools.product(range(base), repeat=base):
            assertions = sorted_digit_constraints(
                [z3.BitVecVal(d, width) for d in ds], base)
            got = all(z3.is_true(z3.simplify(x)) for x in assertions)
            assert got == (sorted(ds) == list(range(base)))
            checks += 1
    for base in [5, 8, 10, 16, 32, 128, 512]:
        width = (base-1).bit_length()
        ds = list(range(base))
        rng.shuffle(ds)
        assert all(z3.is_true(z3.simplify(x)) for x in sorted_digit_constraints(
            [z3.BitVecVal(d, width) for d in ds], base))
        ds[0] = ds[1]
        assert not all(z3.is_true(z3.simplify(x)) for x in sorted_digit_constraints(
            [z3.BitVecVal(d, width) for d in ds], base))
        checks += 2
    print(json.dumps({"seed": 20260924, "karatsuba_validation": results,
                      "sorting_network_checks": checks}, indent=2))


if __name__ == "__main__":
    main()
