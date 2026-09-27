#!/usr/bin/env python3
"""Exact reference-model counts and positivity scales; not an existence proof."""
import argparse
import json
import math
from pathlib import Path

from obstructions import length_interval


def leading_legal_avoidance_sum(b, omitted_count):
    """Sum, over omitted alphabets J of the requested size, of legal words."""
    j = omitted_count
    remaining = b-j
    without_zero = (math.comb(b-1, j-1) * remaining**b if j else 0)
    with_zero = (math.comb(b-1, j) * max(remaining-1, 0)**2 * remaining**(b-2)
                 if j < b else 0)
    return without_zero + with_zero


def reference_inclusion_exclusion(b):
    legal_words = (b-1)**2*b**(b-2)
    permutations = (b-2)*math.factorial(b-1)
    partial = 0
    first_positive_odd = None
    absolute_sum = 0
    for j in range(b+1):
        term = leading_legal_avoidance_sum(b, j)
        partial += (-1)**j*term
        absolute_sum += term
        if j % 2 and partial > 0 and first_positive_odd is None:
            first_positive_odd = j
    assert partial == permutations
    return {"base": b,
            "first_positive_odd_bonferroni_depth": first_positive_odd,
            "depth_fraction": first_positive_odd/b,
            "log10_reference_pandigital_probability":
                (math.log(permutations)-math.log(legal_words))/math.log(10),
            "log10_max_uniform_relative_avoidance_error_sufficient":
                (math.log(permutations)-math.log(absolute_sum))/math.log(10),
            "log10_max_uniform_absolute_probability_error_sufficient":
                (math.log(permutations)-math.log(legal_words)-b*math.log(2))/math.log(10)}


def corrected_reference_expectation(b):
    if b % 5 == 1 or b % 4 == 3:
        return {"base": b, "excluded_by_known_conditions": True}
    lo, hi = length_interval(b)
    modulus = b*(b-1)
    target = b*(b-1)//2
    roots = [s for s in range(b-1) if (s*s*(s+1)-target) % (b-1) == 0]
    zero_count = nonzero_count = 0
    for r in range(b):
        square_last = r*r % b
        cube_last = r*r*r % b
        if square_last == cube_last:
            continue
        for s in roots:
            residue = r + b*((s-r) % (b-1))
            count = ((hi-1-residue)//modulus - (lo-1-residue)//modulus)
            if square_last == 0 or cube_last == 0:
                zero_count += count
            else:
                nonzero_count += count
    numerator = zero_count*math.factorial(b-2) + nonzero_count*(b-4)*math.factorial(b-3)
    denominator = (b-1)*b**(b-4)
    log_expected = math.log(numerator)-math.log(denominator) if numerator else None
    return {"base": b, "candidate_interval_size": str(hi-lo),
            "exact_filtered_candidates_one_last_digit_zero": str(zero_count),
            "exact_filtered_candidates_both_last_digits_nonzero": str(nonzero_count),
            "log10_corrected_reference_expected_count":
                log_expected/math.log(10) if log_expected is not None else None,
            "log10_uncorrected_reference_expected_count":
                (math.log(hi-lo)+math.lgamma(b+1)-b*math.log(b))/math.log(10),
            "warning": "Expectation in a conditional random-string model; actual solution count unknown"}


def exhaustive_small_identity(b=4):
    # This validates the exact inclusion-exclusion coefficient, using all words.
    from itertools import product
    legal_count = nice_count = 0
    for word in product(range(b), repeat=b):
        # Two fixed, distinct positions stand for the two leading digits.
        if word[0] == 0 or word[1] == 0:
            continue
        legal_count += 1
        nice_count += len(set(word)) == b
    assert legal_count == (b-1)**2*b**(b-2)
    assert nice_count == (b-2)*math.factorial(b-1)
    return {"base": b, "legal_words": legal_count, "pandigital_words": nice_count}


def marginal_counterexample(b=4):
    from itertools import product
    target = (b*(b-1)//2 + 1) % b
    words = [tuple(prefix) + ((target-sum(prefix)) % b,)
             for prefix in product(range(b), repeat=b-1)]
    assert not any(len(set(word)) == b for word in words)
    for omitted_slot in range(b):
        projections = [word[:omitted_slot]+word[omitted_slot+1:] for word in words]
        assert len(set(projections)) == b**(b-1)
    return {"base": b, "words": len(words), "uniform_marginal_order": b-1,
            "pandigital_words": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/existence-counting.json"))
    args = parser.parse_args()
    result = {
        "scope": "Exact counting identities and explicitly hypothetical random-string expectations",
        "leading_legal_reference_exhaustion": exhaustive_small_identity(),
        "high_order_uniformity_counterexample": marginal_counterexample(),
        "inclusion_exclusion_scales":
            [reference_inclusion_exclusion(b) for b in [10, 32, 64, 100, 128, 256, 512, 1000]],
        "corrected_reference_expectations":
            [corrected_reference_expectation(b) for b in [10, 54, 57, 64, 100, 120, 125, 128, 150, 200, 512]],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    for row in result["inclusion_exclusion_scales"]:
        print(row)
    for row in result["corrected_reference_expectations"]:
        print({k: v for k, v in row.items() if k in
               ("base", "log10_corrected_reference_expected_count",
                "log10_uncorrected_reference_expected_count", "excluded_by_known_conditions")})
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
