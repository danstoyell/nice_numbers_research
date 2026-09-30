#!/usr/bin/env python3
"""Checks the form of the three gap theorem used in Theorem D1 (D6 note): for the N points {m*theta}, 0 <= m < N,
with q+ = argmin_{1<=m<N} {m theta}, q- = argmax_{1<=m<N} {m theta}, a = {q+ theta}, a' = 1 - {q- theta}:
the gaps are a (N - q+ times), a' (N - q- times), a + a' (q+ + q- - N times).  Exact rational arithmetic."""
from fractions import Fraction
import random
random.seed(5); bad = 0; tests = 0
for _ in range(3000):
    N = random.randint(2, 60); th = Fraction(random.randint(1, 10**9 - 1), 10**9 + 7)
    pts = sorted((m * th) % 1 for m in range(N))
    gaps = [pts[i + 1] - pts[i] for i in range(N - 1)] + [1 - pts[-1] + pts[0]]
    fr = {m: (m * th) % 1 for m in range(1, N)}
    qp = min(fr, key=fr.get); qm = max(fr, key=fr.get)
    a = fr[qp]; a2 = 1 - fr[qm]
    pred = {}
    for L, c in ((a, N - qp), (a2, N - qm), (a + a2, qp + qm - N)):
        if c: pred[L] = pred.get(L, 0) + c
    got = {}
    for g in gaps: got[g] = got.get(g, 0) + 1
    tests += 1; bad += got != pred
print(f"{tests} random (theta, N): multiplicity statement fails in {bad}")
