#!/usr/bin/env python3
"""Exact conditional Monte Carlo from the random-digit model, given deficiency r.

Model (the critique's M1 plus the digit-sum class):
  * n uniform on the checked interval(s) of base b, so the top 2 and bottom 3
    digits of n^2 and n^3 are exact (10 "edge" positions);
  * the other m = b - 10 "middle" digits i.i.d. uniform on 0..b-1;
  * conditioned on the whole b-digit string having exactly b - r distinct
    values, and on digitsum(n^2) + digitsum(n^3) = n^2 + n^3 (mod b-1).

Sampling is exact, not approximate:
  1. n is drawn uniformly and accepted with probability w(u)/max w, where u is
     the number of distinct edge values and w(u) = P(deficiency r | edges) is
     the closed-form count of valid middles (depends on u only);
  2. the middle is drawn uniformly among valid middles: choose the r missing
     values among the values absent from the edges, choose how many middle
     slots reuse edge values (weights C(m,j) u^(m-j) S(j,v)), and draw a
     uniform surjection of the remaining slots onto the new values;
  3. the digit-sum congruence is imposed by rejection. The acceptance rate
     times (b-1) is the exact digit-sum coupling factor for this base.
Each accepted sample also records whether the *separate* congruences
digitsum(n^2) = n^2 and digitsum(n^3) = n^3 (mod b-1) hold, so the stricter
model can be analysed on that subset.

Usage: python3 attack/p3-obstruction/scripts/model_mc.py --per-base 3000 --deficiency 2
"""
import argparse
import math
import pickle
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASES, HERE, intervals, shape  # noqa: E402

T, K = 2, 3   # exact top and bottom digits per power


def stirling2(j, v):
    s = 0
    for i in range(v + 1):
        s += (-1) ** i * math.comb(v, i) * (v - i) ** j
    return s // math.factorial(v)


def valid_middles(b, m, u, r):
    """Number of middle strings giving exactly b-r distinct values, edges with u distinct."""
    v = b - r - u
    if v < 0 or v > m:
        return 0, {}
    jw = {}
    for j in range(v, m + 1):
        w = math.comb(m, j) * u ** (m - j) * stirling2(j, v)
        if w:
            jw[j] = w
    return math.comb(b - u, v) * math.factorial(v) * sum(jw.values()), jw


def to_digits(x, b, width):
    out = [0] * width
    for i in range(width - 1, -1, -1):
        x, out[i] = divmod(x, b)
    assert x == 0
    return out


def edge_digits(n, b, s, c):
    sq, cu = n * n, n ** 3
    top2 = to_digits(sq // b ** (s - T), b, T)
    top3 = to_digits(cu // b ** (c - T), b, T)
    bot2 = to_digits(sq % b ** K, b, K)
    bot3 = to_digits(cu % b ** K, b, K)
    return top2, bot2, top3, bot3


def random_surjection(rng, j, vals):
    """Uniform surjection from j slots onto the list vals (len v, j - v <= 2)."""
    v = len(vals)
    blocks = [[i] for i in range(j)]
    extra = j - v
    slots = list(range(j))
    rng.shuffle(slots)
    if extra == 1:
        blocks = [slots[:2]] + [[x] for x in slots[2:]]
    elif extra == 2:
        n_triple, n_pairs = math.comb(j, 3), 3 * math.comb(j, 4)
        if rng.random() * (n_triple + n_pairs) < n_triple:
            blocks = [slots[:3]] + [[x] for x in slots[3:]]
        else:
            blocks = [slots[:2], slots[2:4]] + [[x] for x in slots[4:]]
    elif extra == 0:
        blocks = [[x] for x in slots]
    else:
        raise ValueError(extra)
    assert len(blocks) == v
    perm = list(vals)
    rng.shuffle(perm)
    out = [None] * j
    for blk, val in zip(blocks, perm):
        for x in blk:
            out[x] = val
    return out


def sample_base(b, r, want, rng):
    s, c = shape(b)
    m = b - 2 * T - 2 * K
    ivs = intervals(b)
    tot_w = sum(w for _, _, w in ivs)
    cum = []
    acc = 0
    for lo, hi, w in ivs:
        acc += w
        cum.append(acc)
    wu, ju = {}, {}
    for u in range(1, 2 * T + 2 * K + 1):
        wu[u], ju[u] = valid_middles(b, m, u, r)
    wmax = max(wu.values())
    sq_mid = list(range(T, s - K))
    cu_mid = list(range(T, c - K))
    samples = []
    drawn = accepted_n = 0
    while len(samples) < want:
        x = rng.randrange(tot_w)
        i = next(i for i, cv in enumerate(cum) if x < cv)
        lo, hi, _ = ivs[i]
        n = rng.randint(lo, hi)
        top2, bot2, top3, bot3 = edge_digits(n, b, s, c)
        edge_vals = set(top2 + bot2 + top3 + bot3)
        u = len(edge_vals)
        if wu[u] == 0 or rng.random() * wmax >= wu[u]:
            continue
        accepted_n += 1
        absent = [d for d in range(b) if d not in edge_vals]
        missing = rng.sample(absent, r)
        new_vals = [d for d in absent if d not in missing]
        jw = ju[u]
        pick = rng.random() * sum(jw.values())
        for j, w in jw.items():
            pick -= w
            if pick < 0:
                break
        slots = list(range(m))
        rng.shuffle(slots)
        reuse, fresh = slots[:m - j], slots[m - j:]
        mid = [None] * m
        ev = sorted(edge_vals)
        for p in reuse:
            mid[p] = rng.choice(ev)
        for p, val in zip(fresh, random_surjection(rng, j, new_vals)):
            mid[p] = val
        sq_d = top2 + mid[:len(sq_mid)] + bot2
        cu_d = top3 + mid[len(sq_mid):] + bot3
        assert len(sq_d) == s and len(cu_d) == c and len(set(sq_d + cu_d)) == b - r
        drawn += 1
        ssq, scu = sum(sq_d), sum(cu_d)
        if (ssq + scu - n * n - n ** 3) % (b - 1):
            continue
        sep = (ssq - n * n) % (b - 1) == 0
        samples.append((n, bytes(sq_d), bytes(cu_d), sep))
    return {"base": b, "s": s, "c": c, "samples": samples, "middle_draws": drawn,
            "coupling_factor": len(samples) * (b - 1) / drawn}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-base", type=int, default=3000)
    ap.add_argument("--deficiency", type=int, default=2)
    ap.add_argument("--seed", type=int, default=49)
    ap.add_argument("--bases", type=int, nargs="*", default=BASES)
    ap.add_argument("--output", default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    out = {}
    for b in args.bases:
        t0 = time.time()
        res = sample_base(b, args.deficiency, args.per_base, rng)
        out[b] = res
        print(f"base {b}: {len(res['samples'])} samples from {res['middle_draws']} conditional draws, "
              f"digit-sum coupling factor {res['coupling_factor']:.3f}, "
              f"separate-congruence subset {sum(x[3] for x in res['samples'])}, {time.time()-t0:.1f}s", flush=True)
    path = args.output or HERE / f"results/model_mc_def{args.deficiency}.pkl"
    with open(path, "wb") as f:
        pickle.dump({"deficiency": args.deficiency, "seed": args.seed, "per_base": args.per_base, "bases": out}, f)


if __name__ == "__main__":
    main()
