#!/usr/bin/env python3
"""Collect (1,2)-nice exact counts and model expectations; per-base and pooled comparison.

Inputs (all in results/):
  qn12_small.jsonl                 C search, bases 6-21 (single chunk each)
  qn12_b24_full.jsonl, qn12_b26_full.jsonl
  b<B>_t*_j*_ap*/chunk_*.json      chunked C searches (29, 30)
  model_exact_*.jsonl              exhaustive numpy model sums (bases <= 21)
  model_mc_*.jsonl                 Monte Carlo model sums (bases >= 24)
  nearmiss_obs.json, nearmiss_model_*.jsonl   deficiency-1/2 counts and model
Outputs: results/hits_by_base.json, results/summary.json, printed markdown tables.
"""
import glob
import json
import math
from pathlib import Path

from scipy import stats

HERE = Path(__file__).resolve().parent
R = HERE / "results"
MODELS = ["naive", "crude", "M0", "M1(0,0)", "M1(1,1)", "M1(1,2)", "M1(2,2)", "M1(2,3)", "M1(3,3)", "M1(3,4)",
          "M1(4,5)", "M1e"]


def log_fact(k):
    return math.lgamma(k + 1)


def load_search():
    rows = {}
    for f in [R / "qn12_small.jsonl", R / "qn12_b24_full.jsonl", R / "qn12_b26_full.jsonl"]:
        for line in open(f):
            r = json.loads(line)
            if "hits" in r:
                rows[r["b"]] = {"b": r["b"], "s": r["s"], "c": r["c"], "lo": r["lo"], "hi": r["hi"], "N": r["N"],
                                "roots": r["roots"], "hits": r["hits"], "witnesses": r["witnesses"],
                                "K": dict(r["K"]), "chunks": "1/1", "complete": True, "leaves": r["leaves"],
                                "params": f"t{r['t']}_j{r['j']}_ap{r['AP']}"}
    for d in sorted(glob.glob(str(R / "b*_t*_j*_ap*"))):
        files = sorted(glob.glob(d + "/chunk_*.json"))
        if not files:
            continue
        parts = [json.loads(open(f).read()) for f in files]
        nch = parts[0]["nchunks"]
        b = parts[0]["b"]
        got = sorted({p["chunk"] for p in parts})
        K = {}
        for p in parts:
            for k, v in p["K"].items():
                K[k] = K.get(k, 0) + v
        w = sorted(x for p in parts for x in p["witnesses"])
        row = {"b": b, "s": parts[0]["s"], "c": parts[0]["c"], "lo": parts[0]["lo"], "hi": parts[0]["hi"],
               "N": parts[0]["N"], "roots": parts[0]["roots"], "hits": sum(p["hits"] for p in parts),
               "witnesses": w, "K": K, "chunks": f"{len(got)}/{nch}", "complete": len(got) == nch,
               "leaves": sum(p["leaves"] for p in parts), "params": Path(d).name}
        if b in rows and rows[b]["complete"]:
            if not row["complete"]:
                continue
            # two complete runs of one base (cross-check): must agree; merge the K grids
            old = rows[b]
            assert old["hits"] == row["hits"] and old["witnesses"] == row["witnesses"], b
            for k, v in row["K"].items():
                assert old["K"].get(k, v) == v, (b, k)
                old["K"].setdefault(k, v)
            old["params"] += "+" + row["params"]
            continue
        rows[b] = row
    return rows


def model_from_K(b, c, K, A, J):
    m = c - A - J
    k = K.get(f"{A},{J}")
    if k is None:
        return None
    return k * math.exp(math.log(b - 1) + log_fact(m) - m * math.log(b))


def load_models():
    out = {}
    for f in sorted(glob.glob(str(R / "model_*.jsonl"))):
        for line in open(f):
            r = json.loads(line)
            out[r["b"]] = r
    return out


def poisson_ci(k, conf=0.95):
    a = 1 - conf
    lo = 0.0 if k == 0 else stats.chi2.ppf(a / 2, 2 * k) / 2
    hi = stats.chi2.ppf(1 - a / 2, 2 * k + 2) / 2
    return lo, hi


def p_two(k, mu):
    if mu <= 0:
        return 1.0 if k == 0 else 0.0
    return min(1.0, 2 * min(stats.poisson.cdf(k, mu), stats.poisson.sf(k - 1, mu)))


def build_table():
    search = load_search()
    models = load_models()
    table = []
    for b in sorted(search):
        r = search[b]
        mi = models.get(b, {})
        mm, se = mi.get("models", {}), mi.get("se", {})
        pn = math.exp(log_fact(b) - b * math.log(b))
        row = {"b": b, "s": r["s"], "c": r["c"], "N": r["N"], "roots": r["roots"], "obs": r["hits"],
               "chunks": r["chunks"], "complete": r["complete"], "search_params": r["params"],
               "model_method": mi.get("method"), "naive": r["N"] * pn, "crude": r["N"] * r["roots"] * pn}
        for k in MODELS[2:]:
            if k in mm:
                row[k] = mm[k]
            if k in se:
                row[k + "_se"] = se[k]
        exhaustive = mi.get("method") == "exhaustive"
        for (A, J) in [(2, 2), (2, 3), (3, 3), (3, 4), (4, 5)]:
            v = model_from_K(b, r["c"], r["K"], A, J)
            if v is None:
                continue
            key = f"M1({A},{J})"
            if exhaustive:
                if r["c"] - A - J >= 6:  # class factor b-1 exact to b^-6; must agree with numpy
                    assert abs(row[key] - v) <= 1e-6 * max(1.0, v), (b, key, row[key], v)
            else:
                if key in row:
                    row[key + "_mc"] = row[key]
                    row[key + "_mc_z"] = (row[key] - v) / row[key + "_se"] if row.get(key + "_se") else None
                row[key] = v
                row[key + "_se"] = 0.0
        if r["roots"] == 0:
            for k in MODELS[2:]:
                row[k] = 0.0
        lo, hi = poisson_ci(r["hits"])
        row["obs_ci95"] = [lo, hi]
        table.append(row)
    return search, table


def pooled(table, key, bmin=0, bmax=99):
    rows = [t for t in table if bmin <= t["b"] <= bmax and t.get(key) is not None and t["complete"]]
    O = sum(t["obs"] for t in rows)
    E = sum(t[key] for t in rows)
    return {"model": key, "bases": [t["b"] for t in rows], "obs": O, "exp": E, "ratio": O / E if E else None,
            "z": (O - E) / math.sqrt(E) if E else None, "p_two_sided": p_two(O, E),
            "ratio_ci95": [x / E for x in poisson_ci(O)] if E else None}


def main():
    search, table = build_table()
    json.dump({str(b): {"hits": r["hits"], "witnesses": r["witnesses"], "complete": r["complete"]}
               for b, r in sorted(search.items())}, open(R / "hits_by_base.json", "w"))
    print("| b | (s,c) | N | roots | naive | crude | M0 | M1(0,0) | M1(1,1) | M1(2,3) | M1(3,4) | M1e | obs | 95% CI | z(M1(2,3)) | p |")
    print("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|")
    for t in table:
        f = lambda k: f"{t[k]:.2f}" if t.get(k) is not None else "-"
        e = t.get("M1(2,3)")
        z = (t["obs"] - e) / math.sqrt(e) if e else float("nan")
        print(f"| {t['b']} | ({t['s']},{t['c']}) | {t['N']:.3g} | {t['roots']} | {f('naive')} | {f('crude')} | {f('M0')} | "
              f"{f('M1(0,0)')} | {f('M1(1,1)')} | {f('M1(2,3)')} | {f('M1(3,4)')} | {f('M1e')} | {t['obs']} | "
              f"{t['obs_ci95'][0]:.1f}-{t['obs_ci95'][1]:.1f} | {z:+.2f} | {p_two(t['obs'], e) if e else float('nan'):.3f} |")
    summ = {"table": table, "pooled": {}}
    for rng_name, (lo, hi) in {"all": (0, 99), "6-21 (first pass)": (6, 21), "17+": (17, 99), "24+ (new)": (24, 99)}.items():
        summ["pooled"][rng_name] = [pooled(table, k, lo, hi) for k in MODELS]
        print(f"\npooled {rng_name}:")
        for p in summ["pooled"][rng_name]:
            if p["exp"]:
                print(f"  {p['model']:9s} obs {p['obs']:5d}  exp {p['exp']:9.2f}  ratio {p['ratio']:.3f} "
                      f"[{p['ratio_ci95'][0]:.3f},{p['ratio_ci95'][1]:.3f}]  z {p['z']:+.2f}  p {p['p_two_sided']:.3g}")
    json.dump(summ, open(R / "summary.json", "w"), indent=1)


if __name__ == "__main__":
    main()
