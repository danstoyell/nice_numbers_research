#!/usr/bin/env python3
"""Cross-check client_count.c against the unmodified client library.

crosscheck/ (Rust, depends on nice-client/common by path) runs the client's
own get_valid_ranges_recursive_masked, StrideTable and seeded nice check;
client_count(256) is the C reimplementation. Leaves, numbers in leaves,
stride visits, cross-end rejects, full checks, mean certificate size and
hits must agree exactly. Output: crosscheck.json.
"""
import json, subprocess, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
RUST = "/private/tmp/nice-rust/target/release/d5_crosscheck"
KEYS = ["stride_residues", "leaves", "leaf_n", "visits", "mask_rejects", "full_checks", "cert_per_visit"]
import sys; sys.path.insert(0, str(HERE.parents[1] / "scripts"))
from verify import candidate_intervals
rng = random.Random(5)
cases = []
for b in (25, 30, 34, 40, 57, 58, 60, 62, 64):
    iv, = candidate_intervals(b)
    for floor, chunk in ((8000, 10**6), (62500, 10**6), (250000, 10**6)):
        w = min(10**7, iv["hi"] - iv["lo"])
        # prefer a window where something survives the MSD filter
        binp = str(HERE / ("client_count256" if b > 40 else "client_count"))
        for _ in range(200):
            s = rng.randrange(iv["lo"], iv["hi"] - w + 1)
            c = json.loads(subprocess.run([binp, "range", str(b), "1", str(s), str(s + w), str(s), str(chunk), str(floor), "1", "0"],
                                          capture_output=True, text=True, check=True).stdout)
            if c["visits"] > 0:
                break
        cases.append((b, floor, chunk, s, s + w))
out = []
ok = True
for b, floor, chunk, s, e in cases:
    r = json.loads(subprocess.run([RUST, str(b), str(floor), str(chunk), str(s), str(e)], capture_output=True, text=True, check=True).stdout)
    binp = str(HERE / ("client_count256" if b > 40 else "client_count"))
    c = json.loads(subprocess.run([binp, "range", str(b), "1", str(s), str(e), str(s), str(chunk), str(floor), "1", "1"], capture_output=True, text=True, check=True).stdout)
    same = all(abs(float(r[k]) - float(c[k])) < 1e-3 for k in KEYS) and r["hits"] == c["solutions"]
    ok &= same
    out.append({"base": b, "floor": floor, "chunk": chunk, "start": s, "end": e, "match": same,
                "rust": {k: r[k] for k in KEYS}, "c": {k: c[k] for k in KEYS}})
    print(b, floor, "match" if same else "MISMATCH", {k: r[k] for k in KEYS})
(HERE / "crosscheck.json").write_text(json.dumps({"all_match": ok, "cases": out}, indent=1) + "\n")
print("ALL MATCH" if ok else "SOME MISMATCH")
