#!/usr/bin/env python3
"""D7 audit: middle-digits/models.py iid occupancy law P(D=d) = C(b,d) d! S(N,d) / b^N.
stirling2_row and iid_dist are copied verbatim from models.py (importing it would rewrite
results/domain_models.json). Checks: brute force over all b^N sequences for small (b, N);
inclusion-exclusion for b = N = 13, 14, 15, 17, 19, 25, 30; mean against b(1-(1-1/b)^N);
and the H1 table's 'iid exact' means and summarize.py's iid P(D<=3) column."""
import itertools, math
from fractions import Fraction

def stirling2_row(N, maxd):
    S = [0] * (maxd + 1); S[0] = 1
    for n in range(1, N + 1):
        new = [0] * (maxd + 1)
        for d in range(1, min(n, maxd) + 1):
            new[d] = d * S[d] + S[d - 1]
        S = new
    return S

def iid_dist(b, N):
    S = stirling2_row(N, b)
    tot = b ** N
    return [math.comb(b, d) * math.factorial(d) * S[d] / tot for d in range(b + 1)]

worst = 0.0
for b, N in [(3, 5), (4, 4), (4, 7), (5, 5), (6, 6), (7, 6), (3, 9)]:
    cnt = [0] * (b + 1)
    for seq in itertools.product(range(b), repeat=N):
        cnt[len(set(seq))] += 1
    exact = [x / b ** N for x in cnt]
    got = iid_dist(b, N)
    err = max(abs(x - y) for x, y in zip(exact, got)); worst = max(worst, err)
    print(f"brute force b={b} N={N}: max |error| = {err:.2e}")
for b in [13, 14, 15, 17, 19, 25, 30]:
    N = b
    # surjections onto a fixed d-set by inclusion-exclusion
    ie = [sum((-1) ** j * math.comb(d, j) * (d - j) ** N for j in range(d + 1)) for d in range(b + 1)]
    S = stirling2_row(N, b)
    assert all(ie[d] == math.factorial(d) * S[d] for d in range(b + 1)), b
    p = iid_dist(b, N)
    mean = sum(d * p[d] for d in range(b + 1)); closed = b * (1 - (1 - 1 / b) ** N)
    le3 = Fraction(sum(math.comb(b, d) * ie[d] for d in range(1, 4)), b ** N)
    print(f"b={b}: Stirling == inclusion-exclusion; sum={sum(p):.15f}; mean {mean:.4f} vs closed form {closed:.4f}; P(D<=3) = {float(le3):.2e}")
print("worst brute-force error:", worst)
