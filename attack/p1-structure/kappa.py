#!/usr/bin/env python3
"""Measure kappa = (output digits that vary with the free block) / (free digits).

Families (L = input length, h = free digits, d = structured denominator):
  bottom : n = (a*b^m + r)/d,    r = r0 + k*d^3, k free (h digits)
  top    : n = K*b^j + floor(c*b^j/d),  K free (h digits) at the top
  middle : n = floor(c*b^m/d) + K*b^i, K free (h digits) in the middle
  generic: n uniform in the candidate interval (h = L)
Fixing r (and K) mod d^3 keeps every structured region on one orbit, so positions
that vary are driven by the free digits. A position counts as varying if it
takes >= 3 distinct values across the sample (structured positions take 1,
occasionally 2 via a carry).
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify import candidate_intervals  # noqa: E402


def digs(x, b):
    out = []
    while x:
        x, r = divmod(x, b)
        out.append(r)
    return out  # little-endian


def varying_positions(ns, b):
    cols = {}
    for n in ns:
        sq, cu = digs(n * n, b), digs(n ** 3, b)
        for i, v in enumerate(sq):
            cols.setdefault(("s", i), set()).add(v)
        for i, v in enumerate(cu):
            cols.setdefault(("c", i), set()).add(v)
    return sum(1 for s in cols.values() if len(s) >= 3)


def run(b, h, d, samples, rng):
    iv = candidate_intervals(b)[0]
    lo = iv["lo"]
    L = len(digs(lo, b))
    m = L - 1
    out = {}
    # bottom
    a = 1 + (d // 2)
    while True:
        if (a * b ** m) // d >= lo:
            break
        a += 1
    base_r = (-a * b ** m) % d
    ns = []
    for _ in range(samples):
        k = rng.randrange(b ** (h - 1), b ** h) // d ** 3
        r = base_r + k * d ** 3
        ns.append((a * b ** m + r) // d)
    out["bottom"] = varying_positions(ns, b)
    # top: K occupies the top h digits
    j = L - h
    c = 1
    ns = [(rng.randrange(b ** (h - 1), b ** h) // d ** 3) * d ** 3 * b ** j
          + (c * b ** j) // d for _ in range(samples)]
    out["top"] = varying_positions(ns, b)
    # middle: K at position i = L//2 - h//2
    i = L // 2 - h // 2
    top = (a * b ** m) // d
    ns = [top - (top // b ** i % b ** h) * b ** i
          + (rng.randrange(b ** h) // d ** 3) * d ** 3 * b ** i
          for _ in range(samples)]
    out["middle"] = varying_positions(ns, b)
    ns = [rng.randrange(lo, iv["hi"] + 1) for _ in range(samples)]
    out["generic"] = varying_positions(ns, b)
    return L, out


def main():
    rng = random.Random(1)
    print(f"{'b':>5} {'L':>4} {'h':>3} {'d':>3} | varying output digits "
          f"(kappa = varying/h; generic uses h = L)")
    for b, h, d in ((200, 6, 3), (200, 10, 7), (500, 8, 5), (1000, 10, 7),
                    (1000, 20, 7)):
        L, out = run(b, h, d, 300, rng)
        parts = [f"{k}={v} (k={v / (L if k == 'generic' else h):.2f})"
                 for k, v in out.items()]
        print(f"{b:>5} {L:>4} {h:>3} {d:>3} | " + "  ".join(parts))


if __name__ == "__main__":
    main()
