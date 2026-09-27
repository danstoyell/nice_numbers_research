#!/usr/bin/env python3
"""Where would a second nice number be, and what would it cost to reach it?

For every admissible base, computes (exactly, with Python integers):

* N: the exact candidate interval size (scripts/verify.py intervals);
* F: candidates passing the digit-sum and distinct-last-digit filters (CRT);
* E: the expected number of nice numbers in the conditional random-digit
  model already used in research/existence-counting.md (reimplemented here
  and cross-checked against that note's saved values);
* W_edge: an idealized count of full checks for a search that exploits every
  edge digit (low and high digits of both powers), as the public client's
  MSD/LSD/cross-end filters approximately do;
* cumulative E from the public frontier upward, the Poisson probability of at
  least one solution, and the years needed at the public network's current
  nice-only throughput.

All expectations are heuristic. Nothing here is evidence about any specific
unsearched candidate.
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals  # noqa: E402

# Public coverage snapshot (data.nicenumbers.net/bases, fetched 2026-09-26):
# every base <= 54 is complete in at least nice-only mode; base 57 is 12.44%
# searched; 55, 56 are excluded by congruences.
FRONTIER_FRACTION_DONE = {57: 0.1244}
COMPLETE_THROUGH = 54
# Public nice-only throughput, range of n per day: sum of niceonly rows on
# 2026-09-26 in cache_search_rate_daily (one fleet account, 4.99e16/day).
RANGE_PER_DAY = 5.0e16


def digit_sum_roots(b):
    m = b - 1
    target = b * (b - 1) // 2 % m
    return [s for s in range(m) if (s * s * (s + 1) - target) % m == 0]


def filtered_counts(b, lo, hi):
    """Return (zero_last, nonzero_last) filtered candidate counts."""
    m, modulus = b - 1, b * (b - 1)
    roots = digit_sum_roots(b)
    zero = nonzero = 0
    for r in range(b):
        sq, cu = r * r % b, r ** 3 % b
        if sq == cu:
            continue
        for s in roots:
            x = (r + b * ((s - r) % m)) % modulus
            first = lo + (x - lo) % modulus
            count = (hi - first) // modulus + 1 if first <= hi else 0
            if sq == 0 or cu == 0:
                zero += count
            else:
                nonzero += count
    return zero, nonzero


def log_expected(b, zero, nonzero):
    """Natural log of E in the conditional model of existence-counting.md.

    A filtered candidate's remaining b-2 digits are uniform among legal
    strings with the right digit sum: (b-1)*b^(b-4) of them. Favorable
    strings: (b-2)! if a fixed last digit is 0, else (b-4)*(b-3)! (zero
    must avoid both leading positions).
    """
    lg = math.lgamma
    terms = []
    if zero:
        terms.append(math.log(zero) + lg(b - 1))
    if nonzero and b > 4:
        terms.append(math.log(nonzero) + math.log(b - 4) + lg(b - 2))
    if not terms:
        return None
    top = max(terms)
    log_num = top + math.log(sum(math.exp(t - top) for t in terms))
    return log_num - math.log(b - 1) - (b - 4) * math.log(b)


def log_edge_survival(b, edges):
    """log P(edges uniform digits are distinct), excluding the last-digit
    pair already enforced by the filter."""
    return sum(math.log1p(-i / b) for i in range(2, edges))


def row_for(b):
    intervals = candidate_intervals(b)
    if not intervals or b % 4 == 3:
        return None
    iv, = intervals
    lo, hi = iv["lo"], iv["hi"]
    n_count = hi - lo + 1
    zero, nonzero = filtered_counts(b, lo, hi)
    filt = zero + nonzero
    le = log_expected(b, zero, nonzero)
    if le is None:
        return None
    root_digits = len(str_base_len(hi, b))
    # Edge digits reachable from both ends: about one high and one low output
    # digit of each power per input digit; subtract two for carry ambiguity.
    edges = max(2, 2 * root_digits - 2)
    log_w_edge = math.log(filt) + log_edge_survival(b, edges)
    return {
        "base": b,
        "square_digits": iv["square_digits"], "cube_digits": iv["cube_digits"],
        "root_digits": root_digits,
        "interval_count": n_count,
        "log10_interval_count": math.log10(n_count),
        "digit_sum_classes": len(digit_sum_roots(b)),
        "filtered_count": filt,
        "log10_filtered_count": math.log10(filt) if filt else None,
        "expected_nice": math.exp(le),
        "log10_expected_nice": le / math.log(10),
        "edge_digits_used": edges,
        "log10_ideal_edge_checks": log_w_edge / math.log(10),
        "log10_edge_checks_per_expected_solution": (log_w_edge - le) / math.log(10),
    }


def str_base_len(n, b):
    out = []
    while n:
        n, d = divmod(n, b)
        out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-base", type=int, default=400)
    ap.add_argument("--output", default=str(ROOT / "critique/results/reachability.json"))
    args = ap.parse_args()

    rows = [r for b in range(10, args.max_base + 1) if (r := row_for(b))]

    # Cross-check against research/existence-counting.md saved values.
    saved = json.loads((ROOT / "results/existence-counting.json").read_text())
    checks = []
    for rec in saved["corrected_reference_expectations"]:
        if rec.get("excluded_by_known_conditions"):
            continue
        mine = next((r for r in rows if r["base"] == rec["base"]), None)
        if mine is None:
            continue
        checks.append({"base": rec["base"],
                       "saved_log10": rec["log10_corrected_reference_expected_count"],
                       "this_log10": mine["log10_expected_nice"]})
        assert abs(checks[-1]["saved_log10"] - checks[-1]["this_log10"]) < 0.01, checks[-1]

    # Cumulative quantities from the public frontier upward.
    cum_e, cum_log_range = 0.0, None
    for r in rows:
        b = r["base"]
        done = 1.0 if b <= COMPLETE_THROUGH else FRONTIER_FRACTION_DONE.get(b, 0.0)
        r["public_fraction_searched"] = done
        remaining = 1.0 - done
        cum_e += r["expected_nice"] * remaining
        if remaining > 0:
            term = math.log(r["interval_count"]) + math.log(remaining)
            cum_log_range = term if cum_log_range is None else (
                max(cum_log_range, term) + math.log1p(math.exp(-abs(cum_log_range - term))))
        r["cumulative_unsearched_expected_through_base"] = cum_e
        r["p_at_least_one_unsearched_through_base"] = -math.expm1(-cum_e)
        r["log10_years_at_current_public_rate_through_base"] = (
            None if cum_log_range is None else
            (cum_log_range - math.log(RANGE_PER_DAY * 365.25)) / math.log(10))

    searched_e = sum(r["expected_nice"] * r["public_fraction_searched"]
                     for r in rows if r["base"] != 10)
    first_half = next((r["base"] for r in rows
                       if r["cumulative_unsearched_expected_through_base"] >= math.log(2)), None)
    first_one = next((r["base"] for r in rows if r["expected_nice"] >= 1), None)
    report = {
        "scope": "Heuristic expectations in the conditional random-digit model; not evidence of existence",
        "assumptions": {
            "public_complete_through_base": COMPLETE_THROUGH,
            "public_partial": FRONTIER_FRACTION_DONE,
            "public_niceonly_range_per_day": RANGE_PER_DAY,
            "edge_model": "uniform digits; 2*(root digits)-2 edge digits must be distinct",
        },
        "cross_check_with_existence_counting": checks,
        "expected_in_base_10": next(r["expected_nice"] for r in rows if r["base"] == 10),
        "expected_in_searched_bases_excluding_10": searched_e,
        "first_base_with_expected_at_least_1": first_one,
        "first_base_where_unsearched_cumulative_reaches_50_percent": first_half,
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(report, indent=1, default=str) + "\n")

    print(f"E(base 10) = {report['expected_in_base_10']:.4f}")
    print(f"E(searched bases 12..57-partial) = {searched_e:.5f}")
    print(f"first base with E>=1: {first_one}; unsearched cumulative reaches 50% at base {first_half}")
    print("base  log10N  log10F  E            cumE(unsearched)  P>=1     log10(yrs)  log10(edge checks/solution)")
    for r in rows:
        if r["base"] in (10, 12, 20, 30, 40, 45, 50, 54, 57, 58, 60, 62, 64, 65, 70, 80, 90,
                         100, 110, 120, 125, 128, 130, 140, 150, 160, 180, 200, 250, 300, 400):
            print(f"{r['base']:4d}  {r['log10_interval_count']:6.2f}  {r['log10_filtered_count']:6.2f}  "
                  f"{r['expected_nice']:.3e}   {r['cumulative_unsearched_expected_through_base']:.3e}"
                  f"        {r['p_at_least_one_unsearched_through_base']:.4f}   "
                  f"{(r["log10_years_at_current_public_rate_through_base"] or float("nan")):8.2f}   "
                  f"{r['log10_edge_checks_per_expected_solution']:.1f}")


if __name__ == "__main__":
    main()
