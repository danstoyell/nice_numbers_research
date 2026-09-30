#!/usr/bin/env python3
"""Theorem S for a general exponent e (D6 note, step 3): in the linear regime 1 <= j <= min(t-1, k+f)
(j = P+1-2k-f, J = P+1-k) the linear coefficient theta1 = (e c^(e-1) mod b^J)/b^J of Lemma 1_e satisfies:
given R, theta1 is uniform on the coset  e R^(e-1)/b^J + (g/b^j) Z/Z,  g = gcd(e(e-1) R^(e-2), b^j).
Exact check: brute-force histogram over all batches == mixture histogram (4096 bins, integer counts)."""
import json
from math import gcd
out = []
for (b, e, t, k, f) in [(10, 4, 3, 3, 1), (7, 4, 4, 3, 1), (10, 5, 3, 2, 1), (6, 4, 4, 3, 2), (12, 2, 3, 2, 1)]:
    L = t + k + f
    for j in range(1, min(t - 1, k + f) + 1):
        P = j + 2 * k + f - 1; J = P + 1 - k; bJ, bj = b ** J, b ** j; NB = 4096
        brute = [0] * NB; mix = [0] * NB
        Pmin, Pmax = b ** (t - 1), b ** t; NP = Pmax - Pmin
        for R in range(b ** k):
            for Pt in range(Pmin, Pmax):
                c = Pt * b ** (k + f) + R
                v = (e * c ** (e - 1)) % bJ; brute[v * NB // bJ] += 1
            g = gcd(e * (e - 1) * R ** (e - 2) if e >= 2 else 0, bj) if e > 2 else gcd(e * (e - 1), bj)
            q = bj // g; w = NP // q; assert NP % q == 0
            base = (e * R ** (e - 1)) % bJ; step = (b ** (k + f) * g) % bJ
            for i in range(q): mix[((base + i * step) % bJ) * NB // bJ] += w
        dev = max(abs(x * NB / (NP * b ** k) - 1) for x in brute[::1])
        ok = brute == mix
        out.append({"b": b, "e": e, "t": t, "k": k, "f": f, "P": P, "j": j, "equal_4096": ok})
        print(f"b={b} e={e} (t,k,f)=({t},{k},{f}) P={P} j={j}: brute == mixture: {ok}")
json.dump(out, open("results/theorem_s_general_e.json", "w"), indent=1)
