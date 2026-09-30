#!/usr/bin/env python3
"""Heterogeneity and trend of observed/M1(2,3) across bases 17-30 (from results/summary.json)."""
import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

R = Path(__file__).resolve().parent / "results"
t = [r for r in json.load(open(R / "summary.json"))["table"] if r["b"] >= 17 and r.get("M1(2,3)")]
out = {}
for key in ["M0", "M1(1,1)", "M1(2,3)", "M1(3,4)", "M1e"]:
    O = np.array([r["obs"] for r in t]); E = np.array([r[key] for r in t]); b = np.array([r["b"] for r in t])
    chi = float((((O - E) ** 2) / E).sum())
    # Poisson regression of O on log E offset with slope in b: log mu = log E + a + g*(b - 24)
    def nll(p):
        mu = E * np.exp(p[0] + p[1] * (b - 24))
        return float((mu - O * np.log(mu)).sum())
    from scipy.optimize import minimize
    res = minimize(nll, [0.0, 0.0], method="Nelder-Mead", options={"xatol": 1e-8, "fatol": 1e-10})
    a, g = res.x
    # standard error of g from the observed information
    mu = E * np.exp(a + g * (b - 24)); X = np.stack([np.ones_like(b, dtype=float), b - 24.0], 1)
    I = X.T @ (X * mu[:, None]); se_g = math.sqrt(np.linalg.inv(I)[1, 1])
    out[key] = {"bases": b.tolist(), "chi2": chi, "dof": len(t), "p": float(stats.chi2.sf(chi, len(t))),
                "trend_per_base": float(g), "trend_se": se_g, "trend_z": float(g / se_g)}
    print(f"{key:8s} heterogeneity chi2 {chi:6.2f} on {len(t)} dof, p {out[key]['p']:.3f}; "
          f"trend in log(obs/model) per base {g:+.4f} +- {se_g:.4f} (z {g / se_g:+.2f})")
json.dump(out, open(R / "extra_stats.json", "w"), indent=1)
