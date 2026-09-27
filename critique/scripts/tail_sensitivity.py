#!/usr/bin/env python3
"""Sensitivity of the M1 tail prediction to the number of exact edge digits.

tail_validation.py computes M1 exactly with t=2 top and k=3 bottom digits.
Here the edge-digit distinct-count distribution P(u) is instead estimated by
sampling n uniformly from the (public) interval and reading exact top-t and
bottom-k digits of n^2 and n^3, for deeper edges (t, k) in {(2,3), (3,4),
(4,5)}. The middle digits remain uniform. If a tail deficit is caused by
unmodeled edge structure, it should shrink as t and k grow.
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "critique/scripts"))
from verify import candidate_intervals  # noqa: E402
from tail_validation import middle_new_values  # noqa: E402


def edge_u_hist(b, lo, hi, s, c, t, k, samples, rng):
    ds, dc, mod = b ** (s - t), b ** (c - t), b ** k
    hist = [0] * (2 * t + 2 * k + 1)
    for _ in range(samples):
        n = rng.randint(lo, hi)
        sq, cu = n * n, n ** 3
        seen = set()
        for value, width in ((sq // ds, t), (cu // dc, t), (sq % mod, k), (cu % mod, k)):
            for _ in range(width):
                value, d = divmod(value, b)
                seen.add(d)
        hist[len(seen)] += 1
    return [h / samples for h in hist]


def predict(b, pu, t, k, deficiencies):
    m = b - 2 * t - 2 * k
    out = {r: 0.0 for r in deficiencies}
    for u, p in enumerate(pu):
        if p == 0:
            continue
        row = middle_new_values(b, m, u)
        for r in deficiencies:
            v = b - r - u
            if 0 <= v < len(row):
                out[r] += p * float(row[v])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", default=str(ROOT / "critique/results/public-bases-2026-09-26.json"))
    ap.add_argument("--samples", type=int, default=400000)
    ap.add_argument("--min-base", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260926)
    ap.add_argument("--output", default=str(ROOT / "critique/results/tail-sensitivity.json"))
    args = ap.parse_args()
    rng = random.Random(args.seed)
    snap = json.loads(Path(args.snapshot).read_text())
    configs = [(2, 3), (3, 4), (4, 5)]
    deficiencies = [1, 2, 3, 4, 5]
    pooled = {cfg: {r: 0.0 for r in deficiencies} for cfg in configs}
    observed = {r: 0 for r in deficiencies}
    rows = []
    for rec in snap["bases"]:
        b, size = rec["id"], int(rec["range_size"])
        if b < args.min_base or not rec["checked_detailed"] or int(rec["checked_detailed"]) != size:
            continue
        iv, = candidate_intervals(b)
        s, c = iv["square_digits"], iv["cube_digits"]
        lo, hi = int(rec["range_start"]), int(rec["range_end"]) - 1
        obs = {x["num_uniques"]: int(x["count"]) for x in rec["distribution"]}
        row = {"base": b, "observed": {r: obs.get(b - r, 0) for r in deficiencies}, "predicted": {}}
        for r in deficiencies:
            observed[r] += obs.get(b - r, 0)
        for t, k in configs:
            if t + k > s:
                continue
            pu = edge_u_hist(b, lo, hi, s, c, t, k, args.samples, rng)
            pred = predict(b, pu, t, k, deficiencies)
            row["predicted"][f"t{t}k{k}"] = {r: pred[r] * size for r in deficiencies}
            for r in deficiencies:
                pooled[(t, k)][r] += pred[r] * size
        rows.append(row)
        print(b, {key: round(v[2], 2) for key, v in row["predicted"].items()}, "obs", row["observed"][2], flush=True)
    summary = {}
    for cfg in configs:
        key = f"t{cfg[0]}k{cfg[1]}"
        summary[key] = {r: {"observed": observed[r], "predicted": pooled[cfg][r],
                            "obs_over_pred": observed[r] / pooled[cfg][r] if pooled[cfg][r] else None,
                            "z": (observed[r] - pooled[cfg][r]) / math.sqrt(pooled[cfg][r]) if pooled[cfg][r] else None}
                        for r in deficiencies}
        print(key, {r: (observed[r], round(pooled[cfg][r], 1), round(summary[key][r]["obs_over_pred"], 4))
                    for r in deficiencies})
    Path(args.output).write_text(json.dumps({
        "scope": "Monte Carlo estimate of edge-digit distinct counts; middle digits uniform",
        "samples_per_base_and_config": args.samples, "seed": args.seed,
        "bases": f">= {args.min_base}, complete detailed histograms only",
        "summary": summary, "rows": rows}, indent=1) + "\n")


if __name__ == "__main__":
    main()
