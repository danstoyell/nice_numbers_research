#!/usr/bin/env python3
"""Exact K(A,J) by brute force (independent of the C code), for small bases.

K(A,J) = #{n in band : n + n^2 == b(b-1)/2 (mod b-1), and the s digits of n together with
the top A and bottom J digits of n^2 are all distinct}.
Usage: python3 kexact.py b [b ...] -> JSON lines
"""
import json
import sys
from brute import band, digits


def valid_residues(b):
    m = b - 1
    T = b * (b - 1) // 2 % m
    return {x for x in range(m) if (x + x * x) % m == T}


def kgrid(b, amax=4, jmax=5):
    (s, c, lo, hi), = band(b)
    vr = valid_residues(b)
    K = {(A, J): 0 for A in range(amax + 1) for J in range(jmax + 1) if A + J <= c}
    for n in range(lo, hi + 1):
        if n % (b - 1) not in vr:
            continue
        dn = digits(n, b)
        if len(set(dn)) != s:
            continue
        dq = digits(n * n, b)
        for (A, J) in K:
            e = dn + dq[:J] + (dq[c - A:] if A else [])
            if len(set(e)) == len(e):
                K[(A, J)] += 1
    return {"b": b, "s": s, "c": c, "lo": lo, "hi": hi, "K": {f"{a},{j}": v for (a, j), v in sorted(K.items())}}


if __name__ == "__main__":
    for b in map(int, sys.argv[1:]):
        print(json.dumps(kgrid(b)), flush=True)
