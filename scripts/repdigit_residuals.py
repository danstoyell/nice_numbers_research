#!/usr/bin/env python3
"""Affine collision certificates for the two residual even-base repdigits.

All calculations use exact integers. A certificate covers one entire
arithmetic progression above a computed threshold by linear inequalities.
"""
import argparse
import json
import time

MODULUS = 4050


def cube_affines(t, residue, count=8):
    carry = 0
    out = []
    inverse = pow(residue, -1, 27)
    for j in range(count):
        raw = -45*t*t-675*t*(j+1)-3375*(j+1)*(j+2)//2
        if j == 0:
            raw -= t**3
        next_carry = ((raw+carry)*inverse) % 27-27
        out.append((-next_carry, raw+carry))
        carry = next_carry
    return out


def carry_residue(t, side, j):
    if side == 'low':
        table = [1, 7, 4] if t == 1 else [4, 7, 1]
    else:
        table = [5, 8, 2] if t == 1 else [8, 5, 2]
    return table[j % 3]


def square_carry(t, b, side, j):
    m = b-1
    r = carry_residue(t, side, j)
    num = 225*j+30*t-1 if side == 'low' else 225*(2*(b//5)-j)-30*t
    return r+9*((num-r*m)//(9*m))


def square_digit(t, b, side, j):
    left = square_carry(t, b, side, j)
    right = square_carry(t, b, side, j+1)
    raw = 225*(j+1)+30*t if side == 'low' else 225*(2*(b//5)-j-1)-30*t
    assert (raw+left-b*right) % 9 == 0
    return (raw+left-b*right)//9


def linear_conditions(t, residue, cube_index, affines, side, w, wn, j0, js):
    """Return C,D for conditions C*q+D>=0, b=residue+4050*q."""
    terms = []
    def add(name, fn):
        d = fn(0)
        terms.append({'name': name, 'slope': fn(1)-d, 'constant': d})
    b = lambda q: residue+MODULUS*q
    L = lambda q: b(q)//5
    j = lambda q: j0+js*q
    add('base_at_least_2001', lambda q: b(q)-2001)
    add('cube_position_below_L', lambda q: L(q)-cube_index-1)
    for ix, (u, v) in enumerate(affines[:cube_index+1]):
        add(f'cube_digit_{ix}_nonnegative', lambda q,u=u,v=v: u*b(q)+v)
        add(f'cube_digit_{ix}_below_base', lambda q,u=u,v=v: 27*b(q)-1-u*b(q)-v)
    if side == 'low':
        add('square_position_at_least_3', lambda q: j(q)-3)
        add('square_position_below_low_end', lambda q: L(q)-2-j(q))
    else:
        add('square_position_after_peak', lambda q: j(q)-L(q)-3)
        add('square_position_before_top', lambda q: 2*L(q)-2-j(q))
    for offset, carry in [(0, w), (1, wn)]:
        def numerator(q,offset=offset):
            x = j(q)+offset
            return 225*x+30*t-1 if side == 'low' else 225*(2*L(q)-x)-30*t
        add(f'carry_{offset}_lower', lambda q,c=carry: numerator(q)-c*(b(q)-1))
        add(f'carry_{offset}_upper', lambda q,c=carry: (c+9)*(b(q)-1)-1-numerator(q))
    return terms


def threshold(terms):
    lower = 0
    for term in terms:
        slope, constant = term['slope'], term['constant']
        if slope < 0 or slope == 0 and constant < 0:
            return None
        if constant < 0:
            lower = max(lower, (-constant+slope-1)//slope)
    return lower


def make_certificate(t, residue, max_cube_index):
    affines = cube_affines(t, residue, max_cube_index+1)
    best = None
    for cube_index, (u, v) in enumerate(affines):
        assert (u*residue+v) % 27 == 0
        d0 = (u*residue+v)//27
        for side in ['low', 'high']:
            for w in range(-8, 47):
                for wn in range(-8, 47):
                    numerator = 9*d0-30*t-w+residue*wn if side == 'low' else 9*d0+30*t-w+residue*wn
                    if numerator % 225:
                        continue
                    if side == 'low':
                        j0, js = numerator//225-1, 6*u+18*wn
                    else:
                        j0, js = 2*(residue//5)-1-numerator//225, 1620-6*u-18*wn
                    if js % 3:
                        continue
                    if w % 9 != carry_residue(t, side, j0):
                        continue
                    if wn % 9 != carry_residue(t, side, j0+1):
                        continue
                    terms = linear_conditions(t, residue, cube_index, affines, side, w, wn, j0, js)
                    qmin = threshold(terms)
                    if qmin is None:
                        continue
                    row = {'template': t, 'base_residue_mod_4050': residue,
                           'cube_position_from_units': cube_index,
                           'cube_digit_numerator': {'base_coefficient': u, 'constant': v},
                           'square_half': side, 'square_position': {'constant': j0, 'q_coefficient': js},
                           'square_carry': w, 'next_square_carry': wn,
                           'minimum_q': qmin, 'minimum_base': residue+MODULUS*qmin,
                           'linear_conditions': terms}
                    if best is None or (qmin, cube_index, side) < (best['minimum_q'], best['cube_position_from_units'], best['square_half']):
                        best = row
        # Continue: a later digit can yield a much smaller all-base threshold.
    return best


def verify_certificate(row):
    t, residue = row['template'], row['base_residue_mod_4050']
    ix = row['cube_position_from_units']
    affines = cube_affines(t, residue, ix+1)
    assert affines[ix] == (row['cube_digit_numerator']['base_coefficient'], row['cube_digit_numerator']['constant'])
    side = row['square_half']
    w, wn = row['square_carry'], row['next_square_carry']
    j0, js = row['square_position']['constant'], row['square_position']['q_coefficient']
    assert js % 3 == 0
    assert w % 9 == carry_residue(t, side, j0)
    assert wn % 9 == carry_residue(t, side, j0+1)
    terms = linear_conditions(t, residue, ix, affines, side, w, wn, j0, js)
    assert terms == row['linear_conditions']
    assert threshold(terms) == row['minimum_q']
    # Equality of affine expressions is checked by their values at q=0,1;
    # valid carry/digit ranges for every q>=qmin follow from nonnegative slopes.
    for q in [0, 1]:
        b, j = residue+MODULUS*q, j0+js*q
        raw = 225*(j+1)+30*t if side == 'low' else 225*(2*(b//5)-j-1)-30*t
        u, v = affines[ix]
        assert 3*(raw+w-b*wn) == u*b+v
    for q in [row['minimum_q'], row['minimum_q']+1, row['minimum_q']+1000000]:
        b, j = residue+MODULUS*q, j0+js*q
        assert square_carry(t, b, side, j) == w
        assert square_carry(t, b, side, j+1) == wn
        assert square_digit(t, b, side, j) == (affines[ix][0]*b+affines[ix][1])//27


def actual_collision(b, t):
    """Exact column arithmetic; returns a duplicate certificate, or None."""
    L, a = b//5, t*(b-1)//3-5
    seen = {}
    carry = 0
    for j in range(2*L-1):
        carry, digit = divmod(a*a*min(j+1, 2*L-1-j)+carry, b)
        location = {'power': 2, 'position_from_units': j}
        if digit in seen:
            return {'digit': digit, 'first': seen[digit], 'second': location}
        seen[digit] = location
    j = 2*L-1
    while carry:
        carry, digit = divmod(carry, b)
        location = {'power': 2, 'position_from_units': j}
        if digit in seen:
            return {'digit': digit, 'first': seen[digit], 'second': location}
        seen[digit] = location
        j += 1
    carry = 0
    def triangular(x):
        return x*(x-1)//2 if x >= 2 else 0
    for j in range(3*L-2):
        count = triangular(j+2)-3*triangular(j-L+2)+3*triangular(j-2*L+2)
        carry, digit = divmod(a**3*count+carry, b)
        location = {'power': 3, 'position_from_units': j}
        if digit in seen:
            return {'digit': digit, 'first': seen[digit], 'second': location}
        seen[digit] = location
    j = 3*L-2
    while carry:
        carry, digit = divmod(carry, b)
        location = {'power': 3, 'position_from_units': j}
        if digit in seen:
            return {'digit': digit, 'first': seen[digit], 'second': location}
        seen[digit] = location
        j += 1
    return None


def main(args):
    start = time.monotonic()
    certificates, missing, finite = [], [], []
    for t, first in [(1, 70), (2, 40)]:
        for residue in range(first, MODULUS, 90):
            row = make_certificate(t, residue, args.max_cube_index)
            if row is None:
                missing.append([t, residue])
                continue
            verify_certificate(row)
            certificates.append(row)
            if args.finite_gap:
                qstart = max(0, (2001-residue+MODULUS-1)//MODULUS)
                for q in range(qstart, row['minimum_q']):
                    b = residue+MODULUS*q
                    collision = actual_collision(b, t)
                    assert collision is not None, (b, t)
                    finite.append({'base': b, 'template': t, 'collision': collision})
    result = {'modulus': MODULUS, 'max_cube_position': args.max_cube_index,
              'certificates': certificates, 'uncovered_classes': missing,
              'finite_gap_requested': args.finite_gap, 'finite_gap_checks': finite,
              'largest_certificate_threshold': max((r['minimum_base'] for r in certificates), default=None),
              'elapsed_seconds': time.monotonic()-start}
    with open(args.output, 'w') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['certificates', 'finite_gap_checks']}, indent=2))
    print('certificate_count', len(certificates), 'finite_gap_count', len(finite))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-cube-index', type=int, default=8)
    parser.add_argument('--finite-gap', action='store_true')
    parser.add_argument('--output', default='results/repdigit-residuals-certificates.json')
    main(parser.parse_args())
