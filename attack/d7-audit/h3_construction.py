#!/usr/bin/env python3
"""D7 audit of h3-covering §3: reproduce the b+1 construction explicitly, and recompute
the full image modulo b+1 with an independent DP (numpy boolean arrays, no bit tricks).

For each base b = 10..40 with its nice-number lengths (s, c) (fallback s = round(2b/5)
where no interval exists, as class_dp.py does):

  1. Construction (Theorem 1). Build every subset E the proof uses by Lemma 1's raising
     procedure (checking that each step raises the sum by exactly 1 and ends at the top
     block), place it by Lemma 2 (checking the leading digit is nonzero), evaluate the
     actual word X = sum d_i b^i, and reduce mod b+1. Report whether the pairs realized
     by the construction cover every admissible pair, and whether the theorem's
     hypothesis holds.
  2. Independent DP over digits with the four class counts, reachable (x, y) pairs as an
     (b+1)x(b+1) numpy boolean array. Compare with class_dp.json.

Usage: python3 h3_construction.py [--max-base 40] [--classdp PATH]
"""
import argparse, json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals  # noqa: E402


def lengths(b):
    iv = candidate_intervals(b)
    if iv:
        return iv[0]["square_digits"], iv[0]["cube_digits"], True
    s = round(2 * b / 5)
    return s, b - s, False


def raise_chain(elems, r):
    """Lemma 1: all r-subsets from bottom block to top block, one raise at a time."""
    elems = sorted(elems)
    u, top = elems[0], elems[-1]
    assert elems == list(range(u, top + 1)), "Lemma 1 needs an interval"
    R = list(elems[:r])
    chain = [tuple(R)]
    target_top = tuple(elems[len(elems) - r:])
    while tuple(R) != target_top:
        Rs = set(R)
        cand = [a for a in R if a + 1 <= top and a + 1 not in Rs]
        assert cand, "Lemma 1: no raisable element but not at top block"
        a = max(cand)
        R = sorted((set(R) - {a}) | {a + 1})
        assert sum(R) == sum(chain[-1]) + 1
        chain.append(tuple(R))
    lo = r * u + r * (r - 1) // 2
    hi = r * u + r * (2 * len(elems) - r - 1) // 2
    assert sum(chain[0]) == lo and sum(chain[-1]) == hi and len(chain) == r * (len(elems) - r) + 1
    return chain


def place(S, E, length, b):
    """Lemma 2: E at even positions, S\\E at odd; smallest digit of a class at its lowest
    position, so 0 never sits at the leading position when the class has >= 2 positions."""
    E = sorted(E); O = sorted(set(S) - set(E))
    ev = list(range(0, length, 2)); od = list(range(1, length, 2))
    assert len(E) == len(ev) and len(O) == len(od)
    word = [None] * length
    for p, d in zip(ev, E): word[p] = d
    for p, d in zip(od, O): word[p] = d
    assert word[length - 1] != 0, "leading zero"
    return sum(d * b ** i for i, d in enumerate(word))


def residues(S, length, b, avoid=None):
    """X residues mod b+1 reached by the construction: E runs over e-subsets of the
    interval S minus `avoid` (the proof's restriction), via Lemma 1's chain."""
    e = (length + 1) // 2
    pool = sorted(set(S) - ({avoid} if avoid is not None else set()))
    out = set()
    for E in raise_chain(pool, e):
        X = place(S, E, length, b)
        assert X % (b + 1) == (2 * sum(E) - sum(S)) % (b + 1)
        out.add(X % (b + 1))
    return out


def construction(b, s, c):
    M = b + 1
    T = b * (b - 1) // 2
    configs = []
    SX = list(range(s)); SY = list(range(s, b))
    configs.append((SX, None, SY, None))
    if b % 2 == 1:
        if s % 2 == 1:
            configs.append((list(range(1, s + 1)), None, [0] + list(range(s + 1, b)), 0))
        else:
            configs.append((list(range(0, s - 1)) + [s], s, [s - 1] + list(range(s + 1, b)), s - 1))
    pairs = set()
    for SXc, avX, SYc, avY in configs:
        assert sorted(SXc + SYc) == list(range(b))
        rx = residues(SXc, s, b, avX); ry = residues(SYc, c, b, avY)
        pairs |= {(x, y) for x in rx for y in ry}
    g = math.gcd(M, b - 1)
    admissible = {(x, y) for x in range(M) for y in range(M) if (x + y - T) % g == 0}
    assert pairs <= admissible
    return len(pairs), len(admissible)


def theorem_condition(b, s, c):
    e, o, e2, o2 = (s + 1) // 2, s // 2, (c + 1) // 2, c // 2
    if b % 2 == 0:
        return e * o >= b and e2 * o2 >= b
    return e * (o - 1) >= (b - 1) // 2 and e2 * (o2 - 1) >= (b - 1) // 2


def image_dp(b, s, c):
    """Independent DP: digits 0..b-1 assigned to classes (X even, X odd, Y even, Y odd);
    weight +d for even, -d for odd (b == -1 mod b+1). Leading digit: 0 may go to the
    leading position's class only if that class has >= 2 positions (true for s, c >= 4)."""
    M = b + 1
    caps = ((s + 1) // 2, s // 2, (c + 1) // 2, c // 2)
    leadX = 0 if (s - 1) % 2 == 0 else 1
    leadY = 2 if (c - 1) % 2 == 0 else 3
    start = np.zeros((M, M), dtype=bool); start[0, 0] = True
    states = {(0, 0, 0, 0): start}
    for d in range(b):
        nxt = {}
        for key, arr in states.items():
            for cls in range(4):
                if key[cls] >= caps[cls]:
                    continue
                if d == 0 and cls in (leadX, leadY) and caps[cls] < 2:
                    continue
                sign = 1 if cls in (0, 2) else -1
                moved = np.roll(arr, sign * d, axis=0 if cls < 2 else 1)
                k2 = list(key); k2[cls] += 1; k2 = tuple(k2)
                if k2 in nxt:
                    nxt[k2] |= moved
                else:
                    nxt[k2] = moved.copy()
        states = nxt
    (arr,) = states.values()
    return int(arr.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-base", type=int, default=10)
    ap.add_argument("--max-base", type=int, default=40)
    ap.add_argument("--classdp", default=str(ROOT / "attack/h3-covering/results/class_dp.json"))
    a = ap.parse_args()
    cdp = {}
    if Path(a.classdp).exists():
        for r in json.load(open(a.classdp))["rows"]:
            cdp[(r["b"], r["M"])] = r
    out = []
    for b in range(a.min_base, a.max_base + 1):
        s, c, nice = lengths(b)
        cond = theorem_condition(b, s, c)
        got, adm = construction(b, s, c)
        img = image_dp(b, s, c)
        ref = cdp.get((b, b + 1))
        row = {"b": b, "s": s, "c": c, "nice_interval": nice, "theorem_condition": cond,
               "construction_pairs": got, "admissible": adm, "construction_covers": got == adm,
               "dp_image": img, "dp_covers": img == adm,
               "class_dp_image": ref["image"] if ref else None,
               "agrees_with_class_dp": (ref["image"] == img and ref["theorem_condition_holds"] == cond) if ref else None}
        out.append(row)
        print(json.dumps(row), flush=True)
    bad = [r for r in out if r["theorem_condition"] and not r["construction_covers"]]
    print("theorem condition holds but construction fails:", [r["b"] for r in bad])
    print("DP image != admissible:", [r["b"] for r in out if not r["dp_covers"]])
    print("disagreements with class_dp.json:", [r["b"] for r in out if r["agrees_with_class_dp"] is False])
    print("condition holds (nice lengths only):", [r["b"] for r in out if r["theorem_condition"] and r["nice_interval"]])
    print("construction alone covers (nice lengths only):", [r["b"] for r in out if r["construction_covers"] and r["nice_interval"]])
    Path(__file__).with_name("results").mkdir(exist_ok=True)
    Path(__file__).with_name("results").joinpath("h3_construction.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
