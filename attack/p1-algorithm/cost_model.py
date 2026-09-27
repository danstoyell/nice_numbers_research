#!/usr/bin/env python3
"""Cost model: ideal edge search vs. overlap join (with/without colour coding).

Nice numbers (multiplicity 1), same conditional random-digit model and edge
convention as critique/scripts/reachability.py (2L-2 edge digits, the last-digit
pair already enforced by the CRT filter).

Overlap join: top list T = prefixes of t digits whose certified top digits
(t-1 of n^2 and t-1 of n^3) are distinct; bottom list B = residues mod b^k
whose bottom k digits of n^2 and n^3 are distinct; t+k > L, hash-joined on the
t+k-L shared digits of n. Each n is produced by exactly one (P, R) pair.
  matches    = F * P(g_T internal) * P(g_B internal)
  survivors  = F * P(g_T + g_B jointly distinct)          (full checks)
  cost       = |T| + |B| + matches
Colour coding: random value set S of size s; T restricted to top digits in S,
B to bottom digits outside S; key-equal pairs are then disjoint by construction.
  cost = (|T_S| + |B_S|) / p_capture + survivors
Ceiling: 4L-2 certified digits with free lists (t = k = L).
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "critique/scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
from reachability import row_for, filtered_counts, log_expected  # noqa: E402
from verify import candidate_intervals  # noqa: E402

LN10 = math.log(10)


def lp(b, g, start=0):
    """log P(g uniform digits distinct), skipping the first `start` factors."""
    return sum(math.log1p(-i / b) for i in range(start, g)) if g <= b else -math.inf


def lcomb(n, r):
    if r < 0 or r > n:
        return -math.inf
    return math.lgamma(n + 1) - math.lgamma(r + 1) - math.lgamma(n - r + 1)


def lse(*xs):
    m = max(xs)
    return m + math.log(sum(math.exp(x - m) for x in xs))


def analyse(b):
    row = row_for(b)
    if row is None:
        return None
    iv, = candidate_intervals(b)
    lo, hi = iv["lo"], iv["hi"]
    L = row["root_digits"]
    lN = math.log(hi - lo + 1)
    z, nz = filtered_counts(b, lo, hi)
    lF = math.log(z + nz)
    lE = log_expected(b, z, nz)
    lead = lo // b ** (L - 1), hi // b ** (L - 1)
    out = {"base": b, "L": L, "log10_E": lE / LN10}
    # ideal edge (as reachability.py)
    w_edge = lF + lp(b, 2 * L - 2, 2)
    out["edge"] = {"certified": 2 * L - 2, "log10_cost": w_edge / LN10,
                   "log10_per_solution": (w_edge - lE) / LN10}
    best, best_cc = None, None
    for t in range(2, L + 1):
        gT = 2 * (t - 1)
        lT = lN - (L - t) * math.log(b) + lp(b, gT)          # |T|
        for k in range(1, L + 1):
            if t + k <= L:
                continue
            gB = 2 * k
            lB = k * math.log(b) + lp(b, gB)                   # |B|
            lM = lF + lp(b, gB, 2) + lp(b, gT)                 # key-equal pairs
            lS = lF + lp(b, gT + gB, 2)                        # survivors
            cost = lse(lT, lB, lM, lS)
            if best is None or cost < best["lc"]:
                best = {"t": t, "k": k, "certified": gT + gB, "lc": cost,
                        "log10_T": lT / LN10, "log10_B": lB / LN10,
                        "log10_matches": lM / LN10, "log10_survivors": lS / LN10}
            # colour coding
            for s in range(gT, b - gB + 1):
                lp_cap = lcomb(b - gT - gB, s - gT) - lcomb(b, s)
                lTs = lT + lcomb(b - gT, s - gT) - lcomb(b, s)
                lBs = lB + lcomb(b - gB, s) - lcomb(b, s)
                c2 = lse(lTs - lp_cap, lBs - lp_cap, lS)
                if best_cc is None or c2 < best_cc["lc"]:
                    best_cc = {"t": t, "k": k, "s": s, "certified": gT + gB, "lc": c2,
                               "log10_trials": -lp_cap / LN10, "log10_survivors": lS / LN10}
    for name, d in (("overlap", best), ("overlap_colour", best_cc)):
        d["log10_cost"] = d.pop("lc") / LN10
        d["log10_per_solution"] = d["log10_cost"] - lE / LN10
        out[name] = d
    ceil = lF + lp(b, 4 * L - 2, 2)
    out["ceiling_80pct"] = {"certified": 4 * L - 2, "log10_cost": ceil / LN10,
                            "log10_per_solution": (ceil - lE) / LN10}
    return out


def main():
    bases = [int(x) for x in sys.argv[1:]] or list(range(20, 131))
    rows = [r for b in bases if (r := analyse(b))]
    print(f"{'b':>4} {'L':>3} {'log10E':>7} | {'edge':>6} | {'ovl':>6} (t,k,cert) | {'ovl+cc':>6} (t,k,cert) | {'ceil':>6}")
    for r in rows:
        o, c = r["overlap"], r["overlap_colour"]
        print(f"{r['base']:>4} {r['L']:>3} {r['log10_E']:7.2f} | {r['edge']['log10_per_solution']:6.2f} | "
              f"{o['log10_per_solution']:6.2f} ({o['t']},{o['k']},{o['certified']}) | "
              f"{c['log10_per_solution']:6.2f} ({c['t']},{c['k']},{c['certified']}) | "
              f"{r['ceiling_80pct']['log10_per_solution']:6.2f}")
    if len(sys.argv) == 1:
        Path(__file__).with_name("cost_model.json").write_text(json.dumps(rows, indent=1) + "\n")


if __name__ == "__main__":
    main()
