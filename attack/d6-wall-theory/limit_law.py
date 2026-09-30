#!/usr/bin/env python3
"""Limit law of Theorem S (D6 note): in the linear-complete regime (1 <= j <= min(t-1, k)) the law of
theta1 over batches is within discrepancy O(b^-(f+j)/2) of
    nu = law of  W + lam*X^2  (mod 1),   lam = 3 b^(k-f-j),  X ~ U[0,1),
    W uniform on the subgroup (1/q)Z/Z,  q = b^j / gcd(6R', b^j),  R' uniform mod b^j, independent of X.
Fourier transform: nu^(h) = gcd(6h, b^j)/b^j * F(lam*h),  F(mu) = int_0^1 e(mu x^2) dx.
Compares nu's 64-bin histogram and Fourier coefficients with the exact law (results/theta1_*.jsonl)."""
import json, math, cmath, sys
from math import gcd, sqrt

def F(mu, n=20000):
    # int_0^1 e(mu x^2) dx by composite Simpson on a fine grid (mu <= ~1e4 here)
    n = max(n, int(40 * abs(mu)) + 2); n += n % 2
    s = 0j
    for i in range(n + 1):
        x = i / n; w = 1 if i in (0, n) else (4 if i % 2 else 2)
        s += w * cmath.exp(2j * math.pi * mu * x * x)
    return s / (3 * n)

def cdf_lamx2(lam, y):
    # P({lam X^2} < y), 0 <= y <= 1, X ~ U[0,1)
    tot = 0.0; n = 0
    while n < lam:
        tot += min(1.0, sqrt((n + y) / lam)) - min(1.0, sqrt(n / lam)); n += 1
    return tot

def prob_arc(lam, c, a, a2):
    # P({c + lam X^2} in [a, a2)), 0<=a<a2<=1
    def P_lt(y):   # P({c + lam X^2} < y) for y in [0,1]
        # {c+Z} < y  <=>  {Z} in [1-c, 1-c+y) mod 1   (c in [0,1))
        lo = (1 - c) % 1.0; hi = lo + y
        if hi <= 1: return cdf_lamx2(lam, hi) - cdf_lamx2(lam, lo)
        return (1 - cdf_lamx2(lam, lo)) + cdf_lamx2(lam, hi - 1)
    return P_lt(a2) - P_lt(a)

def nu_hist(b, j, lam, nb=64):
    bj = b ** j; w = {}
    for r in range(bj):
        q = bj // gcd(6 * r, bj); w[q] = w.get(q, 0) + 1
    h = [0.0] * nb
    for q, cnt in w.items():
        for i in range(q):
            c = i / q
            for a in range(nb):
                h[a] += cnt / bj / q * prob_arc(lam, c, a / nb, (a + 1) / nb)
    return h, w

rows = [json.loads(l) for f in ("results/theta1_exact.jsonl", "results/theta1_other_bases.jsonl") for l in open(f)]
out = []
for r in rows:
    b, t, k, f, j = r["b"], r["t"], r["k"], r["f"], r["j"]
    if r["regime"] != "linear-complete" or j > k: continue
    lam = 3 * b ** (k - f - j) if k - f - j >= 0 else 3 / b ** (f + j - k)
    hist, w = nu_hist(b, j, lam)
    dev = max(abs(x * 64 - 1) for x in hist)
    ferr = 0.0; fr = []
    for fc in r["fourier"]:
        hh = fc["h"]
        if hh == 0: continue
        pred = gcd(6 * hh, b ** j) / b ** j * F(lam * hh)
        ex = complex(*fc["brute"])
        bound = 6 * math.pi * hh / b ** (f + j)
        fr.append({"h": hh, "exact_abs": abs(ex), "nu_abs": abs(pred), "diff": abs(ex - pred), "bound_6pi_h_b^-(f+j)": bound})
        ferr = max(ferr, abs(ex - pred) / bound)
    o = {"b": b, "t": t, "k": k, "f": f, "P": r["P"], "j": j, "lambda1": lam, "maxdev64_exact": r["maxdev64_bruteforce"], "maxdev64_nu": dev,
         "subgroup_weights": {str(q): c / b ** j for q, c in sorted(w.items())}, "fourier": fr, "max_diff_over_bound": ferr}
    out.append(o)
    print(f"b={b} (t,k,f)=({t},{k},{f}) P={r['P']} j={j} lam={lam:.4g}  maxdev exact {r['maxdev64_bruteforce']:.3f}  nu {dev:.3f}  max |diff|/bound {ferr:.2f}")
json.dump(out, open("results/limit_law.json", "w"), indent=1)
