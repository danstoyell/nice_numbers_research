#!/usr/bin/env python3
"""Compare the measured distribution of the number of distinct values a middle-third digit
takes along a batch (H1's mid_domain_hist, batches of b^f roots) with two models:
  iid   : b^f independent uniform digits; P(D = d) = C(b,d) d! S(N,d) / b^N (Stirling numbers),
  poly  : the structure lemma's polynomial sequence with uniform random coefficients
          (from midpoly coeff, results/coeff.jsonl, where available).
Prints a Markdown table and writes results/domain_models.json."""
import json, math
from pathlib import Path
here = Path(__file__).resolve().parent
root = here.parents[1]

def stirling2_row(N, maxd):
    # S(N, d) for d = 0..maxd via the recurrence, exact integers
    S = [0] * (maxd + 1); S[0] = 1
    for n in range(1, N + 1):
        new = [0] * (maxd + 1)
        for d in range(1, min(n, maxd) + 1):
            new[d] = d * S[d] + S[d - 1]
        S = new
    return S

def iid_dist(b, N):
    S = stirling2_row(N, b)
    tot = b ** N
    return [math.comb(b, d) * math.factorial(d) * S[d] / tot for d in range(b + 1)]

rows = [json.loads(l) for l in (root / "attack/h1-domains/results/domains.jsonl").open() if l.startswith("{")]
out = []
print("| Case | f | Positions measured | Mean distinct: measured | iid exact | Total-variation distance measured vs iid | P(D ≤ b/2): measured | iid | Largest single-bin relative deviation (bins with iid prob > 1e-4) |")
print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for r in sorted(rows, key=lambda r: (r["f"], r["b"], r["K"])):
    if r["f"] != 1: continue
    b = r["b"]; N = b ** r["f"]
    h = r["mid_domain_hist"]; tot = sum(h)
    if not tot: continue
    meas = [x / tot for x in h]
    iid = iid_dist(b, N)
    mean_m = sum(d * meas[d] for d in range(b + 1)); mean_i = sum(d * iid[d] for d in range(b + 1))
    tv = 0.5 * sum(abs(meas[d] - iid[d]) for d in range(b + 1))
    half = b // 2
    pm = sum(meas[:half + 1]); pi = sum(iid[:half + 1])
    rel = max((abs(meas[d] - iid[d]) / iid[d], d) for d in range(b + 1) if iid[d] > 1e-4)
    name = {1: "nice", 2: "twice", 3: "thrice"}[r["K"]] + f"-{b}"
    out.append({"case": name, "b": b, "K": r["K"], "f": r["f"], "t": r["t"], "k": r["k"], "positions": tot, "mean_measured": mean_m, "mean_iid": mean_i, "tv_vs_iid": tv,
                "p_le_half_measured": pm, "p_le_half_iid": pi, "max_rel_dev": rel[0], "max_rel_dev_bin": rel[1], "measured": meas, "iid": iid})
    print(f"| {name} ({r['t']},{r['k']}) | {r['f']} | {tot:,} | {mean_m:.4f} | {mean_i:.4f} | {tv:.4f} | {pm:.2e} | {pi:.2e} | {rel[0]:.3f} at d={rel[1]} |")
(here / "results/domain_models.json").write_text(json.dumps(out, indent=1) + "\n")
