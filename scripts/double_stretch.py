#!/usr/bin/env python3
"""Exact validation and selective probes for n=P(B^2)."""
import argparse
import itertools
import json
import random
import time


def digits(n, b):
    out = []
    while n:
        n, d = divmod(n, b)
        out.append(d)
    return out or [0]


def evaluate(coefficients, b):
    n = 0
    for a in reversed(coefficients):
        n = n*b*b+a
    return n


def square_blocks(coefficients, b):
    k = len(coefficients)-1
    q = [sum(coefficients[i]*coefficients[j-i]
             for i in range(max(0, j-k), min(k, j)+1))
         for j in range(2*k+1)]
    carries = [0]
    blocks = []
    for value in q:
        carry, block = divmod(value+carries[-1], b*b)
        carries.append(carry)
        blocks.append(block)
    assert carries[-1] == 0
    return q, carries, blocks


def validate(args):
    rows = []
    for k in [2, 3, 4]:
        for b in range(10*k+2, 10*k+6):
            checked = 0
            for a in range(1, b):
                for inner in itertools.product(range(b), repeat=max(0, k-3)):
                    for neighbor in range(b):
                        # k=2 shares the two neighboring positions.
                        coeff = ([a, neighbor, a] if k == 2 else
                                 [a, neighbor]+list(inner)+[neighbor, a])
                        n = evaluate(coeff, b)
                        ds = digits(n*n, b)
                        assert len(set(ds)) < len(ds), (b, coeff)
                        checked += 1
            rows.append({'degree': k, 'base': b, 'checked': checked,
                         'all_squares_repeated': True})
    rng = random.Random(args.seed)
    random_checks = 0
    for _ in range(2000):
        k = rng.randrange(2, 101)
        b = 10*k+rng.randrange(2, 6)
        coeff = [rng.randrange(b) for _ in range(k+1)]
        coeff[0] = coeff[-1] = rng.randrange(1, b)
        coeff[1] = coeff[-2] = rng.randrange(b)
        q, carries, blocks = square_blocks(coeff, b)
        assert all(0 <= c <= k for c in carries)
        assert carries[1] == 0
        assert carries[2*k-1] <= 2
        assert carries[2*k] <= 1
        n = evaluate(coeff, b)
        assert sum(x*(b*b)**j for j, x in enumerate(blocks)) == n*n
        ds = digits(n*n, b)
        assert len(set(ds)) < len(ds)
        random_checks += 1
    # The degree-one palindromic endpoint condition is also checked explicitly.
    degree_one = []
    for b in range(12, 16):
        for a in range(1, b):
            n = a*(b*b+1)
            ds = digits(n*n, b)
            assert len(set(ds)) < len(ds)
        degree_one.append({'base': b, 'checked': b-1})
    result = {'exhaustive_boundary_symmetric_cases': rows,
              'total_exhaustive_checks': sum(r['checked'] for r in rows),
              'random_carry_and_reconstruction_checks': random_checks,
              'random_seed': args.seed, 'degree_one_palindromes': degree_one,
              'all_passed': True}
    return result


def probe(args):
    rng = random.Random(args.seed)
    rows = []
    for b in [65, 85, 125, 145, 185]:
        k = (b-5)//10
        endpoints = [a for a in range(b//2+1, b) if a*a % b == b-1]
        residues = [r for r in range(b-1)
                    if r*r*(r+1) % (b-1) == b*(b-1)//2 % (b-1)]
        samples = []
        count = 0
        repeated_square = 0
        best = None
        for _ in range(args.samples):
            a = rng.choice(endpoints)
            coeff = [rng.randrange(b) for _ in range(k+1)]
            coeff[0] = coeff[-1] = a
            # This guarantees the final square block receives carry one.
            coeff[-2] = rng.randrange((b*b+2*a-1)//(2*a), b)
            if coeff[1] == coeff[-2]:
                continue
            target = rng.choice(residues)
            coeff[2] = (target-(sum(coeff)-coeff[2])) % (b-1)
            n = evaluate(coeff, b)
            assert n*n*(n+1) % (b-1) == b*(b-1)//2 % (b-1)
            ds = digits(n*n, b)
            dt = digits(n*n*n, b)
            assert len(ds)+len(dt) == b
            count += 1
            unique = len(set(ds+dt))
            if best is None or unique > best['unique_digits']:
                best = {'number': str(n), 'coefficients_units_first': coeff,
                        'unique_digits': unique, 'missing_count': b-unique}
            if len(set(ds)) != len(ds):
                repeated_square += 1
                continue
            samples.append({'number': str(n), 'coefficients_units_first': coeff,
                            'square_digits_units_first': ds,
                            'cube_digits_units_first': dt,
                            'unique_combined_digits': unique,
                            'nice': unique == b})
            if len(samples) == 5:
                break
        rows.append({'base': b, 'degree': k, 'endpoint_choices': endpoints,
                     'allowed_input_sum_residues': residues,
                     'checked': count, 'squares_with_repetitions': repeated_square,
                     'square_distinct_samples': samples, 'best': best})
    return {'random_seed': args.seed, 'maximum_attempts_per_base': args.samples,
            'selection': 'equal endpoints, asymmetric neighbors, endpoint square carry one, exact digit-sum congruence',
            'records': rows,
            'solutions': [{'base': r['base'], **s} for r in rows
                          for s in r['square_distinct_samples'] if s['nice']]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['validate', 'probe'], default='validate')
    parser.add_argument('--seed', type=int, default=20260925)
    parser.add_argument('--samples', type=int, default=20000)
    parser.add_argument('--output', default='results/double-stretch-validation.json')
    args = parser.parse_args()
    start = time.monotonic()
    result = validate(args) if args.mode == 'validate' else probe(args)
    result['elapsed_seconds'] = time.monotonic()-start
    with open(args.output, 'w') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps(result, indent=2))
