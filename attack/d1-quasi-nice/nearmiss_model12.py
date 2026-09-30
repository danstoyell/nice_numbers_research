#!/usr/bin/env python3
"""Model expectation of deficiency-0/1/2 counts for the (1,2) problem under M1(A,J):
n exact, n^2's top A and bottom J digits exact, the other m = c-A-J digits of n^2 uniform,
conditioned on the digit-sum identity digitsum(n) + digitsum(n^2) == n + n^2 (mod b-1)
("coupled"), and also without that conditioning ("uncoupled").

For each n the known multiset E (s digits of n plus the 2 edge blocks of n^2) is fixed, and
the middle multiplicities a_v are summed exactly by a DP over the values v = 0..b-1 with
state (missing values <= 2, excess digits <= 2, digit sum mod b-1); a value absent from E
contributes a_v in {0 (missing), 1, 2, 3}, a value present in E contributes a_v in {0, 1, 2};
each sequence has weight m!/prod(a_v!) / b^m. Deficiency r needs missing = r and
excess = r - kappa, kappa = |E| - #distinct(E).

Usage: python3 nearmiss_model12.py 17 18 20 21 24 --samples 1000000 [--A 2 --J 3]
       (bases with at most --exhaustive-max candidates are done exhaustively)
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from brute import band  # noqa: E402
from model12 import n_digits, sq_digits  # noqa: E402


def dp_probs(n, b, s, c, A, J):
    """Returns (coupled, uncoupled) arrays of shape (len(n), 3): P(deficiency = 0, 1, 2)."""
    M = b - 1
    Dn = n_digits(n, b, s)
    Dq = sq_digits(n, b, c)
    E = np.concatenate([Dn, Dq[:, :J], Dq[:, c - A:]], axis=1)
    m = c - A - J
    cnt = np.zeros((len(n), b), dtype=np.int64)
    for i in range(E.shape[1]):
        np.add.at(cnt, (np.arange(len(n)), E[:, i]), 1)
    u = (cnt > 0).sum(axis=1)
    kappa = E.shape[1] - u
    out_c = np.zeros((len(n), 3))
    out_u = np.zeros((len(n), 3))
    keep = np.nonzero(kappa <= 2)[0]
    if len(keep) == 0:
        return out_c, out_u
    cnt, kappa = cnt[keep], kappa[keep]
    sq_true = (n[keep] % M) ** 2 % M  # n^2 mod (b-1)
    sigma = ((n[keep] % M) + sq_true - E[keep].sum(axis=1)) % M
    S = len(keep)
    st = np.zeros((S, 3, 3, M))
    st[:, 0, 0, 0] = 1.0
    for v in range(b):
        isW = (cnt[:, v] == 0)[:, None, None, None]
        newW = np.zeros_like(st)
        newV = np.zeros_like(st)
        # absent value: a = 0 (missing), 1, 2 (excess 1), 3 (excess 2)
        newW[:, 1:, :, :] += st[:, :2, :, :]
        newW += np.roll(st, v % M, axis=3)
        newW[:, :, 1:, :] += 0.5 * np.roll(st[:, :, :2, :], (2 * v) % M, axis=3)
        newW[:, :, 2:, :] += (1 / 6) * np.roll(st[:, :, :1, :], (3 * v) % M, axis=3)
        # present value: a = 0, 1 (excess 1), 2 (excess 2)
        newV += st
        newV[:, :, 1:, :] += np.roll(st[:, :, :2, :], v % M, axis=3)
        newV[:, :, 2:, :] += 0.5 * np.roll(st[:, :, :1, :], (2 * v) % M, axis=3)
        st = np.where(isW, newW, newV)
    logw = math.lgamma(m + 1) - m * math.log(b)
    eps = float(b) ** (-m)
    q = (1 + eps * ((M) * (sigma == 0) - 1)) / M  # P(m uniform digits sum == sigma mod M)
    idx = np.arange(S)
    for r in range(3):
        e = r - kappa
        okk = e >= 0
        ee = np.clip(e, 0, 2)
        coup = st[idx, r, ee, sigma] * okk
        unc = st[idx, r, ee, :].sum(axis=1) * okk
        out_c[keep, r] = coup * math.exp(logw) / q
        out_u[keep, r] = unc * math.exp(logw)
    return out_c, out_u


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bases", type=int, nargs="+")
    ap.add_argument("--samples", type=int, default=1_000_000)
    ap.add_argument("--A", type=int, default=2)
    ap.add_argument("--J", type=int, default=3)
    ap.add_argument("--batch", type=int, default=100_000)
    ap.add_argument("--exhaustive-max", type=int, default=2_000_000)
    ap.add_argument("--seed", type=int, default=20260927)
    args = ap.parse_args()
    for b in args.bases:
        bd = band(b)
        if not bd:
            continue
        (s, c, lo, hi), = bd
        N = hi - lo + 1
        rng = np.random.default_rng(args.seed + 7 * b)
        exhaustive = N <= args.exhaustive_max
        tot_c, tot_u, sq_c = np.zeros(3), np.zeros(3), np.zeros(3)
        done = 0
        target = N if exhaustive else args.samples
        while done < target:
            k = min(args.batch, target - done)
            if exhaustive:
                n = np.arange(lo + done, lo + done + k, dtype=np.int64)
            else:
                n = lo + rng.integers(0, N, size=k, dtype=np.int64)
            pc, pu = dp_probs(n, b, s, c, args.A, args.J)
            tot_c += pc.sum(axis=0)
            tot_u += pu.sum(axis=0)
            sq_c += (pc * pc).sum(axis=0)
            done += k
        mean_c = tot_c / done
        se_c = np.sqrt(np.maximum(sq_c / done - mean_c ** 2, 0) / done) * N if not exhaustive else np.zeros(3)
        print(json.dumps({"b": b, "s": s, "c": c, "N": N, "A": args.A, "J": args.J,
                          "method": "exhaustive" if exhaustive else f"monte carlo {done} samples",
                          "coupled": list(mean_c * N), "coupled_se": list(se_c),
                          "uncoupled": list(tot_u / done * N)}), flush=True)


if __name__ == "__main__":
    main()
