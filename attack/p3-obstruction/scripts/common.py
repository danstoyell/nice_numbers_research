"""Shared loaders for the p3-obstruction analysis.

Observed near misses (deficiency <= 2):
  * bases 22-49: every one, from the public `bases.numbers` lists
    (results/near_misses.json, verified by extract_near_misses.py);
  * base 20: from critique/results/histogram-recompute.json (exhaustive);
  * base 50: the four numbers in the 32 chunks with published histograms.
Model expectations: critique/results/tail-validation.json (M1, bases 20-48),
results/new_data_test.json (bases 49 uniform, 50 prefix).
"""
import json
import sys

sys.dont_write_bytecode = True  # never write caches into critique/ or scripts/
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals, digits  # noqa: E402

BASES = [20, 22, 23, 24, 25, 27, 28, 29, 30, 32, 33, 34, 35, 37, 38, 39, 40,
         42, 43, 44, 45, 47, 48, 49, 50]


def load_events():
    """{base: [n, ...]} of all deficiency-1 and -2 near misses with their deficiency."""
    out = {b: [] for b in BASES}
    nm = json.loads((HERE / "results/near_misses.json").read_text())
    for row in nm["rows"]:
        b = row["base"]
        if b in out and b != 20:
            assert row["listed_complete_for_def_le_2"]
            out[b] = [(int(e["n"]), e["deficiency"]) for e in row["events"] if e["deficiency"] in (1, 2)]
    rec = json.loads((ROOT / "critique/results/histogram-recompute.json").read_text())
    for row in rec["rows"]:
        if row["base"] == 20:
            out[20] = [(int(e["n"]), 20 - e["distinct"]) for e in row["near_misses_at_most_two_missing"]
                       if 20 - e["distinct"] in (1, 2)]
    ch = json.loads((HERE / "data/chunks-50-numbers.json").read_text())
    out[50] = [(int(y["number"]), 50 - y["num_uniques"]) for x in ch for y in (x["numbers"] or [])
               if y["num_uniques"] >= 48]
    for b, evs in out.items():
        s, c = shape(b)
        for n, d in evs:
            sq, cu = digits(n * n, b), digits(n ** 3, b)
            assert len(sq) == s and len(cu) == c and b - len(set(sq + cu)) == d
    return out


def shape(b):
    iv, = candidate_intervals(b)
    return iv["square_digits"], iv["cube_digits"]


def intervals(b):
    """List of (lo, hi, weight) sub-intervals whose union is what was checked."""
    if b <= 48:
        snap = json.loads((ROOT / "critique/results/public-bases-2026-09-26.json").read_text())
        rec = next(r for r in snap["bases"] if r["id"] == b)
        lo, hi = int(rec["range_start"]), int(rec["range_end"]) - 1
        return [(lo, hi, hi - lo + 1)]
    chunks = json.loads((HERE / f"data/chunks-{b}.json").read_text())
    out = []
    for ch in chunks:
        if not ch["distribution"]:
            continue
        cd = sum(int(x["count"]) for x in ch["distribution"])
        lo, hi = int(ch["range_start"]), int(ch["range_end"]) - 1
        if b == 49:   # uniform-over-chunk bracket (best fit to deficiency 3-4 counts)
            out.append((lo, hi, cd))
        else:         # base 50: prefix bracket (fits deficiency 3-4 counts to 0.5%)
            out.append((lo, lo + cd - 1, cd))
    return out


def m1_expected(b, r=2):
    if b <= 48:
        t = json.loads((ROOT / "critique/results/tail-validation.json").read_text())
        row = next(x for x in t["rows"] if x["base"] == b)
        return next(x["m1_expected"] for x in row["tail"] if x["deficiency"] == r)
    nd = json.loads((HERE / "results/new_data_test.json").read_text())
    return nd[str(b)]["m1_expected"]["uniform" if b == 49 else "prefix"][str(r)]
