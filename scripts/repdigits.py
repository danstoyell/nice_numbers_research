#!/usr/bin/env python3
"""Exact finite checks accompanying the prime-power-plus-one repdigit proof."""
import argparse
import json
import time
from pathlib import Path
from verify import verify


def digits_lsf(n, b):
    out = []
    while n:
        n, r = divmod(n, b)
        out.append(r)
    return out or [0]


def finite_check(limit=124):
    candidates = 0
    length_valid = 0
    solutions = []
    for b in range(2, limit + 1):
        # If a root has L digits, its two powers have 5L-3..5L
        # digits. These disjoint ranges determine L uniquely.
        L = (b - 2) // 5 + 1
        repunit = (b**L - 1) // (b - 1)
        for a in range(1, b):
            candidates += 1
            n = a * repunit
            ds = digits_lsf(n*n, b) + digits_lsf(n*n*n, b)
            if len(ds) != b:
                continue
            length_valid += 1
            nice = sorted(ds) == list(range(b))
            independent = verify(n, b)
            assert independent['nice'] == nice
            if nice:
                solutions.append(independent)
    return {'max_base': limit, 'repdigit_candidates': candidates,
            'length_valid': length_valid, 'solutions': solutions,
            'scope': 'Every positive repdigit in every base 2..124 whose root length could satisfy the nice-number length condition'}


def endpoint_check(limit=2000):
    cases = 0
    for b in range(125, limit + 1, 5):
        L = b // 5
        n = (b - 6) * ((b**L - 1) // (b - 1))
        sq = digits_lsf(n*n, b)
        cu = digits_lsf(n*n*n, b)
        assert len(sq) == 2*L and len(cu) == 3*L
        assert sq[:2] == [36, 60]
        assert cu[-2:] == [60, b - 15]
        assert not verify(n, b)['nice']
        cases += 1
    return {'min_base': 125, 'max_base': limit, 'step': 5,
            'cases': cases, 'shared_digit': 60,
            'square_position_from_units': 1,
            'cube_position_from_leading': 1,
            'scope': 'Validation of the endpoint identity; the note supplies its all-base proof'}


def residual_edge_probe():
    """Check fixed edges of the two unresolved composite-base templates.

    Prefixes are evaluated through exact rational bounds, avoiding enormous
    full roots. The error is less than 3*b^(K-L); since L>K+5 this is
    smaller than the minimum nonzero fractional gap 1/(b-1)^3.
    """
    rows = []
    K = 30
    for numerator, residues in [(1, [70, 160, 250]), (2, [40, 130, 220])]:
        for residue in residues:
            b = 270*4000 + residue
            m, L = b-1, b//5
            a = numerator*m//3 - 5
            assert 3*a == numerator*m - 15
            assert L > K+5
            modulus = b**K
            root_suffix = -a * pow(m, -1, modulus) % modulus
            edges = []
            for e in (2, 3):
                low = digits_lsf(pow(root_suffix, e, modulus), b)
                low += [0]*(K-len(low))
                prefix, remainder = divmod(modulus*a**e, m**e)
                assert remainder > 0
                high = list(reversed(digits_lsf(prefix, b)))
                assert len(high) == K
                edges += [(v, f'{e}:units:{i}') for i, v in enumerate(low)]
                edges += [(v, f'{e}:leading:{i}') for i, v in enumerate(high)]
            seen, collisions = {}, []
            for value, position in edges:
                if value in seen:
                    collisions.append([seen[value], position, value])
                seen[value] = position
            rows.append({'base': b, 'repdigit': a, 'root_length': L,
                         'fraction_numerator': numerator, 'fraction_denominator': 3,
                         'edge_depth_each_end_each_power': K,
                         'distinct_edge_digits': len(seen),
                         'collisions': collisions})
    return {'cases': rows,
            'scope': 'Six exact edge probes only; no full digit check and no nice-number claim'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='results/repdigits.json')
    args = parser.parse_args()
    started = time.monotonic()
    result = {'finite_check': finite_check(),
              'endpoint_identity_checks': endpoint_check(),
              'residual_edge_probe': residual_edge_probe(),
              'seconds': time.monotonic() - started}
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
