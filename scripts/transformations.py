#!/usr/bin/env python3
"""Bounded exact searches of dense digit alphabets, with genuine carries.

Exhaustive per (base, alphabet) only when status says exhaustive. An input
prefix determines the same-length suffix of both powers; those digits are
computed by raw convolution plus their actual base-b carries.
"""
import argparse
from bisect import bisect_left
import collections
import hashlib
import json
import math
import time


def digits(n, b):
    out = []
    while n:
        n, d = divmod(n, b)
        out.append(d)
    return out or [0]


def search(b, alphabet, node_limit, deadline):
    start = time.monotonic()
    length = (b-2)//5+1
    stats = {'base': b, 'alphabet': alphabet, 'input_digits': length,
             'nodes': 0, 'nodes_by_depth': [0]*(length+1),
             'complete_prefixes': 0, 'length_valid': 0,
             'solutions': [], 'status': 'exhaustive', 'best': None}
    if min(alphabet) < 0 or max(alphabet) >= b or min(alphabet) == 0:
        stats['status'] = 'invalid_alphabet'
        return stats
    repunit = (b**length-1)//(b-1)
    lo, hi = min(alphabet)*repunit, max(alphabet)*repunit
    def total_length(n):
        return len(digits(n*n, b))+len(digits(n*n*n, b))
    if total_length(lo) > b or total_length(hi) < b:
        stats['obstruction'] = 'length_interval'
        return stats
    modulus = b-1
    target = b*modulus//2 % modulus
    sums = [s for s in range(min(alphabet)*length, max(alphabet)*length+1)
            if s*s*(s+1) % modulus == target]
    stats['allowed_digit_sums'] = sums
    if not sums:
        stats['obstruction'] = 'digit_sum_congruence'
        return stats
    powers = [b**i for i in range(length)]
    stopped = False

    def visit(a, squares, carry2, carry3, used, digit_sum, n):
        nonlocal stopped
        if stopped:
            return
        if stats['nodes'] >= node_limit:
            stopped = True
            stats['status'] = 'node_limit'
            return
        if stats['nodes'] % 1024 == 0 and time.monotonic() >= deadline:
            stopped = True
            stats['status'] = 'time_limit'
            return
        stats['nodes'] += 1
        j = len(a)
        stats['nodes_by_depth'][j] += 1
        left = length-j
        at = bisect_left(sums, digit_sum+min(alphabet)*left)
        if at == len(sums) or sums[at] > digit_sum+max(alphabet)*left:
            return
        if not left:
            stats['complete_prefixes'] += 1
            ds = digits(n*n, b)+digits(n*n*n, b)
            if len(ds) != b:
                return
            stats['length_valid'] += 1
            count = len(set(ds))
            if stats['best'] is None or count > stats['best']['unique_digits']:
                stats['best'] = {'number': str(n), 'unique_digits': count,
                                 'missing_count': b-count}
            if count == b:
                stats['solutions'].append(str(n))
            return
        for x in alphabet:
            aa = a+[x]
            q = sum(aa[i]*aa[j-i] for i in range(j+1))
            ss = squares+[q]
            r = sum(ss[i]*aa[j-i] for i in range(j+1))
            cc2, d2 = divmod(q+carry2, b)
            cc3, d3 = divmod(r+carry3, b)
            bits = (1 << d2) | (1 << d3)
            if d2 == d3 or used & bits:
                continue
            visit(aa, ss, cc2, cc3, used | bits, digit_sum+x,
                  n+x*powers[j])

    visit([], [], 0, 0, 0, 0, 0)
    stats['elapsed_seconds'] = time.monotonic()-start
    return stats


def quasi_transformations(args):
    """Generate quasi-nice seeds exhaustively through base 14, then transform."""
    seeds = []
    seed_counts = {}
    for b in range(2, 15):
        if b % 3 == 1 or b % 4 == 3:
            continue
        length = (b-2)//3+1
        count = 0
        for n in range(b**(length-1), b**length):
            count += 1
            if n*(n+1) % (b-1) != b*(b-1)//2 % (b-1):
                continue
            ds = digits(n, b)+digits(n*n, b)
            if len(ds) == b and len(set(ds)) == b:
                seeds.append({'number': n, 'base': b})
        seed_counts[b] = count
    def possible_base(n):
        # The total length is nonincreasing in b, while b increases.
        lo, hi = 2, 5*n.bit_length()+2
        while lo < hi:
            mid = (lo+hi)//2
            delta = len(digits(n*n, mid))+len(digits(n*n*n, mid))-mid
            if delta > 0:
                lo = mid+1
            else:
                hi = mid
        if len(digits(n*n, lo))+len(digits(n*n*n, lo)) == lo:
            return lo
        return None
    tested = 0
    valid_length = 0
    solutions = set()
    best = []
    for seed in seeds:
        n, b = seed['number'], seed['base']
        ds = digits(n, b)
        candidates = [('offset', n+c) for c in range(-16, 17)]
        candidates += [('power', n**e) for e in range(1, 7)]
        candidates += [('quadratic', n*n+a*n+c)
                       for a in [-2, -1, 0, 1, 2] for c in [-1, 0, 1]]
        candidates += [('digit_reverse', sum(d*b**i for i, d in enumerate(reversed(ds))))]
        candidates += [('digit_complement', b**len(ds)-1-n)]
        for family, value in candidates:
            if value <= 0:
                continue
            tested += 1
            base = possible_base(value)
            if base is None:
                continue
            valid_length += 1
            joined = digits(value*value, base)+digits(value*value*value, base)
            unique = len(set(joined))
            if unique == base:
                solutions.add((base, value))
            if base-unique <= 2:
                best.append({'seed': seed, 'family': family, 'number': str(value),
                             'base': base, 'unique_digits': unique})
    result = {'quasi_seed_search': seed_counts, 'seeds': seeds,
              'transform_instances': tested, 'length_valid_instances': valid_length,
              'solutions': [{'base': b, 'number': str(n)} for b, n in sorted(solutions)],
              'within_two_missing_digits': best,
              'scope': 'All quasi-nice seeds through base 14; finite stated transformations only.'}
    with open(args.output, 'w') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('seeds', 'within_two_missing_digits')}, indent=2))
    print('seed count', len(seeds))


def growing_denominators(args):
    """A Fermat-integral repunit quotient with d about sqrt(b)."""
    def prime(n):
        return n >= 2 and all(n % p for p in range(2, math.isqrt(n)+1))
    def order(a, modulus, phi):
        value = phi
        for p in range(2, math.isqrt(phi)+2):
            if not prime(p):
                continue
            while value % p == 0 and pow(a, value//p, modulus) == 1:
                value //= p
        # A prime factor larger than sqrt(phi) occurs at most once.
        residual = phi
        for p in range(2, math.isqrt(phi)+2):
            while residual % p == 0:
                residual //= p
        if residual > 1:
            while value % residual == 0 and pow(a, value//residual, modulus) == 1:
                value //= residual
        return value
    rows = []
    for d in range(19, args.denominator_max+1, 5):
        if not prime(d):
            continue
        b, m = d*d-3, (d*d-1)//5
        power = b**m
        assert (power-1) % d == 0
        n = (power-1)//d
        n2, n3 = n*n, n*n*n
        expected2, expected3 = 2*m-1, 3*m-1
        assert n2*b*b >= power*power and n2*b < power*power
        assert n3*b*b >= power*power*power and n3*b < power*power*power
        assert expected2+expected3 == b
        assert n*n*(n+1) % (b-1) == 0
        used = {}
        values = [n2, n3]
        collision = None
        for position in range(expected3):
            for ix in [0, 1]:
                if not values[ix]:
                    continue
                values[ix], digit = divmod(values[ix], b)
                at = {'power': ix+2, 'position_from_units': position}
                if digit in used:
                    collision = {'digit': digit, 'first': used[digit], 'second': at}
                    break
                used[digit] = at
            if collision:
                break
        rows.append({'d': d, 'base': b, 'm': m,
                     'number_formula': '(base**m-1)//d',
                     'square_length': expected2, 'cube_length': expected3,
                     'order_mod_d_squared': order(b, d*d, d*(d-1)),
                     'full_period_d_squared': order(b, d*d, d*(d-1)) == d*(d-1),
                     'unique_suffix_digits_before_collision': len(used),
                     'first_collision': collision, 'nice': collision is None})
    result = {'family': 'd prime, d=4 mod 5; b=d*d-3; m=(d*d-1)/5; n=(b**m-1)/d',
              'denominator_max': args.denominator_max, 'records': rows,
              'solutions': [r for r in rows if r['nice']]}
    with open(args.output, 'w') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps({'candidate_count': len(rows),
                      'largest_base': rows[-1]['base'] if rows else None,
                      'solutions': result['solutions']}, indent=2))


def near_miss_lifts(args):
    """Lift seed digit polynomials into larger bases by composition/repetition."""
    start = time.monotonic()
    raw = open(args.snapshot, 'rb').read()
    seeds = json.loads(raw)
    counts = collections.defaultdict(collections.Counter)
    best = {}
    solutions = []
    seed_sum_survivors = 0
    for seed in seeds:
        value, original_base = seed['number'], seed['base']
        original = digits(value, original_base)
        original_powers = digits(value*value, original_base)+digits(value**3, original_base)
        assert len(original_powers) == original_base
        assert len(set(original_powers)) == seed['num_uniques']
        seed_sum_survivors += (value*value*(value+1) % (original_base-1)
                              == original_base*(original_base-1)//2 % (original_base-1))
        L = len(original)
        patterns = [('repeat', t, t*L) for t in range(2, 9)]
        patterns += [('stretch', t, t*(L-1)+1) for t in [2, 3]]
        for layout, t, D in patterns:
            for b in range(5*D-3, 5*D+1):
                if b < args.min_base or b % 5 == 1 or b % 4 == 3:
                    continue
                scales = sorted({1, 2, 3, (b-1)//(original_base-1)})
                shifts = sorted({0, 1, b//3, 2*b//3, b-1})
                maps = [(f'affine:{scale}:{shift}', [(scale*d+shift) % b for d in original])
                        for scale in scales for shift in shifts]
                rank = [d*(b-1)//(original_base-1) for d in original]
                maps += [('proportional', rank), ('proportional_complement', [b-1-d for d in rank])]
                for label, transformed in maps:
                    counts[layout]['generated_instances'] += 1
                    if transformed[-1] == 0:
                        counts[layout]['leading_zero_rejections'] += 1
                        continue
                    if transformed[0] == 0:
                        counts[layout]['trailing_zero_rejections'] += 1
                        continue
                    if layout == 'repeat':
                        word = transformed*t
                    else:
                        word = [0]*D
                        word[::t] = transformed
                    S = sum(word)
                    if S*S*(S+1) % (b-1) != b*(b-1)//2 % (b-1):
                        continue
                    counts[layout]['digit_sum_survivors'] += 1
                    n = 0
                    for digit in reversed(word):
                        n = n*b+digit
                    ds = digits(n*n, b)+digits(n*n*n, b)
                    if len(ds) != b:
                        continue
                    counts[layout]['length_valid_survivors'] += 1
                    unique = len(set(ds))
                    entry = {'base': b, 'number': str(n), 'unique_digits': unique,
                             'missing_count': b-unique, 'seed_number': str(value),
                             'seed_base': original_base, 'layout': layout,
                             'factor': t, 'digit_map': label}
                    key = (layout, b)
                    if key not in best or unique > best[key]['unique_digits']:
                        best[key] = entry
                    if unique == b:
                        solutions.append(entry)
    result = {'source_url': 'https://data.nicenumbers.net/cache_notable_numbers?select=number,niceness,base,num_uniques&order=off_by.desc',
              'snapshot': args.snapshot, 'snapshot_sha256': hashlib.sha256(raw).hexdigest(),
              'snapshot_date': '2026-09-23', 'seed_count': len(seeds),
              'seed_digit_sum_survivors': seed_sum_survivors,
              'parameters': {'minimum_target_base': args.min_base,
                             'repeat_factors': list(range(2, 9)), 'stretch_factors': [2, 3]},
              'elapsed_seconds': time.monotonic()-start, 'counts': dict(counts),
              'solutions': solutions, 'best_by_layout_and_base': list(best.values()),
              'scope': 'Finite seed/layout/digit-map instances; counts include duplicates.'}
    with open(args.output, 'w') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('best_by_layout_and_base',)}, indent=2))


def stretch_exceptions(args):
    """Exhaust the small cases left by the t>=3 polynomial-stretch proof."""
    records = []
    for b in range(17, 21):
        checked = length_valid = square_distinct = 0
        solutions = []
        square_survivors = []
        for a in range(1, b):
            for c in range(1, b):
                n = a*b**3+c
                checked += 1
                ds, dt = digits(n*n, b), digits(n*n*n, b)
                if len(ds)+len(dt) != b:
                    continue
                length_valid += 1
                if len(set(ds)) == len(ds):
                    square_distinct += 1
                    square_survivors.append({'number': n, 'a': a, 'c': c,
                                             'square_digits_most_significant_first': list(reversed(ds)),
                                             'cube_digits_most_significant_first': list(reversed(dt))})
                if len(set(ds+dt)) == b:
                    solutions.append(n)
        records.append({'base': b, 'family': 'a*b**3+c, 1<=a,c<b',
                        'checked': checked, 'length_valid': length_valid,
                        'square_distinct': square_distinct,
                        'square_survivors': square_survivors, 'solutions': solutions})
    constants = []
    for b in range(2, 6):
        for n in range(1, b):
            ds = digits(n*n, b)+digits(n*n*n, b)
            constants.append({'base': b, 'number': n,
                              'total_digits': len(ds), 'unique_digits': len(set(ds)),
                              'nice': len(ds)==b and len(set(ds))==b})
    result = {'degree_one_t_three': records, 'degree_zero': constants,
              'solutions': [(r['base'], n) for r in records for n in r['solutions']]
                           + [(r['base'], r['number']) for r in constants if r['nice']]}
    with open(args.output, 'w') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps(result, indent=2))


def main(args):
    if args.mode == 'quasi':
        quasi_transformations(args)
        return
    if args.mode == 'growing-denominators':
        growing_denominators(args)
        return
    if args.mode == 'near-miss-lifts':
        near_miss_lifts(args)
        return
    if args.mode == 'stretch-exceptions':
        stretch_exceptions(args)
        return
    start = time.monotonic()
    deadline = start+args.seconds
    alphabets = [[int(x) for x in a.split(',')] for a in args.alphabets]
    records = []
    with open(args.output, 'w') as out:
        for b in range(2, args.max_base+1):
            if b % 5 == 1 or b % 4 == 3:
                continue
            for alphabet in alphabets:
                if max(alphabet) >= b:
                    continue
                if time.monotonic() >= deadline:
                    break
                result = search(b, alphabet, args.node_limit, deadline)
                records.append(result)
                out.write(json.dumps(result)+'\n')
                out.flush()
            if time.monotonic() >= deadline:
                break
    summary = {'parameters': vars(args), 'elapsed_seconds': time.monotonic()-start,
               'records': len(records), 'nodes': sum(r['nodes'] for r in records),
               'exhaustive': sum(r['status']=='exhaustive' for r in records),
               'node_limited': sum(r['status']=='node_limit' for r in records),
               'time_limited': sum(r['status']=='time_limit' for r in records),
               'last_base': records[-1]['base'] if records else None,
               'solutions': [(r['base'], n) for r in records for n in r['solutions']]}
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['dense', 'quasi', 'growing-denominators', 'near-miss-lifts', 'stretch-exceptions'], default='dense')
    parser.add_argument('--denominator-max', type=int, default=199)
    parser.add_argument('--min-base', type=int, default=57)
    parser.add_argument('--snapshot', default='results/public-near-misses-2026-09-23.json')
    parser.add_argument('--max-base', type=int, default=300)
    parser.add_argument('--alphabets', nargs='+', default=['2,3', '1,2,3,4'])
    parser.add_argument('--node-limit', type=int, default=250000)
    parser.add_argument('--seconds', type=float, default=120)
    parser.add_argument('--output', default='results/transformations-dense.jsonl')
    main(parser.parse_args())
