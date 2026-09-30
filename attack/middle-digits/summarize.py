#!/usr/bin/env python3
"""Markdown tables for REPORT.md from results/*.json*; splices them between the markers."""
import json, math, re, subprocess, sys
from pathlib import Path
here = Path(__file__).resolve().parent
root = here.parents[1]
out = {}

# T1: coefficient regimes and domain models per position (b = 30, L = 6)
rows = [json.loads(l) for l in (here / "results/coeff.jsonl").open() if l.strip()]
t = ["| (t, k) | P | Terms active | Range of θ₂ | Max deviation of x₀ | of θ₁ | Mean distinct values: measured | polynomial model | iid | TV distance measured vs polynomial | vs iid | P(D ≤ 3): measured | polynomial |",
     "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for r in rows:
    m = r["mean_distinct"]; tv = r["tv_measured_vs"]; lo = r["frac_domain_le3"]
    P = r["P"]; k = r["k"]; f = r["f"]; L = r["L"]
    terms = "linear" + (", quadratic" if P + 1 > 2 * k else "") + (", cubic" if P + 1 > 3 * k else "")
    t.append(f"| ({r['t']}, {k}) | {P} | {terms} | {r['th2_natural_range']:.3g} | {r['maxdev_x0_64bins']:.3f} | {r['maxdev_th1_64bins']:.3f} | {m['measured']:.3f} | {m['poly_exact_th2']:.3f} | {m['iid_exact']:.3f} | {tv['poly_exact_th2']:.4f} | {tv['iid']:.4f} | {lo['measured']:.1e} | {lo['poly_exact_th2']:.1e} |")
t.append("")
t.append(f"Sampling noise for the 64-bin deviations: {rows[0]['iid_noise_64bins']:.3f}. Samples per row: {rows[0]['samples']:,} batches of {rows[0]['b']**rows[0]['f']} roots.")
out["COEFF"] = "\n".join(t)

# T2: H1 aggregate comparison
out["H1"] = subprocess.run([sys.executable, str(here / "models.py")], capture_output=True, text=True, check=True).stdout.strip()

# T3: degenerate tail from H1
h1 = [json.loads(l) for l in (root / "attack/h1-domains/results/domains.jsonl").open() if l.startswith("{")]
t = ["| Case | b | (batch, position) pairs | P(D = 1) | P(D ≤ 2) | P(D ≤ 3) | Proposition A′ bound 6/b | iid P(D ≤ 3) |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
def iid_le(b, N, s):
    S = [0] * (s + 1); S[0] = 1
    for n in range(1, N + 1):
        new = [0] * (s + 1)
        for d in range(1, min(n, s) + 1): new[d] = d * S[d] + S[d - 1]
        S = new
    return sum(math.comb(b, d) * math.factorial(d) * S[d] for d in range(1, s + 1)) / b ** N
for r in sorted(h1, key=lambda r: (r["b"], r["K"])):
    if r["f"] != 1: continue
    b = r["b"]; h = r["mid_domain_hist"]; tot = sum(h)
    name = {1: "nice", 2: "twice", 3: "thrice"}[r["K"]] + f"-{b} ({r['t']},{r['k']})"
    t.append(f"| {name} | {b} | {tot:,} | {h[1]/tot:.1e} | {sum(h[1:3])/tot:.1e} | {sum(h[1:4])/tot:.1e} | {6/b:.2f} | {iid_le(b, b, 3):.1e} |")
out["TAIL"] = "\n".join(t)

# T4: sensitivity
s = json.load(open(here / "results/sens.json"))
L = s["L"]
t = [f"Base {s['b']}, roots of {L} digits, {s['samples']:,} random changes of one digit; a random new digit would change each position with probability {s['expected_random']:.4f}. A change at root position i reaches the square's positions i … i+L and the cube's positions i … i+2L (the size of 2nδ·b^i and 3n²δ·b^i); above that the change is smooth.", "",
     "| Changed root digit i | Square: position i | i+1 | mean over i+2 … i+L−2 | i+L−1 | i+L | Cube: position i | i+1 | mean over i+2 … i+2L−2 | i+2L−1 | i+2L |", "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for row in s["rows"]:
    i = row["flipped_digit"]; sq = row["square"]; cu = row["cube"]
    msq = sq[i+2:i+L-1]; mcu = cu[i+2:i+2*L-1]
    t.append(f"| {i} | {sq[i]:.2f} | {sq[i+1]:.2f} | {sum(msq)/len(msq):.3f} | {sq[i+L-1]:.2f} | {sq[i+L]:.2f} | {cu[i]:.2f} | {cu[i+1]:.2f} | {sum(mcu)/len(mcu):.3f} | {cu[i+2*L-1]:.2f} | {cu[i+2*L]:.2f} |")
out["SENS"] = "\n".join(t)

# T5: batch discrepancy
t = ["| Fixed top digits t | Prefix | Batch size N | Heuristic Weyl scale N^(−1/4) | iid noise | Max deviation of a digit frequency from 1/b over the middle third (positions 6–11) | Bottom positions 0–5 | Top three positions |", "|---:|---:|---:|---:|---:|---:|---|---|"]
for l in (here / "results/batch.jsonl").open():
    r = json.loads(l); rows_ = {x["P"]: x for x in r["rows"]}
    mid = max(rows_[P]["maxdev"] for P in range(6, 12)); bot = ", ".join(f"{rows_[P]['maxdev']:.4f}" for P in range(0, 6)); top = ", ".join(f"{rows_[P]['maxdev']:.3f} ({rows_[P]['distinct']} values)" for P in range(15, 18))
    t.append(f"| {r['t']} | {r['prefix']} | {r['N']:,} | {r['weyl_bound_N^-1/4']:.4f} | {r['iid_noise']:.6f} | {mid:.4f} | {bot} | {top} |")
out["BATCH"] = "\n".join(t)

rep = here / "REPORT.md"
src = rep.read_text()
for key, text in out.items():
    src, n = re.subn(rf"<!-- {key} -->.*?<!-- /{key} -->", f"<!-- {key} -->\n{text}\n<!-- /{key} -->", src, flags=re.S)
    assert n == 1, key
rep.write_text(src)
print("tables inserted:", ", ".join(out))
