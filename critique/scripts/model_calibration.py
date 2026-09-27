#!/usr/bin/env python3
"""Calibrate the simple conditional model against the exact-edge model M1.

The k-nice expectations in twice_nice.py fix only the last digits exactly and
treat every other digit, including the leading ones, as uniform. This script
measures how much that simplification over-predicts on the nice-number
near-miss data, where the exact-edge model M1 (2 top, 3 bottom digits exact)
is known to match the public counts. It uses the Monte Carlo edge sampler from
tail_sensitivity.py with (t, k) = (0, 1) versus (2, 3), bases 30-48.

Usage: python3 critique/scripts/model_calibration.py
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "critique/scripts"))
from verify import candidate_intervals  # noqa: E402
from tail_sensitivity import edge_u_hist, predict  # noqa: E402


def main():
    snap = json.loads((ROOT / "critique/results/public-bases-2026-09-26.json").read_text())
    rng = random.Random(20260926)
    deficiencies = (1, 2, 3)
    totals = {"last_only": dict.fromkeys(deficiencies, 0.0),
              "exact_edges": dict.fromkeys(deficiencies, 0.0),
              "observed": dict.fromkeys(deficiencies, 0)}
    for rec in snap["bases"]:
        b, size = rec["id"], int(rec["range_size"])
        if b < 30 or not rec["checked_detailed"] or int(rec["checked_detailed"]) != size:
            continue
        iv, = candidate_intervals(b)
        s, c = iv["square_digits"], iv["cube_digits"]
        lo, hi = int(rec["range_start"]), int(rec["range_end"]) - 1
        obs = {x["num_uniques"]: int(x["count"]) for x in rec["distribution"]}
        for key, (t, k) in (("last_only", (0, 1)), ("exact_edges", (2, 3))):
            pu = edge_u_hist(b, lo, hi, s, c, t, k, 150000, rng)
            pred = predict(b, pu, t, k, list(deficiencies))
            for r in deficiencies:
                totals[key][r] += pred[r] * size
        for r in deficiencies:
            totals["observed"][r] += obs.get(b - r, 0)
    over = {r: totals["last_only"][r] / totals["exact_edges"][r] - 1 for r in deficiencies}
    for r in deficiencies:
        print(f"missing {r}: last-digit-only {totals['last_only'][r]:.1f}, exact edges "
              f"{totals['exact_edges'][r]:.1f}, observed {totals['observed'][r]}; "
              f"over-prediction {100 * over[r]:.1f}%")
    (ROOT / "critique/results/model-calibration.json").write_text(json.dumps({
        "scope": "Last-digit-only model vs exact-edge model M1 on near misses, bases 30-48 (MC, 1.5e5 samples per base)",
        "seed": 20260926, "totals": totals, "last_only_over_prediction": over}, indent=1) + "\n")


if __name__ == "__main__":
    main()
