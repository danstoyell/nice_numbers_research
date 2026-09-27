#!/usr/bin/env python3
"""Rational affine certificates for a repeated cube digit in the 5/6 family."""
import json
import math
from fractions import Fraction as F
from pathlib import Path


def lower_coefficient(j):
    return -(F(5, 6)+5)**3 if j == 0 else -F(125, 12)*(6*j*j+24*j+19)


def upper_coefficient(j):
    return F(125, 12)*(-6*j*j+24*j-19)


def certificates():
    rows = []
    max_ratio = F(0)
    max_low_threshold = F(0)
    for residue in range(25, 216, 36):
        carry = F(0)
        lower_digits = []
        for j in range(8):
            value = lower_coefficient(j)+carry
            q, denominator = value.numerator, value.denominator
            k = -q*pow(residue, -1, denominator) % denominator
            if k == 0 and q < 0:
                k = denominator
            slope = F(k, denominator)
            assert slope > 0 and slope <= 1 and value < 0
            max_low_threshold = max(max_low_threshold, -value/slope)
            lower_digits.append((slope, value))
            carry = -slope
        gamma = F(5, 6)**3
        upper_digits = []
        for j in range(11):
            value = residue*gamma+upper_coefficient(j+1)
            fractional = value-math.floor(value)
            if fractional:
                margin = min(fractional, 1-fractional)
                max_ratio = max(max_ratio, abs(upper_coefficient(j+2))/margin)
            gamma_next = (fractional if fractional or upper_coefficient(j+2)>0
                          else F(1))
            upper_digits.append((gamma, upper_coefficient(j+1)-gamma_next))
            gamma = gamma_next
        assert lower_digits[7] == upper_digits[10]
        slope, intercept = lower_digits[7]
        rows.append({'base_residue_mod_216': residue,
                     'slope': str(slope), 'intercept': str(intercept),
                     'low_digit_index': 7, 'high_digit_index': 10})
    return rows, max_ratio, max_low_threshold


def numerical_check(rows):
    cases = 0
    by_residue = {r['base_residue_mod_216']: r for r in rows}
    for b in range(1_000_000, 1_100_001):
        if b % 180 != 25:
            continue
        m, L = b-1, b//5
        a = 5*m//6-5
        assert 6*a == 5*m-30
        row = by_residue[b % 216]
        prediction = F(row['slope'])*b+F(row['intercept'])
        assert prediction.denominator == 1
        modulus = b**8
        root_suffix = -a*pow(m, -1, modulus) % modulus
        actual_low = pow(root_suffix, 3, modulus)//b**7
        prefix, remainder = divmod(b**11*a**3, m**3)
        assert remainder > 0 and L >= 15
        actual_high = prefix % b
        assert actual_low == actual_high == prediction
        cases += 1
    return cases


def main():
    rows, ratio, threshold = certificates()
    assert ratio == 130050
    assert threshold < 1_000_000
    result = {'family': 'b=25 mod180, a=5*(b-1)/6-5, L=b/5',
              'proved_min_base': 1_000_000,
              'certificates': rows,
              'max_abs_next_coefficient_over_prefix_margin': str(ratio),
              'max_lower_digit_nonnegative_threshold': str(threshold),
              'exact_numerical_validation_cases': numerical_check(rows),
              'scope': 'Affine equality certificate plus analytic remainder bounds in the note; no search of arbitrary roots'}
    Path('results/repdigit-five-sixths.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
