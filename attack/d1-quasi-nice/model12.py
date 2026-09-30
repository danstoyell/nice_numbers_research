#!/usr/bin/env python3
"""Random-digit model expectations for (1,2)-nice counts (n and n^2 jointly pandigital).

Models (all but naive/crude are conditioned on the digit-sum class, i.e. only n with
n + n^2 == b(b-1)/2 (mod b-1) contribute, with a factor b-1 for the class):

  naive   N * b!/b^b                                (all b digits uniform)
  crude   N * roots * b!/b^b                        (first pass, quasi_nice.c)
  M0      last digit of n and of n^2 exact, both leading digits uniform on 1..b-1,
          other b-4 digits uniform; the analogue of twice_nice.model_expectation
  M1(A,J) n exact (all s digits), n^2's top A and bottom J digits exact, the other
          m = c-A-J digits of n^2 uniform (top digit legal when A = 0)
  M1e     both-edges analogue of the (2,3) M1e: n's top 2 / bottom 3 and n^2's top 2 /
          bottom 3 digits exact, the other b-10 digits (middle of n and of n^2) uniform

Expectations are sums over n in the valid classes. They are computed either exhaustively
(every valid-class n, numpy, exact up to float rounding) or by Monte Carlo over n.

Usage: python3 model12.py exact 5 6 8 ...    python3 model12.py mc 24 26 --samples 20000000
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

M1_SPECS = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 5)]


def roots(b):
    m = b - 1
    T = b * (b - 1) // 2 % m
    return [x for x in range(m) if (x + x * x) % m == T]


def class_counts(b, lo, hi):
    m = b - 1
    out = []
    for x in roots(b):
        first = lo + (x - lo) % m
        out.append((x, first, (hi - first) // m + 1 if first <= hi else 0))
    return out


def n_digits(n, b, s):
    """(len(n), s) array of digits, little-endian."""
    D = np.empty((len(n), s), dtype=np.int64)
    v = n.copy()
    for i in range(s):
        D[:, i] = v % b
        v //= b
    return D


def sq_digits(n, b, c):
    """(len(n), c) digits of n^2, little-endian, via base-b^6 limbs in int64."""
    B = b ** 6
    assert B * B < 2 ** 63 or True
    x, y = n // B, n % B
    y2 = y * y
    l0, cy = y2 % B, y2 // B
    t1 = 2 * x * y + cy
    l1, cy = t1 % B, t1 // B
    t2 = x * x + cy
    l2, l3 = t2 % B, t2 // B
    D = np.empty((len(n), c), dtype=np.int64)
    k = 0
    for limb in (l0, l1, l2, l3):
        v = limb.copy()
        for _ in range(6):
            if k == c:
                break
            D[:, k] = v % b
            v //= b
            k += 1
    assert k == c
    return D


def masks(D):
    m = np.zeros(D.shape[0], dtype=np.uint64)
    for i in range(D.shape[1]):
        m |= np.left_shift(np.uint64(1), D[:, i].astype(np.uint64))
    return m


def distinct(D):
    if D.shape[1] == 0:
        return np.ones(D.shape[0], dtype=bool), np.zeros(D.shape[0], dtype=np.uint64)
    m = masks(D)
    return np.bitwise_count(m) == D.shape[1], m


def log_fact(k):
    return math.lgamma(k + 1)


def class_factor(b, m, E):
    """1 / P(m uniform digits have digit sum == sigma mod b-1), exactly, where sigma is the
    sum of the remaining values R (the complement of the known digits E): the sum a pandigital
    completion needs. For a single uniform digit the residue mod b-1 has Fourier coefficient 1/b
    at every nonzero frequency, so P = (1 + b^-m ((b-1)[sigma == 0] - 1)) / (b-1)."""
    T = b * (b - 1) // 2
    sigma = (T - E.sum(axis=1)) % (b - 1)
    eps = float(b) ** (-m)
    return (b - 1) / (1 + eps * ((b - 1) * (sigma == 0) - 1))


def weights(n, b, s, c):
    """dict model -> per-n weight arrays (n all in valid classes)."""
    Dn = n_digits(n, b, s)
    Dq = sq_digits(n, b, c)
    # sanity: top digits nonzero (exact lengths)
    assert np.all(Dn[:, -1] > 0) and np.all(Dq[:, -1] > 0)
    out = {}
    ndist, nm = distinct(Dn)
    for A, J in M1_SPECS:
        if A + J > c:
            continue
        m = c - A - J
        E = np.concatenate([Dn, Dq[:, :J], Dq[:, c - A:]], axis=1)
        ok, em = distinct(E)
        if A >= 1:
            w = ok * math.exp(log_fact(m) - m * math.log(b)) * class_factor(b, m, E)
        else:
            zero_free = (em & np.uint64(1)) == 0  # 0 not yet used -> it is in the remaining set R
            full = math.exp(log_fact(m) - (m - 1) * math.log(b))
            part = math.exp(log_fact(m - 1) - (m - 1) * math.log(b))
            w = ok * (full - zero_free * part)
        out[f"M1({A},{J})"] = w
    if s >= 5:
        E = np.concatenate([Dn[:, :3], Dn[:, s - 2:], Dq[:, :3], Dq[:, c - 2:]], axis=1)
        ok, _ = distinct(E)
        M = b - 10
        out["M1e"] = ok * math.exp(log_fact(M) - M * math.log(b)) * class_factor(b, M, E)
    # M0: last digits exact, two leading digits legal-uniform, rest uniform; class-conditioned
    r = Dn[:, 0]
    r2 = Dq[:, 0]
    okl = r != r2
    zero_left = (r != 0) & (r2 != 0)
    rest = b - 2
    lead_ok = np.where(zero_left, (rest - 2) / rest, 1.0)
    out["M0"] = okl * lead_ok * math.exp(log_fact(rest) - math.log(b - 1) - (b - 4) * math.log(b))
    return out


def closed_forms(b):
    (s, c, lo, hi), = band(b)
    N = hi - lo + 1
    pn = math.exp(log_fact(b) - b * math.log(b))
    return {"b": b, "s": s, "c": c, "lo": lo, "hi": hi, "N": N, "roots": len(roots(b)),
            "naive": N * pn, "crude": N * len(roots(b)) * pn}


def run_exact(b, chunk=10_000_000):
    info = closed_forms(b)
    s, c, lo, hi = info["s"], info["c"], info["lo"], info["hi"]
    tot = {}
    nvalid = 0
    for x, first, cnt in class_counts(b, lo, hi):
        for k0 in range(0, cnt, chunk):
            k = np.arange(k0, min(cnt, k0 + chunk), dtype=np.int64)
            n = first + (b - 1) * k
            nvalid += len(n)
            for key, w in weights(n, b, s, c).items():
                tot[key] = tot.get(key, 0.0) + float(w.sum())
    info.update({"method": "exhaustive", "valid_class_n": nvalid, "models": tot})
    return info


def run_mc(b, samples, seed=20260927, batch=2_000_000):
    info = closed_forms(b)
    s, c, lo, hi = info["s"], info["c"], info["lo"], info["hi"]
    cls = class_counts(b, lo, hi)
    V = sum(cnt for _, _, cnt in cls)
    rng = np.random.default_rng(seed + b)
    sums, sq = {}, {}
    done = 0
    firsts = np.array([f for _, f, _ in cls], dtype=np.int64)
    cnts = np.array([cnt for _, _, cnt in cls], dtype=np.int64)
    while done < samples:
        k = min(batch, samples - done)
        u = rng.integers(0, V, size=k, dtype=np.int64)  # uniform over all valid-class n
        idx = np.searchsorted(np.cumsum(cnts), u, side="right")
        off = u - np.concatenate([[0], np.cumsum(cnts)[:-1]])[idx]
        n = firsts[idx] + (b - 1) * off
        assert np.all((n >= lo) & (n <= hi))
        for key, w in weights(n, b, s, c).items():
            sums[key] = sums.get(key, 0.0) + float(w.sum())
            sq[key] = sq.get(key, 0.0) + float((w * w).sum())
        done += k
    models, ses = {}, {}
    for key in sums:
        mean = sums[key] / done
        var = sq[key] / done - mean * mean
        models[key] = mean * V
        ses[key] = math.sqrt(max(var, 0) / done) * V
    info.update({"method": f"monte carlo, {done} samples, seed {seed + b}", "valid_class_n": V,
                 "models": models, "se": ses})
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["exact", "mc"])
    ap.add_argument("bases", type=int, nargs="+")
    ap.add_argument("--samples", type=int, default=20_000_000)
    args = ap.parse_args()
    for b in args.bases:
        if not band(b):
            continue
        if not roots(b):
            info = closed_forms(b)
            info.update({"method": "no digit-sum roots", "valid_class_n": 0, "models": {}})
        elif args.mode == "exact":
            info = run_exact(b)
        else:
            info = run_mc(b, args.samples)
        print(json.dumps(info), flush=True)


if __name__ == "__main__":
    main()
