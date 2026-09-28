#!/usr/bin/env python3
"""Tabulate the H1 oracle results (results/domains.jsonl) as Markdown."""
import json, sys
from pathlib import Path
here = Path(__file__).resolve().parent
rows = [json.loads(l) for l in (here / "results/domains.jsonl").open() if l.startswith("{")]
name = {1: "nice", 2: "twice", 3: "thrice"}
print("| Case | f | (t, k) | Batches | End-check rejected | Surviving | Hall rejected, no middle | Hall rejected, with middle | Extra batches | Extra, root-weighted | Middle domain / b | Hits | Sound |")
print("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
for r in sorted(rows, key=lambda r: (r["K"], r["b"], r["f"], -r["t"])):
    extra = r["hall_rejected_all"] - r["hall_rejected_nomid"]
    rextra = (r["roots_hall_rejected_all"] - r["roots_hall_rejected_nomid"]) / r["roots"]
    print(f"| {name[r['K']]}-{r['b']} | {r['f']} | ({r['t']}, {r['k']}) | {r['batches']:,} | {r['end_rejected']:,} | {r['surviving']:,} | "
          f"{r['hall_rejected_nomid']:,} | {r['hall_rejected_all']:,} | {extra:,} | {rextra:.1e} | {r['mid_domain_mean']/r['b']:.3f} | "
          f"{r['hits']} | {'yes' if r['hits_in_rejected_all']==0 and r['hits_in_rejected_nomid']==0 else 'NO'} |")
print()
print("Domain-size distribution of the cube's middle-third positions in surviving batches (fraction of positions with domain size = b, i.e. the whole alphabet):")
print()
print("| Case | f | Batch size b^f | Positions | Mean domain / b | Share with full alphabet | Smallest domain seen |")
print("|---|---:|---:|---:|---:|---:|---:|")
for r in sorted(rows, key=lambda r: (r["K"], r["b"], r["f"], -r["t"])):
    h = r["mid_domain_hist"]; tot = sum(h)
    if not tot: continue
    smallest = next(i for i, v in enumerate(h) if v)
    print(f"| {name[r['K']]}-{r['b']} | {r['f']} | {r['b']**r['f']:,} | {tot:,} | {r['mid_domain_mean']/r['b']:.3f} | {h[r['b']]/tot:.4f} | {smallest} |")
