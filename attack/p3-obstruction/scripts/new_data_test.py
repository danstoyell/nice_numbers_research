#!/usr/bin/env python3
"""Pre-registered out-of-sample test: deficiency-2 count in the detailed-checked
parts of bases 49 and 50 against model M1 (exact top-2/bottom-3 digits, uniform
middle), computed with critique/scripts/tail_validation.py's exact M1.

The public chunk caches give, per chunk (1% of a base), the number of
detailed-checked candidates and their exact histogram, but not which 1e9-wide
fields inside a partial chunk were checked (they are not a contiguous prefix).
M1 depends on position only through the top digits, so the prediction for a
partial chunk is bracketed three ways:
  uniform - the checked fields are spread evenly over the chunk;
  prefix  - they are the first `checked_detailed` integers of the chunk;
  suffix  - they are the last `checked_detailed` integers of the chunk.
Fully checked chunks are exact under every assumption.

Usage: python3 attack/p3-obstruction/scripts/new_data_test.py
"""
import json
import math
import sys

sys.dont_write_bytecode = True  # never write caches into critique/ or scripts/
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "critique/scripts"))
from verify import candidate_intervals  # noqa: E402
from tail_validation import top_configs, bottom_configs, distinct_count_distribution, middle_new_values  # noqa: E402

DEFS = (0, 1, 2, 3, 4)


def m1_rates(b, lo, hi, s, c, bottom, t=2, k=3):
    top = top_configs(b, lo, hi, s, c, t)
    pu = distinct_count_distribution(b, top, bottom)
    m = b - 2 * t - 2 * k
    out = {r: 0.0 for r in DEFS}
    for u in range(1, 2 * t + 2 * k + 1):
        if pu[u] == 0:
            continue
        row = middle_new_values(b, m, u)
        for r in DEFS:
            v = b - r - u
            if 0 <= v < len(row):
                out[r] += pu[u] * float(row[v])
    return out


def poisson_cdf(k, mu):
    return sum(math.exp(-mu) * mu ** i / math.factorial(i) for i in range(k + 1))


def main():
    report = {}
    for b in (49, 50):
        chunks = json.loads((HERE / f"data/chunks-{b}.json").read_text())
        iv, = candidate_intervals(b)
        s, c = iv["square_digits"], iv["cube_digits"]
        bottom = bottom_configs(b, 0, b ** 3 * 1000 - 1, 3)  # uniform over residues mod b^3
        tot = {a: {r: 0.0 for r in DEFS} for a in ("uniform", "prefix", "suffix")}
        obs = {r: 0 for r in DEFS}
        checked = 0
        nfull = npart = 0
        for ch in chunks:
            if not ch["distribution"] or not ch["checked_detailed"]:
                continue
            lo, hi = int(ch["range_start"]), int(ch["range_end"]) - 1
            hi = min(hi, iv["hi"])
            hist = {x["num_uniques"]: int(x["count"]) for x in ch["distribution"]}
            # The histogram is what was observed; one base-49 chunk cache (1133)
            # states 1.195e12 more checked than its histogram covers.
            cd = sum(hist.values())
            assert 0 < cd <= int(ch["checked_detailed"])
            for r in DEFS:
                obs[r] += hist.get(b - r, 0)
            checked += cd
            whole = m1_rates(b, lo, hi, s, c, bottom)
            if cd == hi - lo + 1:
                nfull += 1
                for a in tot:
                    for r in DEFS:
                        tot[a][r] += whole[r] * cd
                continue
            npart += 1
            pre = m1_rates(b, lo, lo + cd - 1, s, c, bottom)
            suf = m1_rates(b, hi - cd + 1, hi, s, c, bottom)
            for r in DEFS:
                tot["uniform"][r] += whole[r] * cd
                tot["prefix"][r] += pre[r] * cd
                tot["suffix"][r] += suf[r] * cd
        row = {"base": b, "chunks_with_histogram": nfull + npart, "full_chunks": nfull,
               "partial_chunks": npart, "checked_detailed_in_those_chunks": checked,
               "observed": obs, "m1_expected": tot}
        e2 = [tot[a][2] for a in tot]
        row["def2_poisson_p_le_observed"] = {a: poisson_cdf(obs[2], tot[a][2]) for a in tot}
        report[b] = row
        print(f"base {b}: {nfull} full + {npart} partial chunks, {checked:.4e} checked")
        for r in DEFS:
            print(f"   def {r}: observed {obs[r]:>10d}   M1 uniform {tot['uniform'][r]:14.2f}  "
                  f"prefix {tot['prefix'][r]:14.2f}  suffix {tot['suffix'][r]:14.2f}")
        print("   def-2 P(X<=obs):", {a: round(p, 3) for a, p in row["def2_poisson_p_le_observed"].items()},
              " expected range", round(min(e2), 2), "-", round(max(e2), 2))
    (HERE / "results/new_data_test.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
