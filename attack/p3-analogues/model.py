#!/usr/bin/env python3
"""Model expectations for k-nice counts.

M0  -- the critique's conditional random-digit model, computed by the existing
       code (critique/scripts/twice_nice.py: model_expectation). Exact rational.
       Conditions on the last digits of n^2, n^3 and the digit-sum class; the
       other k*b-2 digits are uniform legal strings.
M1e -- exact-edge variant (secondary, for interpretation only): for each n the
       top A digits of n^2 and n^3 and the bottom J digits are taken exactly;
       the k*b - 2A - 2J middle digits are uniform, conditioned on the digit-sum
       class (a factor b-1). Monte Carlo over n in the digit-sum classes.

Also: M0 mass of a partial coverage set (chunks of residues n mod b^J), used
when a base is not finished.

Usage: python3 model.py [--mc 400000]    # writes results/model.json
"""
import argparse
import json
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "critique" / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
from twice_nice import intervals_total_length, model_expectation  # noqa: E402


def roots(b, k):
    m = b - 1
    target = (k * b * (b - 1) // 2) % m
    return [s for s in range(m) if (s * s * (s + 1) - target) % m == 0]


def p_last(b, k, r):
    """M0 per-candidate probability for n = r (mod b) in a valid digit-sum class.
    Same formula as twice_nice.model_expectation."""
    rest = k * b - 2
    x, y = r * r % b, r ** 3 % b
    left = [k] * b
    left[x] -= 1
    left[y] -= 1
    if min(left) < 0:
        return Fraction(0)
    denom = 1
    for v in left:
        denom *= math.factorial(v)
    arrangements = Fraction(math.factorial(rest), denom)
    lead_ok = Fraction(math.comb(rest - 2, left[0]), math.comb(rest, left[0]))
    return arrangements * lead_ok / ((b - 1) * b ** (rest - 2))


def valid_class_count(b, k, lo, hi):
    m = b - 1
    tot = 0
    for s in roots(b, k):
        first = lo + (s - lo) % m
        tot += (hi - first) // m + 1 if first <= hi else 0
    return tot


def m0(b, k):
    ivs = intervals_total_length(b, k * b)
    if not ivs:
        return None
    (lo, hi, s, c), = ivs
    e, ncls = model_expectation(b, lo, hi, k)
    count = hi - lo + 1
    vc = valid_class_count(b, k, lo, hi)
    return {"base": b, "k": k, "lo": lo, "hi": hi, "square_digits": s, "cube_digits": c,
            "count": count, "digit_sum_classes": ncls, "valid_class_candidates": vc,
            "m0_expected": e, "p_per_candidate": e / count,
            "p_per_valid_candidate": e / vc if vc else 0.0}


def m0_partial(b, k, lo, hi, j, nchunks, a, chunk_ids):
    """M0 expectation over n in [lo, hi] whose residue mod b^j lies in the given chunks
    (chunk c = {i*a mod b^j : c*M/nchunks <= i < (c+1)*M/nchunks}), exactly as knice.c."""
    M = b ** j
    m = b - 1
    S = m * M
    inv = next(x for x in range(m) if (M % m) * x % m == 1 % m)
    pt = np.array([float(p_last(b, k, r)) for r in range(b)])
    total = 0.0
    for c in chunk_ids:
        i0, i1 = M * c // nchunks, M * (c + 1) // nchunks
        i = np.arange(i0, i1, dtype=np.int64)
        rho = (i * a) % M  # a < M <= 32^6, products < 2^63
        pr = pt[rho % b]
        for s in roots(b, k):
            diff = (s - rho % m) % m
            R = rho + M * ((diff * inv) % m)
            cnt = (hi - R) // S - (lo - 1 - R) // S
            total += float(np.sum(cnt * pr))
    return total


def digits_le(n, b):
    out = []
    while n:
        n, d = divmod(n, b)
        out.append(d)
    return out


def m1e(b, k, samples, top=2, bottom=3, seed=20260926):
    """Exact-edge model expectation by Monte Carlo; returns (mean, standard error)."""
    info = m0(b, k)
    lo, hi = info["lo"], info["hi"]
    rs = set(roots(b, k))
    rng = random.Random(seed + 1000 * b + k)
    mid = k * b - 2 * top - 2 * bottom
    assert mid > 0
    # log of mid! / prod (k - c_v)! / b^mid, times (b-1) for the digit-sum class
    logf = [math.lgamma(i + 1) for i in range(k * b + 1)]
    base_log = logf[mid] - mid * math.log(b) + math.log(b - 1)
    vals = []
    got = 0
    while got < samples:
        n = rng.randint(lo, hi)
        if n % (b - 1) not in rs:
            continue
        got += 1
        sq, cu = digits_le(n * n, b), digits_le(n ** 3, b)
        edge = sq[:bottom] + sq[-top:] + cu[:bottom] + cu[-top:]
        cnt = [0] * b
        for d in edge:
            cnt[d] += 1
        if max(cnt) > k:
            vals.append(0.0)
            continue
        lp = base_log - sum(logf[k - c] for c in cnt)
        vals.append(math.exp(lp))
    v = np.array(vals)
    vc = info["valid_class_candidates"]
    return float(v.mean() * vc), float(v.std(ddof=1) / math.sqrt(len(v)) * vc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mc", type=int, default=400000)
    ap.add_argument("--output", default=str(HERE / "results" / "model.json"))
    ap.add_argument("--extra", nargs="*", default=None,
                    help="only compute these k:b pairs and merge them into the existing output")
    args = ap.parse_args()
    rows = []
    if args.extra:
        old = json.loads(Path(args.output).read_text())
        pairs = [tuple(int(v) for v in x.split(":")) for x in args.extra]
        rows = [r for r in old["rows"] if (r["k"], r["base"]) not in pairs]
        plan = pairs
    else:
        plan = [(k, b) for k, bases in ((2, range(5, 28)), (3, range(5, 22))) for b in bases]
    for k, b in plan:
        if True:
            info = m0(b, k)
            if info is None:
                continue
            if info["m0_expected"] > 0 and k * b - 10 > 0:
                e1, se1 = m1e(b, k, args.mc)
                info["m1e_expected"], info["m1e_se"] = e1, se1
            for key in ("lo", "hi"):
                info[key] = str(info[key])
            rows.append(info)
            print(json.dumps({x: info.get(x) for x in ("k", "base", "count", "m0_expected", "p_per_candidate",
                                                       "m1e_expected", "m1e_se")}), flush=True)
    rows.sort(key=lambda r: (r["k"], r["base"]))
    Path(args.output).write_text(json.dumps({
        "m0": "critique/scripts/twice_nice.py model_expectation (exact rational, float)",
        "m1e": f"exact top-2/bottom-3 edges, uniform middle, digit-sum conditioned; MC {args.mc} samples per base",
        "rows": rows}, indent=1) + "\n")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# M2: M1e plus the two separate digit-sum congruences
#   digitsum(n^2) == n^2 and digitsum(n^3) == n^3 (mod b-1).
# M0/M1e impose only their sum. Given the edges, count the ways to fill the
# square's and cube's middle positions with the remaining multiset R such that
# the square's middle digit sum has the required class, via the generating
# function prod_v sum_a x^a y^(a v) / (a! (R_v - a)!), cyclic in y.
def split_ratio(b, R, m2, sigma):
    """(b-1) * #(fillings with square-middle sum == sigma) / #(all fillings)."""
    m = b - 1
    A = np.zeros((m2 + 1, m))
    A[0, 0] = 1.0
    for v in range(b):
        r = R[v]
        if r == 0:
            continue
        new = np.zeros_like(A)
        for a in range(r + 1):
            if a > m2:
                break
            coef = 1.0 / (math.factorial(a) * math.factorial(r - a))
            sh = np.zeros_like(A)
            sh[a:, :] = A[:m2 + 1 - a, :]
            new += coef * np.roll(sh, (a * v) % m, axis=1)
        A = new
    tot = A[m2].sum()
    return m * A[m2, sigma % m] / tot


def m2split(b, k, samples, top=2, bottom=3, seed=20260927):
    """Paired Monte Carlo: returns dict with M1e and M2 expectations and SEs."""
    info = m0(b, k)
    lo, hi = info["lo"], info["hi"]
    rs = set(roots(b, k))
    rng = random.Random(seed + 1000 * b + k)
    s_len, c_len = info["square_digits"], info["cube_digits"]
    mid = k * b - 2 * top - 2 * bottom
    m2 = s_len - top - bottom
    logf = [math.lgamma(i + 1) for i in range(k * b + 1)]
    base_log = logf[mid] - mid * math.log(b) + math.log(b - 1)
    v1, v2 = [], []
    got = 0
    while got < samples:
        n = rng.randint(lo, hi)
        if n % (b - 1) not in rs:
            continue
        got += 1
        sq, cu = digits_le(n * n, b), digits_le(n ** 3, b)
        e_sq = sq[:bottom] + sq[-top:]
        edge = e_sq + cu[:bottom] + cu[-top:]
        cnt = [0] * b
        for d in edge:
            cnt[d] += 1
        if max(cnt) > k:
            v1.append(0.0)
            v2.append(0.0)
            continue
        p1 = math.exp(base_log - sum(logf[k - c] for c in cnt))
        R = [k - c for c in cnt]
        sigma = (n * n - sum(e_sq)) % (b - 1)
        v1.append(p1)
        v2.append(p1 * split_ratio(b, R, m2, sigma))
    v1, v2 = np.array(v1), np.array(v2)
    vc = info["valid_class_candidates"]
    se = lambda v: float(v.std(ddof=1) / math.sqrt(len(v)) * vc)
    d = v2 - v1
    return {"m1e": float(v1.mean() * vc), "m1e_se": se(v1), "m2": float(v2.mean() * vc), "m2_se": se(v2),
            "m2_over_m1e": float(v2.mean() / v1.mean()), "diff_se_rel": float(d.std(ddof=1) / math.sqrt(len(d)) / v1.mean()),
            "samples": samples, "top": top, "bottom": bottom}
