#!/usr/bin/env python3
"""Near-miss calibration of the exact-edge model M1e at a given base.

Data: logs/nearmiss_k{k}_b{b}_j{J}_c{N}.log from nearmiss.c (all residues of the
covered chunks, filters off): exact histogram of D = sum_v |c_v - k| (digit-count
distance from the exact k-nice vector) by digit-sum offset delta.
Model: M1e (exact top-2 / bottom-3 digits of n^2 and n^3, uniform middle digits
conditioned on the digit-sum identity). For each sampled n the probability of
every count vector c is (b-1) * m!/b^m / prod_v (c_v - e_v)!, if
sum_v v c_v == n^2 + n^3 (mod b-1), else 0. The sum over vectors with
D = 2j is read off a generating function in (P, Q, y).

Usage: python3 nearmiss_model.py --k 3 --base 18 --j 5 --chunks 2000 [--samples 60000]
"""
import argparse
import itertools
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from model import digits_le  # noqa: E402
from run import interval, perm_a  # noqa: E402

JMAX = 3  # D = 0, 2, 4, 6


def dbin_probs(b, k, e, m, delta):
    """P(D = 2j | edges e, class offset delta) for j = 0..JMAX (uniform middle, m digits)."""
    mm = b - 1
    A = np.zeros((JMAX + 1, JMAX + 1, mm))
    A[0, 0, 0] = 1.0
    for v in range(b):
        base = k - e[v]
        new = np.zeros_like(A)
        for x in range(-JMAX, JMAX + 1):
            if base + x < 0:
                continue
            g = 1.0 / math.factorial(base + x)
            sh = np.zeros_like(A)
            if x >= 0:
                sh[x:, :, :] = A[:JMAX + 1 - x, :, :]
            else:
                sh[:, -x:, :] = A[:, :JMAX + 1 + x, :]
            new += g * np.roll(sh, (v * x) % mm, axis=2)
        A = new
    scale = math.exp(math.lgamma(m + 1) - m * math.log(b) + math.log(mm))
    return np.array([A[j, j, delta % mm] * scale for j in range(JMAX + 1)])


def brute_check():
    """Enumerate all middle strings for tiny cases and compare with dbin_probs."""
    rng = random.Random(5)
    for _ in range(8):
        b, k = rng.choice([(4, 2), (5, 2), (4, 3)])
        tot = k * b
        m = rng.randint(3, 6)
        edge = [rng.randrange(b) for _ in range(tot - m)]
        e = [edge.count(v) for v in range(b)]
        delta = rng.randrange(b - 1)
        want = np.zeros(JMAX + 1)
        for mid in itertools.product(range(b), repeat=m):
            c = e[:]
            for d in mid:
                c[d] += 1
            D = sum(abs(x - k) for x in c)
            cls = (sum(v * c[v] for v in range(b)) - k * b * (b - 1) // 2) % (b - 1)
            if cls == delta and D // 2 <= JMAX:
                want[D // 2] += (b - 1) / b ** m
        got = dbin_probs(b, k, e, m, delta)
        assert np.allclose(got, want, rtol=1e-9, atol=1e-15), (b, k, e, m, delta, got, want)
    print("dbin_probs matches brute force")


def parse(path, b):
    chunks, hist, inr, hits = [], np.zeros((b - 1, 8), dtype=np.int64), 0, []
    for line in open(path):
        if not line.startswith("C "):
            continue
        left, right = line.split("|")
        f = left.split()
        chunks.append(int(f[1]))
        hits += [int(x) for x in f[9:]]
        vals = [int(x) for x in right.split()]
        inr += vals[0]
        hist += np.array(vals[1:]).reshape(b - 1, 8)
    return sorted(chunks), hist, inr, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--base", type=int, required=True)
    ap.add_argument("--j", type=int, required=True)
    ap.add_argument("--chunks", type=int, required=True)
    ap.add_argument("--samples", type=int, default=60000)
    ap.add_argument("--top", type=int, default=2)
    ap.add_argument("--bottom", type=int, default=3)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        brute_check()
    k, b, J = args.k, args.base, args.j
    lo, hi, s, c = interval(b, k)
    log = HERE / "logs" / f"nearmiss_k{k}_b{b}_j{J}_c{args.chunks}.log"
    chunks, hist, inr, hits = parse(log, b)
    M, mm = b ** J, b - 1
    S = mm * M
    N0 = lo // S * S
    a = perm_a(b, J)
    inv = next(x for x in range(mm) if (M % mm) * x % mm == 1 % mm)
    rng = random.Random(1234 + b)
    top, bot = args.top, args.bottom
    mid = k * b - 2 * top - 2 * bot
    acc = np.zeros(JMAX + 1)
    acc2 = np.zeros(JMAX + 1)
    got = 0
    while got < args.samples:
        ci = rng.choice(chunks)
        i = rng.randrange(M * ci // args.chunks, M * (ci + 1) // args.chunks)
        rho = i * a % M
        sres = rng.randrange(mm)
        R = rho + M * (((sres - rho % mm) % mm) * inv % mm)
        n = N0 + R + S * rng.randrange((hi - N0) // S + 1)
        if not lo <= n <= hi:
            continue
        got += 1
        sq, cu = digits_le(n * n, b), digits_le(n ** 3, b)
        edge = sq[:bot] + sq[-top:] + cu[:bot] + cu[-top:]
        e = [edge.count(v) for v in range(b)]
        delta = (n * n * (n + 1) - k * b * (b - 1) // 2) % mm
        pr = dbin_probs(b, k, e, mid, delta)
        acc += pr
        acc2 += pr ** 2
    mean = acc / got
    se = np.sqrt(np.maximum(acc2 / got - mean ** 2, 0) / got)
    exp = mean * inr
    obs = [int(hist[:, j].sum()) for j in range(JMAX + 1)]
    out = {"k": k, "base": b, "J": J, "chunks_covered": len(chunks), "chunks_total": args.chunks,
           "candidates_in_range": inr, "edges": [top, bot], "samples": got, "bins": []}
    for j in range(JMAX + 1):
        o, ex, sex = obs[j], float(exp[j]), float(se[j] * inr)
        out["bins"].append({"D": 2 * j, "observed": o, "m1e_expected": ex, "m1e_mc_se": sex,
                            "ratio": o / ex if ex else None,
                            "z_poisson": (o - ex) / math.sqrt(ex) if ex else None})
        print(json.dumps(out["bins"][-1]))
    out["exact_hits_in_subset"] = sorted(hits)
    res = HERE / "results" / "nearmiss.json"
    allr = json.loads(res.read_text()) if res.exists() else {}
    allr[f"k{k}_b{b}_top{top}_bot{bot}"] = out
    res.write_text(json.dumps(allr, indent=1) + "\n")


if __name__ == "__main__":
    main()
