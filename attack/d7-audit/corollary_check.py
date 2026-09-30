#!/usr/bin/env python3
"""D7 audit: h3-covering Corollary. For every b in [10, 200000] and every s allowed by the
necessary length condition 2b-2 < 5s < 2b+3 (c = b - s), check Theorem 1's hypothesis
(even b: e*o >= b and e'*o' >= b; odd b: e(o-1) >= (b-1)/2 and e'(o'-1) >= (b-1)/2).
Also list the bases below the Corollary's thresholds where it holds anyway, and check the
algebra 4b^2 - 108b - 21 >= 0 <=> b >= 28."""
def cond(b, s):
    c = b - s; e, o, e2, o2 = (s + 1) // 2, s // 2, (c + 1) // 2, c // 2
    if b % 2 == 0: return e * o >= b and e2 * o2 >= b
    return e * (o - 1) >= (b - 1) // 2 and e2 * (o2 - 1) >= (b - 1) // 2
fails, small_ok, no_s = [], [], []
for b in range(10, 200001):
    ss = [s for s in range((2 * b - 2) // 5, (2 * b + 3) // 5 + 1) if 2 * b - 2 < 5 * s < 2 * b + 3]
    if not ss: no_s.append(b); continue
    for s in ss:
        ok = cond(b, s)
        above = (b % 2 == 0 and b >= 28) or (b % 2 == 1 and b >= 21)
        if above and not ok: fails.append((b, s))
        if not above and ok: small_ok.append((b, s))
print("violations above the Corollary thresholds:", fails[:10], len(fails))
print("bases below thresholds where the hypothesis holds anyway:", small_ok)
print("bases 10..40 with no admissible s:", [b for b in no_s if b <= 40], "; all == 1 mod 5:", all(b % 5 == 1 for b in no_s))
print("4b^2-108b-21 >= 0 first at b =", next(b for b in range(1, 100) if 4*b*b - 108*b - 21 >= 0))
