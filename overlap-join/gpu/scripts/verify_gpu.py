#!/usr/bin/env python3
"""Exactness of the GPU join against the CPU prototype (and brute force on the
small ranges), on the 21 cases of attack/d5-client-join/verify_proto.py:
base 10 (must find 69) plus 20 windows at bases 20-64, several (t, k, p),
aligned and unaligned, six of them windows where the client's MSD filter
lets candidates through. Per case: GPU survivor set == CPU survivor set,
GPU match count == CPU match count, every n rebuilt on the device (check
kernel in probe mode) == the survivor set, GPU hits == CPU hits, every hit
re-verified with exact integer arithmetic (in Rust, and again here in Python).
Output: results/verify_gpu.json. Any mismatch is reported as a failure."""
import json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
B = os.environ.get("JOIN_GPU", "/private/tmp/nice-rust/target-gpu/release/overlap_join_gpu")
OUT = HERE / "results" / os.environ.get("VERIFY_OUT", "verify_gpu.json")

cases = [(10, 47, 100, 2, 1, 0),
         (20, 58945, 160000, 3, 2, 0), (20, 58945, 160000, 3, 2, 1), (20, 58945, 160000, 2, 3, 1), (20, 60001, 150003, 2, 3, 1),
         (25, 3339797, 4339797, 4, 3, 1), (25, 5000123, 5700456, 3, 4, 2),
         (30, 300000000, 301000000, 5, 4, 2), (34, 12000000017, 12001000017, 5, 5, 2),
         (40, 3000000000000, 3000002000000, 6, 5, 2), (40, 3000000000000, 3000002000000, 7, 4, 2),
         (57, 30000000000000000000, 30000000000000300000, 10, 4, 1),
         (57, 20635899893042801193, 20635899893043101193, 9, 5, 1),
         (58, 150000000000000000123, 150000000000000200123, 10, 4, 2),
         (64, 50000000000000000000000, 50000000000000000200000, 11, 4, 2),
         (57, 78920310198429586458, 78920310198429886458, 10, 4, 1),
         (57, 78920310198429586458, 78920310198429886458, 9, 5, 2),
         (58, 114041927169846138720, 114041927169846438720, 10, 4, 2),
         (60, 1573714731429953349518, 1573714731429953649518, 10, 4, 2),
         (62, 11098052380541596298900, 11098052380541596598900, 11, 4, 2),
         (64, 52125117810081128433988, 52125117810081128733988, 11, 4, 2)]


def exact_nice(n, b):
    d = []
    for x in (n * n, n * n * n):
        while x:
            d.append(x % b)
            x //= b
    return sorted(d) == list(range(b))


out, allok = [], True
for c in cases:
    r = subprocess.run([B, "verify"] + [str(x) for x in c], capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED TO RUN", c, r.stderr[-2000:], flush=True)
        out.append({"case": c, "error": r.stderr[-2000:]})
        allok = False
        continue
    d = json.loads(r.stdout)
    d["hits_python_exact"] = all(exact_nice(int(h), c[0]) for h in d["gpu_hits"])
    ok = d["exact"] and d["hits_python_exact"]
    if c[0] == 10:
        ok &= d["gpu_hits"] == ["69"]
        d["base10_finds_69"] = d["gpu_hits"] == ["69"]
    d["pass"] = ok
    allok &= ok
    out.append(d)
    print(("PASS " if ok else "FAIL "), {k: d[k] for k in ("base", "start", "t", "k", "p", "parts", "gpu_survivors", "cpu_survivors",
                                                        "gpu_matches", "cpu_matches", "gpu_hits") if k in d},
          "brute" if "brute_equal" in d else "", flush=True)
OUT.write_text(json.dumps({"all_pass": allok, "binary": B, "cases": out}, indent=1) + "\n")
print("ALL PASS" if allok else "FAILURES PRESENT")
sys.exit(0 if allok else 1)
