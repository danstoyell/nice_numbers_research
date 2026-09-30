#!/usr/bin/env python3
"""D7 audit: Theorem A of middle-digits §5 is false as stated without an upper bound on P.
At P + 1 = 3L the hypotheses P + 1 >= 3(k+f) + eta*t and k >= eta*t hold (small eta), but
c^3 < b^(3L) = b^(P+1), so x0 = c^3 / b^(P+1) is a smooth function of c and
P(x0 < 1/2) -> (2^(-1/3) - 1/b)/(1 - 1/b) = 0.7866 (b = 30) for every t: no equidistribution.
The proof uses P + 1 <= 2L (twice), which the statement omits."""
from fractions import Fraction
b = 30
for t, k, f in [(3, 2, 1), (4, 2, 1), (6, 3, 1)]:
    L = t + k + f; P = 3 * L - 1
    lo, hi = b ** (t - 1), b ** t
    cnt = tot = 0
    for Ptop in range(lo, hi, max(1, (hi - lo) // 20000)):
        for R in (0, b ** k // 2, b ** k - 1):
            c = Ptop * b ** (k + f) + R
            cnt += Fraction(c ** 3 % b ** (P + 1), b ** (P + 1)) < Fraction(1, 2); tot += 1
    print(f"(t,k,f)=({t},{k},{f}) L={L} P={P}: P(x0 < 1/2) = {cnt / tot:.4f} (uniform: 0.5)")
