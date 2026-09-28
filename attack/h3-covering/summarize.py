#!/usr/bin/env python3
"""Tabulate the H3 covering results (results/cover_b*_s*.jsonl, results/class_dp.json) as Markdown
and splice them into REPORT.md between the TABLES markers."""
import glob, json, re
from pathlib import Path
here = Path(__file__).resolve().parent
out = []
out.append("**Exhaustive DP (`cover.c`): all M coprime to b, nice-number lengths.** \"Fail\" means the image is a proper subset of the predicted set. Bases 11 and 16 have no nice-number interval; s = round(2b/5) is used there.")
out.append("")
out.append("| b | (s, c) | M tested | Largest M | Failures with M < b² | Failures overall | Smallest failing M | Largest covering M |")
out.append("|---:|---|---:|---:|---:|---:|---:|---:|")
main_rows = []
extra = {}
total_tested_below = total_fail_below = 0
for f in sorted(glob.glob(str(here / "results/cover_b*_s*.jsonl"))):
    rows = [json.loads(l) for l in open(f) if l.strip()]
    if not rows: continue
    b, s, c = rows[0]["b"], rows[0]["s"], rows[0]["c"]
    from math import gcd
    rows = [r for r in rows if gcd(r["M"], b) == 1]
    fails = [r for r in rows if not r["equal"]]
    below = [r for r in rows if r["M"] < b * b]
    fb = [r for r in below if not r["equal"]]
    rec = (b, s, c, len(rows), max(r["M"] for r in rows), len(below), len(fb), len(fails),
           min(r["M"] for r in fails) if fails else None, max(r["M"] for r in rows if r["equal"]))
    if f.endswith("_big.jsonl") or s != (json.load(open(here / "results/class_dp.json"))["rows"][0]["s"] if False else s):
        pass
    # decide main vs extra: main = the nice lengths file without suffix
    import sys
    sys.path.insert(0, str(here.parents[1] / "scripts"))
    from verify import candidate_intervals
    iv = candidate_intervals(b)
    s_nice = iv[0]["square_digits"] if iv else round(2 * b / 5)
    if s == s_nice and not f.endswith("_big.jsonl"):
        main_rows.append(rec); total_tested_below += len(below); total_fail_below += len(fb)
    else:
        extra.setdefault(b, []).append(rec)
for b, s, c, n, mx, nb, nfb, nf, first, lastok in sorted(main_rows):
    out.append(f"| {b} | ({s}, {c}) | {n} | {mx} | {nfb} of {nb} | {nf} | {first if first else '—'} | {lastok} |")
out.append("")
out.append(f"Totals below b²: {total_fail_below} failures in {total_tested_below} tested (b, M) pairs.")
out.append("")
out.append("**Other word lengths and larger moduli** (b = 10 and 12; s from the hypothesis range and beyond):")
out.append("")
out.append("| b | (s, c) | M tested | Largest M | Failures with M < b² | Failures overall | Smallest failing M | Largest covering M |")
out.append("|---:|---|---:|---:|---:|---:|---:|---:|")
for b in sorted(extra):
    for (bb, s, c, n, mx, nb, nfb, nf, first, lastok) in sorted(extra[b], key=lambda r: (r[1], r[4])):
        out.append(f"| {bb} | ({s}, {c}) | {n} | {mx} | {nfb} of {nb} | {nf} | {first if first else '—'} | {lastok} |")
out.append("")
cd = json.load(open(here / "results/class_dp.json"))["rows"]
fails = [r for r in cd if not r["equal"]]
bs1 = sorted(r["b"] for r in cd if r["M"] == r["b"] + 1)
bs2 = sorted(r["b"] for r in cd if r["M"] == r["b"] ** 2 - 1)
cond = sorted(r["b"] for r in cd if r["M"] == r["b"] + 1 and r["theorem_condition_holds"])
out.append(f"**Class DP (`class_dp.py`)**: M = b+1 for b = {bs1[0]}–{bs1[-1]} and M = b²−1 for b = {bs2[0]}–{bs2[-1]}: {len(fails)} failures. The sufficient condition of Theorem 1 holds for b in {{{', '.join(map(str, cond))}}} (and, by the Corollary, for every larger b).")
text = "\n".join(out)
rep = here / "REPORT.md"
src = rep.read_text()
src = re.sub(r"<!-- TABLES -->.*<!-- /TABLES -->", "<!-- TABLES -->\n" + text + "\n<!-- /TABLES -->", src, flags=re.S)
src = re.sub(r"<!-- EXH_SUMMARY -->.*?<!-- /EXH_SUMMARY -->", f"<!-- EXH_SUMMARY -->{total_fail_below} failures in {total_tested_below} tested (b, M) pairs<!-- /EXH_SUMMARY -->", src, flags=re.S)
rep.write_text(src)
print(text)
