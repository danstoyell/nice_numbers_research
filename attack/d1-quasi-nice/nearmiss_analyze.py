#!/usr/bin/env python3
"""Compare observed deficiency-1 and -2 counts (all n in the band) with the M1(2,3) model
(coupled to the digit-sum identity, and uncoupled). Observed: brute.py histograms (bases <= 18)
and nm12.c chunk histograms (results/nm_b*/). Model: results/nearmiss_model_*.jsonl.
Writes results/nearmiss_summary.json and prints a markdown table.
"""
import glob
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"


def observed():
    obs = {}
    for f in ["brute_2_14.jsonl", "brute_15_18.jsonl"]:
        for line in open(R / f):
            r = json.loads(line)
            if r.get("band") is None and "N" not in r:
                continue
            h = r["deficiency_hist"]
            obs[r["b"]] = {"N": r["N"], "d": [h.get(str(k), 0) for k in range(3)], "source": "brute.py"}
    for d in sorted(glob.glob(str(R / "nm_b*"))):
        parts = [json.loads(open(f).read()) for f in glob.glob(d + "/chunk_*.json")]
        if not parts:
            continue
        nch = parts[0]["nchunks"]
        if len({p["chunk"] for p in parts}) != nch:
            continue
        b = parts[0]["b"]
        hist = [sum(p["hist"][k] for p in parts) for k in range(3)]
        N = parts[0]["hi"] - parts[0]["lo"] + 1
        assert sum(sum(p["hist"]) for p in parts) == N
        obs[b] = {"N": N, "d": hist, "source": "nm12.c"}
    return obs


def main():
    obs = observed()
    mod = {}
    for f in sorted(glob.glob(str(R / "nearmiss_model_*.jsonl"))):
        for line in open(f):
            r = json.loads(line)
            mod[r["b"]] = r
    rows = []
    print("| b | N | def-1 obs | def-1 model (coupled) | def-1 uncoupled | z | def-2 obs | def-2 model (coupled) | def-2 uncoupled | z |")
    print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    pool = {1: [0, 0.0, 0.0, 0.0], 2: [0, 0.0, 0.0, 0.0]}
    for b in sorted(obs):
        if b not in mod:
            continue
        o, m = obs[b], mod[b]
        row = {"b": b, "N": o["N"], "source": o["source"], "model_method": m["method"]}
        cells = []
        for r in (1, 2):
            e, eu, se = m["coupled"][r], m["uncoupled"][r], m["coupled_se"][r]
            z = (o["d"][r] - e) / math.sqrt(e + se ** 2) if e > 0 else float("nan")
            row[f"def{r}"] = {"obs": o["d"][r], "coupled": e, "coupled_se": se, "uncoupled": eu, "z": z}
            cells += [f"{o['d'][r]}", f"{e:.1f} ± {se:.1f}", f"{eu:.1f}", f"{z:+.2f}"]
            if b >= 12:
                pool[r][0] += o["d"][r]
                pool[r][1] += e
                pool[r][2] += se ** 2
                pool[r][3] += eu
        rows.append(row)
        print(f"| {b} | {o['N']:.3g} | " + " | ".join(cells) + " |")
    summ = {"rows": rows, "pooled_b12plus": {}}
    for r in (1, 2):
        O, E, V, EU = pool[r]
        z = (O - E) / math.sqrt(E + V)
        summ["pooled_b12plus"][f"def{r}"] = {"obs": O, "coupled": E, "model_se": math.sqrt(V), "ratio": O / E,
                                             "z": z, "uncoupled": EU, "ratio_uncoupled": O / EU}
        print(f"pooled b>=12 deficiency {r}: obs {O}, coupled model {E:.1f} (MC se {math.sqrt(V):.1f}), "
              f"ratio {O / E:.4f}, z {z:+.2f}; uncoupled {EU:.1f}, ratio {O / EU:.4f}")
    json.dump(summ, open(R / "nearmiss_summary.json", "w"), indent=1)


if __name__ == "__main__":
    main()
