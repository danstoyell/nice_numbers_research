#!/usr/bin/env python3
"""Predicted list sizes / matches / survivors for the k-nice testbed.

P_K(g): probability that g uniform base-b digits use no value more than K times.
Edge (t+k=L): leaves = N * P_K(2(t-1)+2k) jointly.
Overlap (t+k>L): |T| = N/b^(L-t) * P_K(2(t-1)), |B| = b^k * P_K(2k),
matches = N * P_K(2(t-1)) * P_K(2k), survivors = N * P_K(2(t-1)+2k).
"""
import math
import sys
from fractions import Fraction


def pk(b, K, g):
    # g! [x^g] (sum_{j<=K} x^j/j!)^b / b^g
    poly = [Fraction(1)]
    base = [Fraction(1, math.factorial(j)) for j in range(K + 1)]
    for _ in range(b):
        new = [Fraction(0)] * min(len(poly) + K, g + 1)
        for i, a in enumerate(poly):
            if a == 0:
                continue
            for j, c in enumerate(base):
                if i + j <= g:
                    new[i + j] += a * c
        poly = new
    if g >= len(poly):
        return 0.0
    return float(poly[g] * math.factorial(g) / Fraction(b) ** g)


def main():
    b, K, lo, hi = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    N = hi - lo + 1
    L = len(str_b(hi, b))
    cache = {}
    P = lambda g: cache.setdefault(g, pk(b, K, g))
    print(f"b={b} K={K} N={N:.3e} L={L}")
    for t in range(1, L + 1):
        k = L - t
        if k < 1:
            continue
        g = 2 * (t - 1) + 2 * k
        print(f" edge t={t} k={k} cert={g} leaves={N*P(g):.3e} T={N/b**(L-t)*P(2*(t-1)):.2e} B={b**k*P(2*k):.2e}")
    for t in range(2, L + 1):
        for k in range(1, L + 1):
            if t + k <= L or t + k > L + t - 1:
                continue
            gT, gB = 2 * (t - 1), 2 * k
            T = N / b ** (L - t) * P(gT)
            B = b ** k * P(gB)
            M = N * P(gT) * P(gB)
            S = N * P(gT + gB)
            print(f" ovl t={t} k={k} o={t+k-L} cert={gT+gB} T={T:.2e} B={B:.2e} matches={M:.2e} surv={S:.2e} work={T+B+M:.2e}")


def str_b(n, b):
    out = []
    while n:
        n, d = divmod(n, b)
        out.append(d)
    return out


if __name__ == "__main__":
    main()
