#!/usr/bin/env python3
"""Residue covering for moduli M | b^2 - 1, by a DP over digits with position CLASSES.

For M | b^2 - 1 the weight of position i depends only on i mod 2, so a split is
determined, as far as (X mod M, Y mod M) goes, by which digits land in the four
classes X_even, X_odd, Y_even, Y_odd (sizes ceil(s/2), floor(s/2), ceil(c/2),
floor(c/2)). The DP processes the digits 0..b-1 in order; its state is the four
class counts so far plus a bitset of reachable (X mod M, Y mod M) pairs.
Leading digits: for s, c >= 4 every class has >= 2 positions, so digit 0 can
always be placed at a non-leading position of its class; no constraint is needed.

Usage: python3 class_dp.py [--max-base 40] [--moduli b+1,b^2-1]
Prints one JSON line per (b, M) and a summary of the theorem's sufficient
conditions.
"""
import argparse, json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals  # noqa: E402


def lengths(b):
    iv = candidate_intervals(b)
    if iv:
        return iv[0]["square_digits"], iv[0]["cube_digits"]
    s = round(2 * b / 5)
    return s, b - s


def cover(b, s, c, M, wX, wY):
    """wX, wY: weights (mod M) of the even and odd classes of each word."""
    eX, oX, eY, oY = (s + 1) // 2, s // 2, (c + 1) // 2, c // 2
    MM = M * M
    full = (1 << MM) - 1
    # row masks for rotating y within rows: bits with (index mod M) >= d and < d
    rowlo = [0] * M
    base_lo = 0
    for x in range(M):
        base_lo |= 1 << (x * M)
    # mask of bits with y < d: sum_{y<d} base_lo << y
    acc = 0
    for d in range(M):
        rowlo[d] = acc
        acc |= base_lo << d
    def add_x(v, d):        # x -> x + d (mod M): global rotation by d*M bits
        if d == 0: return v
        sh = d * M
        return ((v << sh) | (v >> (MM - sh))) & full
    def add_y(v, d):        # y -> y + d (mod M): rotation within every row
        if d == 0: return v
        hi = (v << d) & full & ~rowlo[d]          # bits whose new y >= d (no wrap)
        lo = (v >> (M - d)) & rowlo[d]            # wrapped bits land at y < d
        return hi | lo
    states = {(0, 0, 0, 0): 1}                    # (0,0) reachable
    for dgt in range(b):
        nxt = {}
        for (a, bb, cc, dd), v in states.items():
            if a < eX:
                k = (a + 1, bb, cc, dd); nxt[k] = nxt.get(k, 0) | add_x(v, dgt * wX[0] % M)
            if bb < oX:
                k = (a, bb + 1, cc, dd); nxt[k] = nxt.get(k, 0) | add_x(v, dgt * wX[1] % M)
            if cc < eY:
                k = (a, bb, cc + 1, dd); nxt[k] = nxt.get(k, 0) | add_y(v, dgt * wY[0] % M)
            if dd < oY:
                k = (a, bb, cc, dd + 1); nxt[k] = nxt.get(k, 0) | add_y(v, dgt * wY[1] % M)
        states = nxt
    (v,) = states.values()
    T = b * (b - 1) // 2
    g = math.gcd(M, b - 1)
    image = bin(v).count("1")
    predicted = MM // g
    outside = 0
    for idx in range(MM):
        if v >> idx & 1:
            x, y = divmod(idx, M)
            if (x + y - T) % g: outside += 1
    return image, predicted, outside


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-base", type=int, default=10)
    ap.add_argument("--max-base", type=int, default=40)
    ap.add_argument("--max-base-sq", type=int, default=24, help="largest base for M = b^2-1")
    ap.add_argument("--output", default=str(ROOT / "attack/h3-covering/results/class_dp.json"))
    args = ap.parse_args()
    rows = []
    for b in range(args.min_base, args.max_base + 1):
        s, c = lengths(b)
        for M in (b + 1, b * b - 1):
            if M == b * b - 1 and b > args.max_base_sq: continue
            wX = (1 % M, (b % M))    # even positions weight 1, odd positions weight b
            image, predicted, outside = cover(b, s, c, M, wX, wX)
            eX, oX, eY, oY = (s + 1) // 2, s // 2, (c + 1) // 2, c // 2
            if b % 2 == 0:
                cond = eX * oX >= b and eY * oY >= b
            else:
                cond = eX * (oX - 1) >= (b - 1) // 2 and eY * (oY - 1) >= (b - 1) // 2
            row = {"b": b, "s": s, "c": c, "M": M, "g": math.gcd(M, b - 1), "image": image,
                   "predicted": predicted, "outside_prediction": outside,
                   "equal": image == predicted and outside == 0,
                   "theorem_condition_holds": bool(cond) if M == b + 1 else None}
            rows.append(row); print(json.dumps(row), flush=True)
    Path(args.output).write_text(json.dumps({"rows": rows}, indent=1) + "\n")
    fails = [r for r in rows if not r["equal"]]
    print("failures:", [(r["b"], r["M"], r["predicted"] - r["image"]) for r in fails])
    print("b+1 theorem condition holds for b in:", [r["b"] for r in rows if r["M"] == r["b"] + 1 and r["theorem_condition_holds"]])


if __name__ == "__main__":
    main()
