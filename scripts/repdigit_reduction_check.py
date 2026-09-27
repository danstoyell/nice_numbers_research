#!/usr/bin/env python3
"""Finite closure and independent checks of the even-base repdigit reduction."""
import argparse
import json
import math
import time
from pathlib import Path
from verify import verify


def first_collision(n, base):
    seen = {}
    length = 0
    for power in (2, 3):
        value, pos = n**power, 0
        while value:
            value, digit = divmod(value, base)
            if digit in seen:
                return {'digit': digit, 'first': seen[digit],
                        'second': [power, pos]}, None
            seen[digit] = [power, pos]
            pos += 1
            length += 1
    return None, length


def search(limit, parity='even'):
    rows, solutions = [], []
    for b in range(2, limit+1):
        if (parity == 'even' and b % 2) or (parity == 'odd' and not b % 2):
            continue
        L = (b-2)//5 + 1
        record = {'base': b, 'root_length': L,
                  'repdigits': b-1, 'sum_survivors': 0,
                  'collision_rejections': 0, 'length_rejections': 0}
        if b % 5 == 1 or b % 4 == 3:
            record['base_length_exclusion'] = b % 5 == 1
            record['base_exclusion_reason'] = ('length' if b % 5 == 1
                                                else 'digit-sum parity')
            rows.append(record)
            continue
        m = b-1
        target = b*m//2 % m
        repunit = (b**L-1)//m
        for a in range(1, b):
            residue = a*L % m
            if (residue*residue*(residue+1)-target) % m:
                continue
            record['sum_survivors'] += 1
            n = a*repunit
            assert n % m == residue
            collision, length = first_collision(n, b)
            if collision is not None:
                record['collision_rejections'] += 1
                continue
            if length != b:
                record['length_rejections'] += 1
                continue
            checked = verify(n, b)
            assert checked['nice']
            solutions.append(checked)
        assert record['sum_survivors'] == (record['collision_rejections']
                                            + record['length_rejections']
                                            + sum(x['base'] == b for x in solutions))
        rows.append(record)
    return {'max_base': limit, 'base_parity': parity,
            'repdigits_in_considered_bases': sum(r['repdigits'] for r in rows),
            'sum_survivors': sum(r['sum_survivors'] for r in rows),
            'collision_rejections': sum(r['collision_rejections'] for r in rows),
            'length_rejections': sum(r['length_rejections'] for r in rows),
            'solutions': solutions, 'bases': rows,
            'scope': f'Every repdigit with the uniquely possible root length in every {parity} base from 2 through the stated bound. Exact necessary filters and early duplicate rejection.'}


def order_checks(limit=300):
    cases = 0
    for b in range(2, limit+1, 2):
        m = b-1
        for a in range(1, b):
            D = m//math.gcd(a, m)
            expected = m//math.gcd(a*a, m)
            if D == 1:
                actual = 1
            else:
                actual, value = 1, b % (D*D)
                while value != 1:
                    value = value*b % (D*D)
                    actual += 1
                assert actual == expected
            cases += 1
    return {'max_even_base': limit, 'cases': cases,
            'method': 'Direct modular iteration, compared with the prime-power order formula'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-base', type=int, default=2000)
    parser.add_argument('--parity', choices=['even', 'odd', 'all'], default='even')
    parser.add_argument('--output', default='results/repdigit-reduction-check.json')
    args = parser.parse_args()
    start = time.monotonic()
    result = {'finite_search': search(args.max_base, args.parity),
              'order_validation': order_checks(),
              'seconds': time.monotonic()-start}
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    summary = result | {'finite_search': {k: v for k, v in result['finite_search'].items()
                                         if k != 'bases'}}
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
