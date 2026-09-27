#!/usr/bin/env python3
"""Extract every public number with <= 2 missing digits (bases 10-49) from the
current `bases` API table (field `numbers`), verify each one exactly, check the
list against the histogram bins, and write near_misses.json.

Usage: python3 attack/p3-obstruction/scripts/extract_near_misses.py
Input:  attack/p3-obstruction/data/bases-now.json
        (https://data.nicenumbers.net/bases?select=*&order=id.asc, fetched 2026-09-26)
"""
import hashlib
import json
import sys

sys.dont_write_bytecode = True  # never write caches into critique/ or scripts/
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals, digits  # noqa: E402


def main():
    raw = (HERE / "data/bases-now.json").read_bytes()
    bases = json.loads(raw)
    out = {"source": "https://data.nicenumbers.net/bases?select=*&order=id.asc",
           "fetched": "2026-09-26", "sha256": hashlib.sha256(raw).hexdigest(), "rows": []}
    for rec in bases:
        b = rec["id"]
        if not rec["distribution"]:
            continue
        hist = {x["num_uniques"]: int(x["count"]) for x in rec["distribution"]}
        ivs = candidate_intervals(b)
        assert len(ivs) == 1
        iv = ivs[0]
        s, c = iv["square_digits"], iv["cube_digits"]
        listed = [x for x in rec["numbers"] if x["num_uniques"] >= b - 2]
        by_def = Counter(b - x["num_uniques"] for x in listed)
        complete = all(by_def.get(r, 0) == hist.get(b - r, 0) for r in (0, 1, 2))
        events = []
        for x in listed:
            n = int(x["number"])
            assert iv["lo"] <= n <= iv["hi"]
            sq, cu = digits(n * n, b), digits(n ** 3, b)
            assert len(sq) == s and len(cu) == c
            cnt = Counter(sq + cu)
            assert len(cnt) == x["num_uniques"], (b, n)
            events.append({"n": str(n), "deficiency": b - len(cnt),
                           "missing": [d for d in range(b) if d not in cnt],
                           "repeated": {str(d): k for d, k in sorted(cnt.items()) if k > 1},
                           "square_digits_msd_first": sq, "cube_digits_msd_first": cu})
        events.sort(key=lambda e: int(e["n"]))
        out["rows"].append({"base": b, "lo": iv["lo"], "hi": iv["hi"], "s": s, "c": c,
                            "checked_detailed": int(rec["checked_detailed"]),
                            "range_size": int(rec["range_size"]),
                            "hist_def": {r: hist.get(b - r, 0) for r in range(0, 4)},
                            "listed_complete_for_def_le_2": complete, "events": events})
        print(b, "def0/1/2 hist", [hist.get(b - r, 0) for r in (0, 1, 2)],
              "listed", [by_def.get(r, 0) for r in (0, 1, 2)], "complete" if complete else "INCOMPLETE")
    (HERE / "results/near_misses.json").write_text(json.dumps(out, indent=0) + "\n")


if __name__ == "__main__":
    main()
