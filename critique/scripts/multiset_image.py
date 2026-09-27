#!/usr/bin/env python3
"""Residues of pandigital (square-word, cube-word) splits modulo M.

Enumerates every split of the digits 0..b-1 into an s-digit and a c-digit word
(leading digits nonzero) and compares the set of (X mod M, Y mod M) with the set
allowed by the digit-sum congruence alone. Supports the claim in
critique/research-directions.md that, for M coprime to b and words long
compared with log_b(M), pandigitality imposes no modular condition beyond the
digit sum. Usage: python3 critique/scripts/multiset_image.py [M ...]
"""
# For every pandigital split of 0..b-1 into an s-digit "square" word and c-digit "cube" word
# (leading digits nonzero), record (X mod M, Y mod M). Compare the image with the set
# predicted by digit sum alone: {(x,y): x+y = T mod gcd(M,b-1)}. M coprime to b.
import itertools, math, json, sys
b, s, c = 10, 4, 6
T = b*(b-1)//2
Ms = [int(a) for a in sys.argv[1:]] or [3, 7, 9, 11, 13, 21, 27, 33, 37, 99, 101]
img = {M: set() for M in Ms}
count = 0
for perm in itertools.permutations(range(b)):
    if perm[0] == 0 or perm[s] == 0:
        continue
    X = 0
    for d in perm[:s]: X = X*b + d
    Y = 0
    for d in perm[s:]: Y = Y*b + d
    count += 1
    for M in Ms:
        img[M].add((X % M, Y % M))
out = {}
for M in Ms:
    g = math.gcd(M, b-1)
    predicted = {(x, y) for x in range(M) for y in range(M) if (x + y - T) % g == 0}
    out[M] = {"image": len(img[M]), "predicted": len(predicted), "equal": img[M] == predicted}
print(json.dumps({"base": b, "lengths": [s, c], "pandigital_pairs": count, "results": out}))
