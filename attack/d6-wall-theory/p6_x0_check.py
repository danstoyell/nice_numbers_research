#!/usr/bin/env python3
"""nice-30, shape (t,k)=(2,3), position P=6 (theta3 = 0, theta2 = (3R mod 30)/30, theta1 = {3R^2/b^4}).
D = 1 needs theta2 in {0, 1/2} (a pure rotation by delta = theta1 + theta2 mod 1); then
P(D=1 | x0 uniform) = (1 - b(b-1)|delta|)^+, while the actual x0 = (3 Ptop R^2 b^4 + R^3 mod b^7)/b^7.
Compares the two over all batches of the nice-30 interval (no end-check filter)."""
from fractions import Fraction
b, t, k, f, P = 30, 2, 3, 1, 6
lo, hi = 234613921, 728999999
N_act = N_mod = 0.0; nb = 0; nrot = 0
for R in range(b ** k):
    th2 = (3 * R) % b
    if th2 not in (0, 15): continue
    d = ((3 * R * R) % b ** 4) / b ** 4 + th2 / 30.0; d -= round(d)          # delta in [-1/2, 1/2]
    span = (b - 1) * abs(d) * b                                              # span of the 30 points in cell units
    for Pt in range(b ** (t - 1), b ** t):
        c = Pt * b ** (k + f) + R
        if c < lo or c + (b - 1) * b ** k > hi: continue
        nb += 1
        if span >= 1: continue
        nrot += 1
        x = ((c ** 3) % b ** 7) * b / b ** 7; x -= int(x)                    # position of y_0 inside its cell
        fits = (x + span < 1) if d >= 0 else (x - span >= 0)
        N_act += fits; N_mod += 1 - span
print(f"full batches with theta2 in {{0,1/2}}: {nb}; with span < 1 cell: {nrot}")
print(f"D=1 count: actual x0 {N_act:.0f}   uniform x0 (expected) {N_mod:.1f}   ratio {N_act / N_mod:.3f}")
