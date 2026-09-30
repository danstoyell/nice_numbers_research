#!/usr/bin/env python3
"""D7 audit of middle-digits §5 (text after Theorem C). For i >= 1, (n + delta b^i)^3 - n^3
== 3 n0^2 delta b^i (mod b^(i+1)) and the digits below i do not change, so the cube's digit
at position i changes iff b does not divide 3 n0^2 delta: there is no carry. Exact
probabilities for b = 30 with n0 uniform mod b and
  (a) delta = d' - d, d uniform, d' uniform among the other b-1 digits (midpoly sens);
  (b) delta uniform in {1..b-1} (Theorem C's delta);
  (c) delta uniform in {0..b-1} (includes delta = 0; this reproduces the report's 0.73/0.80)."""
from fractions import Fraction as F
b = 30
def prob(coef_pow, deltas):
    tot = F(0); w = F(1, b * len(deltas))
    for n0 in range(b):
        for dl in deltas:
            if (coef_pow(n0) * dl) % b != 0: tot += w
    return tot
cube = lambda n0: 3 * n0 * n0
square = lambda n0: 2 * n0
a = [d2 - d for d in range(b) for d2 in range(b) if d2 != d]
for name, ds in [("(a) midpoly sens, delta = d'-d", a), ("(b) delta in 1..b-1", list(range(1, b))), ("(c) delta in 0..b-1", list(range(b)))]:
    pc, ps = prob(cube, ds), prob(square, ds)
    print(f"{name}: cube P(change at i) = {pc} = {float(pc):.4f}; square = {ps} = {float(ps):.4f}")
