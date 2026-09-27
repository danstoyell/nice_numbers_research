#!/usr/bin/env python3
"""Test the random-digit heuristic in its extreme tail, using public data.

The public project's detailed mode records, for every candidate n in a base's
exact interval, how many distinct digits n^2 and n^3 jointly contain. Bases
10-48 are complete. A nice number is the case "b distinct"; the heuristic that
predicts nice numbers in large bases is a claim about this histogram's tail.
The counts at b-1, b-2, b-3, ... are far larger than the nice count, so they
test the heuristic where it matters with real statistical power.

Two models are compared with the observed histograms:

* M0 - uniform legal strings: b digits, the two leading ones uniform on
  1..b-1, the rest uniform on 0..b-1 (exact inclusion-exclusion).
* M1 - exact edges, random middle: the top t digits of both powers follow
  their exact distribution over the interval (integer roots, exact segment
  weights) and the bottom k digits follow their exact distribution over
  residues mod b^k (exact counts). Top and bottom are treated as independent;
  the remaining b-2t-2k digits are uniform. Exact rational occupancy formula.

Usage: python3 critique/scripts/tail_validation.py
Input: critique/results/public-bases-2026-09-26.json (dated API snapshot).
"""
import argparse
import json
import math
import sys
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals, floor_root, ceil_root  # noqa: E402


def digits_fixed(value, base, width):
    out = []
    for _ in range(width):
        value, d = divmod(value, base)
        out.append(d)
    return out


def mask_of(ds):
    m = 0
    for d in ds:
        m |= 1 << d
    return m


@lru_cache(maxsize=None)
def stirling2_row(j):
    """S(j, v) for v = 0..j."""
    row = [1]
    for i in range(1, j + 1):
        new = [0] * (i + 1)
        for v in range(1, i + 1):
            new[v] = v * (row[v] if v < len(row) else 0) + row[v - 1]
        row = new
    return tuple(row)


def m0_distribution(b):
    """Exact P(D distinct) for uniform legal strings of length b."""
    total = (b - 1) ** 2 * b ** (b - 2)

    def within(u, has_zero):
        return (u - 1) ** 2 * u ** (b - 2) if has_zero else u ** b

    probs = {}
    for d in range(1, b + 1):
        s = 0
        for u in range(1, d + 1):
            inner = math.comb(b - 1, u - 1) * within(u, True) + math.comb(b - 1, u) * within(u, False)
            s += (-1) ** (d - u) * math.comb(b - u, d - u) * inner
        probs[d] = Fraction(s, total)
    assert sum(probs.values()) == 1
    return probs


def middle_new_values(b, m, u):
    """Row over v of P(m uniform digits add exactly v values outside a
    fixed set of size u), as exact Fractions."""
    n_out = b - u
    denom = b ** m
    row = []
    for v in range(0, min(m, n_out) + 1):
        s = 0
        for j in range(v, m + 1):
            st = stirling2_row(j)
            if v >= len(st) or st[v] == 0:
                continue
            s += math.comb(m, j) * u ** (m - j) * st[v]
        row.append(Fraction(s * math.comb(n_out, v) * math.factorial(v), denom))
    return row


def top_configs(b, lo, hi, s, c, t):
    """Exact segments of [lo, hi] on which the top t digits of n^2 and n^3
    are constant. Returns (masks, weights) as numpy arrays."""
    ds, dc = b ** (s - t), b ** (c - t)
    points = {lo, hi + 1}
    for v in range((lo * lo) // ds + 1, (hi * hi) // ds + 1):
        points.add(ceil_root(v * ds, 2))
    for v in range((lo ** 3) // dc + 1, (hi ** 3) // dc + 1):
        points.add(ceil_root(v * dc, 3))
    points = sorted(p for p in points if lo <= p <= hi + 1)
    masks, weights = [], []
    for a, z in zip(points, points[1:]):
        if z <= a:
            continue
        t2 = (a * a) // ds
        t3 = (a ** 3) // dc
        ds2 = digits_fixed(t2, b, t)
        ds3 = digits_fixed(t3, b, t)
        assert ds2[-1] != 0 and ds3[-1] != 0 and t2 < b ** t and t3 < b ** t
        masks.append(mask_of(ds2 + ds3) if len(set(ds2 + ds3)) == 2 * t else -1 - mask_of(ds2 + ds3))
        weights.append(z - a)
    return masks, weights


def bottom_configs(b, lo, hi, k):
    mod = b ** k
    masks, weights = [], []
    for r in range(mod):
        cnt = (hi - r) // mod - (lo - 1 - r) // mod
        if cnt <= 0:
            continue
        d2 = digits_fixed(r * r % mod, b, k)
        d3 = digits_fixed(r ** 3 % mod, b, k)
        masks.append(mask_of(d2 + d3))
        weights.append(cnt)
    return masks, weights


def distinct_count_distribution(b, top, bottom):
    """P(u) where u = number of distinct values among all edge digits."""
    tm = np.array([m if m >= 0 else -1 - m for m in top[0]], dtype=np.uint64)
    tw = np.array(top[1], dtype=np.float64)
    bm_raw = np.array(bottom[0], dtype=np.uint64)
    bw_raw = np.array(bottom[1], dtype=np.float64)
    # group identical bottom masks
    bm, inv = np.unique(bm_raw, return_inverse=True)
    bw = np.bincount(inv, weights=bw_raw)
    hist = np.zeros(b + 1)
    for mask, w in zip(tm, tw):
        u = np.bitwise_count(bm | mask).astype(np.int64)
        hist += w * np.bincount(u, weights=bw, minlength=b + 1)
    return hist / hist.sum()


def m1_distribution(b, lo, hi, s, c, t, k):
    top = top_configs(b, lo, hi, s, c, t)
    bottom = bottom_configs(b, lo, hi, k)
    pu = distinct_count_distribution(b, top, bottom)
    m = b - 2 * t - 2 * k
    out = {d: 0.0 for d in range(1, b + 1)}
    for u in range(1, 2 * t + 2 * k + 1):
        if pu[u] == 0:
            continue
        row = middle_new_values(b, m, u)
        for v, p in enumerate(row):
            if 1 <= u + v <= b:
                out[u + v] += pu[u] * float(p)
    return out, len(top[0]), len(bottom[0])


def poisson_z(obs, exp):
    return (obs - exp) / math.sqrt(exp) if exp > 0 else float("nan")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", default=str(ROOT / "critique/results/public-bases-2026-09-26.json"))
    ap.add_argument("--output", default=str(ROOT / "critique/results/tail-validation.json"))
    ap.add_argument("--tail", type=int, default=6, help="deficiencies 0..tail reported")
    args = ap.parse_args()
    snap = json.loads(Path(args.snapshot).read_text())
    rows = []
    pooled = {}
    for rec in snap["bases"]:
        b = rec["id"]
        size = int(rec["range_size"])
        if not rec["checked_detailed"] or int(rec["checked_detailed"]) != size:
            continue
        iv, = candidate_intervals(b)
        lo, hi = iv["lo"], iv["hi"]
        api_lo, api_hi = int(rec["range_start"]), int(rec["range_end"]) - 1
        observed = {x["num_uniques"]: int(x["count"]) for x in rec["distribution"]}
        s, c = iv["square_digits"], iv["cube_digits"]
        t = 2
        k = 3 if s >= t + 3 and b >= 12 else 2
        m0 = m0_distribution(b)
        m1, n_top, n_bottom = m1_distribution(b, api_lo, api_hi, s, c, t, k)
        mean_obs = sum(d * n for d, n in observed.items()) / size
        mean_m0 = float(sum(d * p for d, p in m0.items()))
        mean_m1 = sum(d * p for d, p in m1.items())
        tail = []
        for r in range(0, args.tail + 1):
            d = b - r
            o = observed.get(d, 0)
            e0 = float(m0[d]) * size
            e1 = m1[d] * size
            tail.append({"deficiency": r, "distinct": d, "observed": o,
                         "m0_expected": e0, "m1_expected": e1,
                         "obs_over_m1": o / e1 if e1 else None,
                         "z_m1": poisson_z(o, e1)})
            if b >= 20:
                p = pooled.setdefault(r, {"observed": 0, "m0": 0.0, "m1": 0.0})
                p["observed"] += o
                p["m0"] += e0
                p["m1"] += e1
        rows.append({"base": b, "size": size, "exact_lo": lo, "exact_hi": hi,
                     "api_lo": api_lo, "api_hi": api_hi,
                     "api_matches_exact_interval": (lo, hi) == (api_lo, api_hi),
                     "top_digits_t": t, "bottom_digits_k": k,
                     "top_segments": n_top, "bottom_residues": n_bottom,
                     "mean_distinct_observed": mean_obs, "mean_m0": mean_m0, "mean_m1": mean_m1,
                     "tail": tail})
        print(f"base {b:2d}  N={size:.3e}  interval_ok={(lo, hi) == (api_lo, api_hi)}  "
              f"mean obs/M0/M1 = {mean_obs/b:.4f}/{mean_m0/b:.4f}/{mean_m1/b:.4f}", flush=True)
        for x in tail[:5]:
            print(f"    D=b-{x['deficiency']}: obs {x['observed']:>8d}  M0 {x['m0_expected']:12.2f}  "
                  f"M1 {x['m1_expected']:12.2f}  obs/M1 {x['obs_over_m1'] or float('nan'):.3f}  "
                  f"z {x['z_m1']:+.2f}", flush=True)
    for r, p in sorted(pooled.items()):
        p["obs_over_m0"] = p["observed"] / p["m0"] if p["m0"] else None
        p["obs_over_m1"] = p["observed"] / p["m1"] if p["m1"] else None
        p["z_m1"] = poisson_z(p["observed"], p["m1"])
    print("pooled over bases 20-48:")
    for r, p in sorted(pooled.items()):
        print(f"  deficiency {r}: observed {p['observed']:>9d}  M0 {p['m0']:14.2f}  M1 {p['m1']:14.2f}  "
              f"obs/M0 {p['obs_over_m0']:.4f}  obs/M1 {p['obs_over_m1']:.4f}  z(M1) {p['z_m1']:+.2f}")
    Path(args.output).write_text(json.dumps({
        "scope": "Public detailed-mode histograms versus random-digit models; heuristic evidence only",
        "snapshot": {k: snap[k] for k in ("source", "fetched", "sha256")},
        "models": {"M0": "uniform legal strings", "M1": "exact top-t/bottom-k edge digits, uniform middle"},
        "rows": rows, "pooled_bases_20_to_48": pooled}, indent=1) + "\n")


if __name__ == "__main__":
    main()
