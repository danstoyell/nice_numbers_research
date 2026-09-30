#!/usr/bin/env python3
"""Measure the client's operation counts per n at bases 57-64 by exact sampling.

For each base and client configuration, client_count(256) runs the exact
client pipeline on NSAMP stratified random chunks of the base's candidate
interval (one uniformly random aligned chunk per equal stratum) and counts
MSD analyses, stride visits and full checks (full checks counted, not run).
Totals are the per-chunk means times the number of chunks in the interval.

Configurations (see REPORT section 1):
  cpu    : CPU client on 1e14 fields -> chunk 1e9 (chunk_multiple 1000), floor 8000
  gpu62k : GPU pipeline, chunk 1e6, MSD floor 62,500 (controller minimum)
  gpu250k: GPU pipeline, chunk 1e6, floor 250,000 (controller seed)
  gpu500k: GPU pipeline, chunk 1e6, floor 500,000 (controller maximum)
Validation bases (34, 38, 40) use the testbed's CPU chunk 1e6 so the sampled
estimate can be compared with the exact full-interval run.

Usage: python3 sample_client.py [bases...]      Output: client_sample.json (merged)
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
from verify import candidate_intervals  # noqa: E402

OUT = HERE / "client_sample.json"
THREADS = 2
CONFIGS = {
    "cpu": (10 ** 9, 8000, 300),
    "cpu1e6": (10 ** 6, 8000, 20000),
    "gpu62k": (10 ** 6, 62500, 20000),
    "gpu250k": (10 ** 6, 250000, 20000),
    "gpu500k": (10 ** 6, 500000, 20000),
}


def run(b, cfg, seed=1):
    chunk, floor, ns = CONFIGS[cfg]
    iv, = candidate_intervals(b)
    lo, hix = iv["lo"], iv["hi"] + 1
    binp = HERE / ("client_count256" if b > 40 else "client_count")
    res = subprocess.run([str(binp), "sample", str(b), "1", str(lo), str(hix), str(lo), str(chunk), str(floor),
                          str(THREADS), "0", str(ns), str(seed)], capture_output=True, text=True, check=True)
    d = json.loads(res.stdout)
    N = hix - lo
    scale = N / (d["chunks"] * chunk)          # chunks in interval / sampled chunks
    mean = d["sum_ops"] / d["chunks"]
    var = max(d["sum_ops2"] / d["chunks"] - mean * mean, 0.0)
    se_rel = math.sqrt(var / d["chunks"]) / mean if mean else float("nan")
    per_n = {k: int(d[k]) / (d["chunks"] * chunk) for k in ("analyses", "visits", "mask_rejects", "full_checks", "leaf_n")}
    return {"base": b, "config": cfg, "chunk": chunk, "floor": floor, "nsamples": d["chunks"], "N": N,
            "per_n": per_n, "ops_per_n": per_n["analyses"] + per_n["visits"] + per_n["full_checks"],
            "total_ops": (int(d["analyses"]) + int(d["visits"]) + int(d["full_checks"])) * scale,
            "log10_total_ops": math.log10((int(d["analyses"]) + int(d["visits"]) + int(d["full_checks"])) * scale),
            "rel_se_ops": se_rel, "cert_per_visit": d["cert_per_visit"], "doms_per_visit": d["doms_per_visit"],
            "stride_residues": d["stride_residues"], "stride_modulus": d["stride_modulus"],
            "msd_digits_per_analysis": int(d["msd_digits"]) / max(int(d["analyses"]), 1),
            "hall_calls_per_analysis": int(d["hall_calls"]) / max(int(d["analyses"]), 1)}


def main():
    bases = [int(x) for x in sys.argv[1:]] or [57, 58, 60, 62, 64]
    db = json.loads(OUT.read_text()) if OUT.exists() else {}
    for b in bases:
        cfgs = ["cpu1e6"] if b <= 40 else ["cpu", "gpu62k", "gpu250k", "gpu500k"]
        for cfg in cfgs:
            key = f"{b}:{cfg}"
            if key in db:
                continue
            r = run(b, cfg)
            db[key] = r
            OUT.write_text(json.dumps(db, indent=1) + "\n")
            pn = r["per_n"]
            print(f"b={b} {cfg}: ops/n={r['ops_per_n']:.3e} (analyses {pn['analyses']:.2e}, visits {pn['visits']:.2e}, "
                  f"full {pn['full_checks']:.2e}, surviving {pn['leaf_n']:.3f}) total 10^{r['log10_total_ops']:.2f} "
                  f"+-{100 * r['rel_se_ops']:.1f}% cert/visit {r['cert_per_visit']:.1f}", flush=True)


if __name__ == "__main__":
    main()
