#!/usr/bin/env python3
"""Exactness tests of join-proto against brute force (join_proto verify):
survivor set and match count must equal a direct per-n evaluation of the
same certificate on small ranges, bases 20-64, several (t, k, p), ranges
aligned and unaligned to prefix blocks. Plus: base 10 finds 69.
Output: verify_proto.json."""
import json, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
import os
J = os.environ.get("JOIN_PROTO", "/private/tmp/nice-rust/target-proposal/release/join_proto")
cases = [(20, 58945, 160000, 3, 2, 0), (20, 58945, 160000, 3, 2, 1), (20, 58945, 160000, 2, 3, 1), (20, 60001, 150003, 2, 3, 1),
         (25, 3339797, 4339797, 4, 3, 1), (25, 5000123, 5700456, 3, 4, 2),
         (30, 300000000, 301000000, 5, 4, 2), (34, 12000000017, 12001000017, 5, 5, 2),
         (40, 3000000000000, 3000002000000, 6, 5, 2), (40, 3000000000000, 3000002000000, 7, 4, 2),
         (57, 30000000000000000000, 30000000000000300000, 10, 4, 1),
         (57, 20635899893042801193, 20635899893043101193, 9, 5, 1),
         (58, 150000000000000000123, 150000000000000200123, 10, 4, 2),
         (64, 50000000000000000000000, 50000000000000000200000, 11, 4, 2),
         # windows where the client's MSD filter lets candidates through (crosscheck.json)
         (57, 78920310198429586458, 78920310198429886458, 10, 4, 1),
         (57, 78920310198429586458, 78920310198429886458, 9, 5, 2),
         (58, 114041927169846138720, 114041927169846438720, 10, 4, 2),
         (60, 1573714731429953349518, 1573714731429953649518, 10, 4, 2),
         (62, 11098052380541596298900, 11098052380541596598900, 11, 4, 2),
         (64, 52125117810081128433988, 52125117810081128733988, 11, 4, 2)]
out = []
allok = True
r = json.loads(subprocess.run([J, "full", "10", "47", "100", "2", "1", "0"], capture_output=True, text=True, check=True).stdout)
out.append({"case": "base10 full", "hits": r["hits"]}); allok &= r["hits"] == [69]
print("base 10 hits", r["hits"])
for c in cases:
    r = json.loads(subprocess.run([J, "verify"] + [str(x) for x in c], capture_output=True, text=True, check=True).stdout)
    keep = {k: r[k] for k in ("base", "start", "end", "t", "k", "p", "exact", "join_survivors", "brute_survivors",
                              "join_matches", "out_of_range", "brute_matches", "tlay", "tops", "bottoms", "hits")}
    out.append(keep); allok &= r["exact"]
    print(keep, flush=True)
(HERE / "verify.json").write_text(json.dumps({"all_exact": allok, "cases": out}, indent=1) + "\n")
print("ALL EXACT" if allok else "MISMATCH")
