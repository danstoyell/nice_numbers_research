#!/usr/bin/env python3
"""Exhaustive check of the bottom-up 'line lemma' used in REPORT.md, section 4.

Lemma.  Let gcd(b,6)=1, n = n' + t*b^i with n' < b^i, i >= 1, 0 <= t < b, and
n_0 = n mod b a unit with 2-3n_0 a unit mod b.  Then
   digit_i(n^2) = (A(n') + 2 n_0 t) mod b,   digit_i(n^3) = (B(n') + 3 n_0^2 t) mod b,
so as t varies the new output pair runs over a line in (Z/b)^2 whose two coordinates
are bijections of t.  Hence if the 2i digits below position i are pairwise distinct,
at least b - 4i - 1 values of t keep all 2(i+1) bottom digits pairwise distinct.

Consequence: #{n mod b^k : lowest k digits of n^2 and of n^3 (2k digits) pairwise distinct}
   >= G_b * prod_{i=1}^{k-1} (b - 4i - 1),
where G_b = #{n_0 : n_0, 2-3n_0 units, n_0^2 != n_0^3 mod b}.
The script verifies the digit identity for every n' and the count bound exactly.
"""
import json
from math import gcd, prod
from pathlib import Path


def low_digits(x, b, k):
    out = []
    for _ in range(k):
        out.append(x % b)
        x //= b
    return out


def check(b, k):
    assert gcd(b, 6) == 1
    good0 = [n0 for n0 in range(b) if gcd(n0, b) == 1 and gcd((2 - 3 * n0) % b, b) == 1
             and (n0 * n0) % b != (n0 ** 3) % b]
    # identity check
    for i in range(1, k):
        for nprime in range(b ** i):
            n0 = nprime % b
            A = (nprime ** 2 // b ** i) % b
            B = (nprime ** 3 // b ** i) % b
            for t in range(b):
                n = nprime + t * b ** i
                assert (n * n // b ** i) % b == (A + 2 * n0 * t) % b
                assert (n ** 3 // b ** i) % b == (B + 3 * n0 * n0 * t) % b
    # exact count vs bound, restricted to units n0 with the stated conditions
    count = 0
    for n in range(b ** k):
        if n % b not in good0:
            continue
        d = low_digits(n * n, b, k) + low_digits(n ** 3, b, k)
        count += len(set(d)) == 2 * k
    bound = len(good0) * prod(b - 4 * i - 1 for i in range(1, k))
    model = b ** k * prod((b - j) / b for j in range(2 * k))
    return {"b": b, "k": k, "G_b": len(good0), "exact_count": count,
            "lemma_lower_bound": bound, "ratio": count / bound,
            "all_residue_model_count": model}


if __name__ == "__main__":
    rows = [check(b, k) for b, k in [(13, 3), (17, 3), (25, 3), (29, 3), (37, 3), (41, 3), (17, 4), (29, 4)]]
    for r in rows:
        print(r)
        assert r["exact_count"] >= r["lemma_lower_bound"]
    out = Path(__file__).resolve().parent / "results" / "edge_lemma_check.json"
    out.write_text(json.dumps(rows, indent=2) + "\n")
    print("wrote", out)
