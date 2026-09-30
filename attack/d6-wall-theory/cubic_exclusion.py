#!/usr/bin/env python3
"""Theorem D4 (D6 note): along a batch of b roots, a digit whose Lemma-1 cubic coefficient is theta3 = b^-e3
cannot be constant (D = 1) if some r <= (b-1)/3 has ||6 r^3 theta3|| >= 4/b: four points y_0, y_r, y_2r, y_3r in
one cell of length 1/b have third difference in (-4/b, 4/b), and that difference is 6 r^3 theta3 mod 1.
Prints the bases in [4, 2000] where the criterion does not apply."""
from fractions import Fraction as F
for e3 in (1, 2, 3):
    fails = [b for b in range(4, 2001) if not any(min((6 * r**3 * F(1, b**e3)) % 1, 1 - (6 * r**3 * F(1, b**e3)) % 1) >= F(4, b)
                                                  for r in range(1, (b - 1) // 3 + 1))]
    print(f"theta3 = b^-{e3}: D = 1 excluded for all b in [4, 2000] except {fails}")
