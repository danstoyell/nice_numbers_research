#!/usr/bin/env python3
"""Pre-registered triage: do exact k-nice counts fall below the random-digit
model as the per-candidate probability p falls?

Inputs: the critique's searched rows (critique/results/{twice,thrice}-nice.json)
plus this folder's runs (results/run_k{k}_b{b}.json; thrice 16 comes from both).
Model: M0 (critique model, exact) as primary; M1e (exact-edge Monte Carlo,
results/model.json) as a secondary check.

Trend: obs_i ~ Poisson(E_i * exp(alpha + beta * (x_i - xbar))), x = log10 p_i.
An obstruction that bites harder on rarer events predicts beta > 0 (the ratio
obs/exp shrinks as p shrinks). Fit by maximum likelihood; 95% intervals from
the profile likelihood.

Usage: python3 analyze.py   # writes results/analysis.json and prints tables
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from model import m0  # noqa: E402


def pois_cdf(k, lam):
    if k < 0:
        return 0.0
    if lam == 0:
        return 1.0
    return min(1.0, sum(math.exp(i * math.log(lam) - lam - math.lgamma(i + 1)) for i in range(k + 1)))


def tails(obs, lam):
    return pois_cdf(obs, lam), (1.0 - pois_cdf(obs - 1, lam)) if obs > 0 else 1.0


def gather():
    rows = {}
    for k, fname in ((2, "twice-nice.json"), (3, "thrice-nice.json")):
        d = json.loads((ROOT / "critique" / "results" / fname).read_text())
        for r in d["rows"]:
            if r.get("searched"):
                rows[(k, r["base"])] = {"k": k, "base": r["base"], "observed": r["observed"],
                                        "solutions": [int(x) for x in r["solutions"]],
                                        "source": f"critique/results/{fname}"}
    for f in sorted((HERE / "results").glob("run_k[23]_b*.json")):
        r = json.loads(f.read_text())
        key = (r["k"], r["base"])
        new = {"k": r["k"], "base": r["base"], "observed": r["observed"],
               "solutions": [int(x) for x in r["solutions"]], "complete": r["complete"],
               "source": f"attack/p3-analogues/results/{f.name}"}
        if not r["complete"]:
            new["partial"] = r
        if key in rows:  # cross-check an old result
            assert sorted(rows[key]["solutions"]) == sorted(new["solutions"]) or not r["complete"], key
            rows[key]["source"] += " + " + new["source"]
        else:
            rows[key] = new
    return rows


def fit_trend(obs, lam, x):
    """MLE for log mu = log lam + a + b*(x - xbar). Returns dict with profile CIs."""
    obs, lam, x = map(np.asarray, (obs, lam, x))
    keep = lam > 0
    obs, lam, x = obs[keep], lam[keep], x[keep]
    xbar = float(np.average(x, weights=lam))
    xc = x - xbar

    def nll(a, b):
        mu = lam * np.exp(a + b * xc)
        return float(np.sum(mu - obs * np.log(mu)))

    def fit_a(b):  # closed form for a given b
        return math.log(obs.sum() / np.sum(lam * np.exp(b * xc)))

    # Newton on b with a profiled out
    b = 0.0
    for _ in range(100):
        h = 1e-5
        f0, fp, fm = nll(fit_a(b), b), nll(fit_a(b + h), b + h), nll(fit_a(b - h), b - h)
        g, hh = (fp - fm) / (2 * h), (fp - 2 * f0 + fm) / h ** 2
        step = g / hh if hh > 0 else 0.1 * np.sign(-g)
        b -= step
        if abs(step) < 1e-10:
            break
    a = fit_a(b)
    best = nll(a, b)

    def prof(bb):
        return nll(fit_a(bb), bb) - best

    def root(lo, hi):
        for _ in range(200):
            mid = (lo + hi) / 2
            if (prof(mid) - 1.92) * (prof(lo) - 1.92) > 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    span = 1.0
    while prof(b - span) < 1.92 or prof(b + span) < 1.92:
        span *= 2
    lo95, hi95 = root(b - span, b), root(b, b + span)
    # standard error from curvature
    h = 1e-4
    curv = (prof(b + h) - 2 * prof(b) + prof(b - h)) / h ** 2
    se = 1 / math.sqrt(curv) if curv > 0 else float("nan")
    # likelihood-ratio test of b = 0
    lr = 2 * prof(0.0)
    p_b0 = math.erfc(math.sqrt(lr / 2)) if lr > 0 else 1.0
    # one-sided p for b > 0 (obstruction direction)
    z = b / se if se == se else 0.0
    p_pos = 0.5 * math.erfc(z / math.sqrt(2))  # P(Z >= z) under b = 0
    # overall scale with b = 0
    tot_o, tot_e = float(obs.sum()), float(lam.sum())
    return {"n_bases": int(len(obs)), "xbar_log10p": xbar, "scale_at_xbar": math.exp(a),
            "slope_beta": b, "slope_se": se, "slope_95ci": [lo95, hi95],
            "lr_p_beta_eq_0": p_b0, "one_sided_p_beta_gt_0": p_pos,
            "total_observed": tot_o, "total_expected": tot_e, "ratio": tot_o / tot_e,
            "ratio_95ci": poisson_ratio_ci(int(tot_o), tot_e),
            "meaning": "ratio(p) = scale * 10^(beta*(log10 p - xbar)); obstruction => beta > 0"}


def fit_common_slope(groups):
    """Common slope beta, separate scale per group (e.g. per k). groups: list of (obs, lam, x)."""
    gs = []
    allx = np.concatenate([np.asarray(x, float) for _, _, x in groups])
    alll = np.concatenate([np.asarray(l, float) for _, l, _ in groups])
    xbar = float(np.average(allx, weights=alll))
    for o, l, x in groups:
        gs.append((np.asarray(o, float), np.asarray(l, float), np.asarray(x, float) - xbar))

    def prof_nll(b):
        tot = 0.0
        for o, l, xc in gs:
            a = math.log(o.sum() / np.sum(l * np.exp(b * xc)))
            mu = l * np.exp(a + b * xc)
            tot += float(np.sum(mu - o * np.log(mu)))
        return tot
    grid = np.linspace(-1, 1, 4001)
    vals = np.array([prof_nll(b) for b in grid])
    i = int(vals.argmin())
    lo_b, hi_b = grid[max(i - 2, 0)], grid[min(i + 2, len(grid) - 1)]
    for _ in range(100):  # golden-section refine
        m1, m2 = lo_b + (hi_b - lo_b) * 0.382, lo_b + (hi_b - lo_b) * 0.618
        if prof_nll(m1) < prof_nll(m2):
            hi_b = m2
        else:
            lo_b = m1
    b = (lo_b + hi_b) / 2
    best = prof_nll(b)
    d = lambda bb: prof_nll(bb) - best
    h = 1e-4
    se = 1 / math.sqrt((d(b + h) - 2 * d(b) + d(b - h)) / h ** 2)
    ci = [float(grid[np.where((vals - best) < 1.92)[0].min()]), float(grid[np.where((vals - best) < 1.92)[0].max()])]
    z = b / se
    scales = [float(o.sum() / np.sum(l * np.exp(b * xc))) for o, l, xc in gs]
    return {"xbar_log10p": xbar, "slope_beta": b, "slope_se": se, "slope_95ci_grid": ci,
            "scale_per_group_at_xbar": scales, "slope_per_decade_note": "mu = E * scale_k * exp(beta*(log10p - xbar))",
            "lr_p_beta_eq_0": math.erfc(math.sqrt(max(2 * d(0.0), 0) / 2)),
            "one_sided_p_beta_gt_0": 0.5 * math.erfc(z / math.sqrt(2))}


def poisson_ratio_ci(o, e):
    """Exact (Garwood) 95% CI for obs/exp."""
    def inv_upper(target, lo, hi):  # find lam with P(X>=o | lam) = target
        for _ in range(200):
            mid = (lo + hi) / 2
            if 1 - pois_cdf(o - 1, mid) < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def inv_lower(target, lo, hi):  # find lam with P(X<=o | lam) = target
        for _ in range(200):
            mid = (lo + hi) / 2
            if pois_cdf(o, mid) > target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lo = inv_upper(0.025, 0.0, o + 10 * math.sqrt(o + 1) + 10) if o > 0 else 0.0
    hi = inv_lower(0.025, 0.0, o + 20 * math.sqrt(o + 1) + 20)
    return [lo / e, hi / e]


def main():
    rows = gather()
    model = {(r["k"], r["base"]): r for r in json.loads((HERE / "results" / "model.json").read_text())["rows"]}
    table = []
    for (k, b), r in sorted(rows.items()):
        info = m0(b, k)
        mrow = model.get((k, b), {})
        e0 = info["m0_expected"]
        partial = r.get("partial")
        frac = 1.0
        if partial:
            e0 = partial["m0_expected_covered"]
            frac = e0 / info["m0_expected"]
        o = r["observed"]
        lo_t, hi_t = tails(o, e0) if e0 > 0 else (1.0, 1.0 if o == 0 else 0.0)
        row = {"k": k, "base": b, "count": info["count"], "p_per_candidate": info["p_per_candidate"],
               "log10_p": math.log10(info["p_per_candidate"]) if info["p_per_candidate"] > 0 else None,
               "m0_expected": e0, "m0_coverage_fraction": frac, "observed": o,
               "ratio": o / e0 if e0 > 0 else None,
               "p_le_obs": lo_t, "p_ge_obs": hi_t,
               "m1e_expected": (mrow.get("m1e_expected") or 0.0) * frac,
               "m1e_se": (mrow.get("m1e_se") or 0.0) * frac,
               "new": "attack/p3-analogues" in r["source"] and "critique" not in r["source"]
                      or (k == 3 and b == 16),
               "source": r["source"], "solutions": [str(x) for x in r["solutions"]]}
        table.append(row)
    fits = {}
    for name, sel in (("all", lambda r: True), ("k2", lambda r: r["k"] == 2), ("k3", lambda r: r["k"] == 3)):
        for mname, key in (("M0", "m0_expected"), ("M1e", "m1e_expected")):
            rs = [r for r in table if sel(r) and r[key] > 0]  # M1e undefined for the tiniest bases
            fits[f"{name}_{mname}"] = fit_trend([r["observed"] for r in rs], [r[key] for r in rs],
                                                [r["log10_p"] for r in rs])
    for mname, key in (("M0", "m0_expected"), ("M1e", "m1e_expected")):
        groups = []
        for kk in (2, 3):
            rs = [r for r in table if r["k"] == kk and r[key] > 0]
            groups.append(([r["observed"] for r in rs], [r[key] for r in rs], [r["log10_p"] for r in rs]))
        fits[f"all_{mname}_scale_per_k"] = fit_common_slope(groups)
    # robustness: rare regime only, and out-of-sample test (fit old data, predict new bases)
    robust = {}
    for mname, key in (("M0", "m0_expected"), ("M1e", "m1e_expected")):
        for label, sel in (("p_below_1e-7", lambda r: r["p_per_candidate"] < 1e-7),
                           ("E_at_least_1", lambda r, key=key: r[key] >= 1),
                           ("old_only", lambda r: not r["new"])):
            groups = []
            for kk in (2, 3):
                rs = [r for r in table if r["k"] == kk and r[key] > 0 and sel(r)]
                groups.append(([r["observed"] for r in rs], [r[key] for r in rs], [r["log10_p"] for r in rs]))
            robust[f"{mname}_scale_per_k_{label}"] = fit_common_slope(groups)
        f = robust[f"{mname}_scale_per_k_old_only"]
        pred = []
        for r in table:
            if not r["new"]:
                continue
            sc = f["scale_per_group_at_xbar"][r["k"] - 2]
            mu = r[key] * sc * math.exp(f["slope_beta"] * (r["log10_p"] - f["xbar_log10p"]))
            pred.append({"k": r["k"], "base": r["base"], "observed": r["observed"], "predicted_by_old_trend": mu,
                         "flat_model": r[key]})
        o = sum(p["observed"] for p in pred)
        mu = sum(p["predicted_by_old_trend"] for p in pred)
        robust[f"{mname}_out_of_sample"] = {"rows": pred, "observed": o, "predicted_by_old_trend": mu,
                                             "flat_model": sum(p["flat_model"] for p in pred),
                                             "p_ge_obs_under_old_trend": tails(o, mu)[1]}
    fits["robustness"] = robust
    # pooled comparison: rare regime vs earlier
    pooled = {}
    for label, sel in (("previously_tested", lambda r: not r["new"]), ("new_bases", lambda r: r["new"]),
                       ("p_below_1e-10", lambda r: r["p_per_candidate"] < 1e-10),
                       ("p_below_1e-12", lambda r: r["p_per_candidate"] < 1e-12),
                       ("new_k2", lambda r: r["new"] and r["k"] == 2),
                       ("new_k3", lambda r: r["new"] and r["k"] == 3)):
        rs = [r for r in table if sel(r) and r["m0_expected"] > 0]
        o, e = sum(r["observed"] for r in rs), sum(r["m0_expected"] for r in rs)
        e1 = sum(r["m1e_expected"] for r in rs)
        lo_t, hi_t = tails(o, e)
        pooled[label] = {"bases": [f"k{r['k']}b{r['base']}" for r in rs], "observed": o, "m0_expected": e,
                         "ratio": o / e if e else None, "ratio_95ci": poisson_ratio_ci(o, e) if e else None,
                         "p_le_obs": lo_t, "p_ge_obs": hi_t, "m1e_expected": e1,
                         "ratio_m1e": o / e1 if e1 else None,
                         "m1e_p_le_obs": tails(o, e1)[0] if e1 else None,
                         "m1e_p_ge_obs": tails(o, e1)[1] if e1 else None,
                         "ratio_m1e_95ci": poisson_ratio_ci(o, e1) if e1 else None}
    # What slope would an obstruction need? Extrapolate ratio(p) = 10^(beta*(log10 p - xbar)) (scale 1)
    # to the nice-number (k = 1) model and ask for < 1 expected second nice number in bases 58..Bmax.
    reach = json.loads((ROOT / "critique" / "results" / "reachability.json").read_text())["rows"]
    ref = fits["all_M1e"]
    xbar = ref["xbar_log10p"]
    needed = {}
    for bmax in (100, 150, 200, 300, 600):
        rs = [r for r in reach if 58 <= r["base"] <= bmax and r["expected_nice"] > 0]
        le = np.array([r["log10_expected_nice"] for r in rs])
        lp = le - np.array([r["log10_interval_count"] for r in rs])

        def total(beta):
            return float(np.sum(10.0 ** (le + beta * (lp - xbar))))
        lo_b, hi_b = 0.0, 5.0
        for _ in range(200):
            mid = (lo_b + hi_b) / 2
            if total(mid) > 1:
                lo_b = mid
            else:
                hi_b = mid
        beta_need = (lo_b + hi_b) / 2
        f = ref
        needed[str(bmax)] = {"model_expected_58_to_bmax": total(0.0), "beta_needed": beta_need,
                             "log10p_range_58_to_bmax": [float(lp.min()), float(lp.max())],
                             "z_of_needed_vs_M1e_fit": (beta_need - f["slope_beta"]) / f["slope_se"]}
    # Calibration extras (k = 4, 5 at small bases; not part of the pre-registered fit)
    extras = []
    for f in sorted((HERE / "results").glob("extra_k*_b*.json")):
        r = json.loads(f.read_text())
        k, b = r["k"], r["base"]
        info, mrow = m0(b, k), model.get((k, b), {})
        o, e0, e1 = r["observed"], info["m0_expected"], mrow.get("m1e_expected") or 0.0
        extras.append({"k": k, "base": b, "count": info["count"], "complete": r["complete"],
                       "log10_p": math.log10(info["p_per_candidate"]), "observed": o,
                       "m0_expected": e0, "ratio_m0": o / e0, "z_m0": (o - e0) / math.sqrt(e0),
                       "m1e_expected": e1, "m1e_se": mrow.get("m1e_se"),
                       "ratio_m1e": o / e1 if e1 else None,
                       "z_m1e": (o - e1) / math.sqrt(e1) if e1 else None})
        print("extra", json.dumps(extras[-1]))
    nm = json.loads((HERE / "results" / "nearmiss.json").read_text()) if (HERE / "results" / "nearmiss.json").exists() else {}
    depth = json.loads((HERE / "results" / "m1e_depth34.json").read_text()) if (HERE / "results" / "m1e_depth34.json").exists() else {}
    out = {"table": table, "fits": fits, "pooled": pooled, "beta_needed_for_uniqueness": needed,
           "calibration_extras": extras, "nearmiss_calibration": nm, "m1e_depth_3_4": depth}
    print("beta needed", json.dumps(needed))
    (HERE / "results" / "analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{'k':>2} {'b':>3} {'log10p':>7} {'M0 exp':>9} {'M1e exp':>9} {'obs':>5} {'ratio':>6} {'P(<=)':>7} {'P(>=)':>7}  new")
    for r in table:
        print(f"{r['k']:>2} {r['base']:>3} {r['log10_p'] if r['log10_p'] is not None else float('nan'):>7.2f} "
              f"{r['m0_expected']:>9.3f} {r['m1e_expected']:>9.3f} {r['observed']:>5} "
              f"{(r['ratio'] or 0):>6.3f} {r['p_le_obs']:>7.3f} {r['p_ge_obs']:>7.3f}  {r['new']}")
    for k, v in fits.items():
        print(k, json.dumps({x: (round(y, 4) if isinstance(y, float) else y) for x, y in v.items() if x != "meaning"}))
    for k, v in pooled.items():
        print(k, json.dumps({x: y for x, y in v.items() if x != "bases"}))


if __name__ == "__main__":
    main()
