#!/usr/bin/env python3
"""Reproducible, bounded tests of structured nice-number constructions.

Uses only Python's standard library and integer arithmetic. Families are finite
experiments, not a search of all n in their bases. Includes exact regressions.
"""
import argparse
import collections
import json
import math
import time


def digits(n, b):
    out = []
    while n:
        n, d = divmod(n, b)
        out.append(d)
    return out or [0]


def assess(n, b):
    ds = digits(n*n, b) + digits(n*n*n, b)
    return len(ds), len(set(ds))


def families(b, coefficient_max, denominator_max):
    k = (b - 2) // 5
    power = b**k
    lim = min(b-1, coefficient_max)
    for a in range(1, lim+1):
        for c in range(1, lim+1):
            yield 'two_blocks_plus', a*power+c
            if a >= 2:
                yield 'two_blocks_minus', a*power-c
    for c in range(1, lim+1):
        yield 'near_power', b*power-c
    yield 'stretch_69', 6*power+9
    if k:
        # Every base-b digit arithmetic progression of this length.
        for step in range(-(b-1)//k, (b-1)//k+1):
            lo = max(0, -k*step)
            hi = min(b-1, b-1-k*step)
            for a in range(lo, hi+1):
                if a+k*step == 0:
                    continue
                value = sum((a+j*step)*b**j for j in range(k+1))
                yield 'arithmetic_digits', value
    scale = b*power
    for den in range(2, denominator_max+1):
        for num in range(1, den):
            if math.gcd(num, den) != 1:
                continue
            value = num*scale//den
            for offset in range(-2, 3):
                yield 'rational_fraction', value+offset


def run(args):
    assert assess(69, 10) == (10, 10)
    assert assess(330169542960890, 45) == (45, 44)
    counts = collections.defaultdict(collections.Counter)
    best = {}
    solutions = set()
    checked_bases = []
    start = time.monotonic()
    for b in range(2, args.max_base+1):
        if b % 5 == 1 or b % 4 == 3:
            continue
        checked_bases.append(b)
        modulus = b-1
        target = b*modulus//2 % modulus
        for family, n in families(b, args.coefficient_max, args.denominator_max):
            counts[family]['generated'] += 1
            if n <= 0:
                continue
            # Necessary digit-sum condition, evaluated before large powers.
            r = n % modulus
            if r*r*(r+1) % modulus != target:
                continue
            counts[family]['modular_survivors'] += 1
            length, uniques = assess(n, b)
            if length != b:
                continue
            counts[family]['length_valid_modular_survivors'] += 1
            item = {'number': str(n), 'base': b, 'unique_digits': uniques,
                    'missing_count': b-uniques, 'family': family}
            old = best.get((family, b))
            if old is None or uniques > old['unique_digits']:
                best[family, b] = item
            if uniques == b:
                solutions.add((b, n))
        if b % 25 == 0:
            print(f'completed base {b}', flush=True)
    summary = {'parameters': vars(args), 'checked_bases': checked_bases,
               'elapsed_seconds': time.monotonic()-start,
               'counts': dict(counts),
               'solutions': [{'base': b, 'number': str(n)}
                             for b, n in sorted(solutions)],
               'best_by_family_and_base': list(best.values()),
               'caveat': 'Finite structured families only; duplicate candidates across families count repeatedly.'}
    with open(args.output, 'w') as out:
        json.dump(summary, out, indent=2)
        out.write('\n')
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ('checked_bases', 'best_by_family_and_base')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-base', type=int, default=300)
    parser.add_argument('--coefficient-max', type=int, default=24)
    parser.add_argument('--denominator-max', type=int, default=64)
    parser.add_argument('--output', default='results/constructions.json')
    run(parser.parse_args())
