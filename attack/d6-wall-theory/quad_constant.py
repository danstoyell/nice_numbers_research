#!/usr/bin/env python3
"""Constants for the degenerate-batch theorem (D6 note, step 2).
a_b(v) = integral over u of (1 - range_{m<b}(u m/b + v (m/b)^2))^+ du ;  A_b = integral of a_b over v in R.
Continuous limit (t in [0,1]), closed form for v >= 0 (a is even in v):
    a(v) = 1 - v^2/6 (0<=v<=1),  (8/3)sqrt(v) - 2v + v^2/6 (1<=v<=4),  0 (v>=4);   A = 2*17/9 = 34/9.
Quadratic model (x0, th1, th2 uniform):  P(D=1) = 2 A_b / b^5.
th2 uniform on [0, rho), rho < 1/2:     P(D=1) = (1/(rho b^5)) * int_0^{rho b^3} a_b(v) dv."""
import json
import numpy as np

def a_closed(v):
    v = abs(v)
    return 1 - v * v / 6 if v <= 1 else ((8 / 3) * v ** 0.5 - 2 * v + v * v / 6 if v <= 4 else 0.0)

def a_num(v, t, nu=2001):
    U = np.linspace(-abs(v) - 1.2, abs(v) + 1.2, nu)
    g = np.outer(U, t) + v * t * t
    f = np.clip(1 - (g.max(axis=1) - g.min(axis=1)), 0, None)
    return np.trapezoid(f, U)

out = {"A_closed_form": 34 / 9}
V = np.linspace(-4.5, 4.5, 361)
for label, t in [("continuous", np.linspace(0, 1, 801))] + [(f"b={b}", np.arange(b) / b) for b in (10, 13, 14, 15, 17, 19, 25, 30)]:
    av = np.array([a_num(v, t) for v in V]); A = float(np.trapezoid(av, V))
    out[label] = A
    print(f"{label:>10}: A_b = {A:.4f}   (closed form limit 34/9 = {34/9:.4f})")
out["a_check"] = [[float(v), a_closed(v), float(a_num(v, np.linspace(0, 1, 801)))] for v in (0, 0.5, 1, 2, 3, 3.9)]
print("a(v) closed vs numeric:", [(v, round(c, 4), round(n, 4)) for v, c, n in out["a_check"]])
json.dump(out, open("results/quad_constant.json", "w"), indent=1)
