#!/usr/bin/env python3
"""Exact M1 distribution of n mod b^k (k = 1, 2, 3) given deficiency r, and
tests of the observed near misses against it.

Under M1 the bottom 3 digits of n^2 and n^3 are fixed by n mod b^3 and the top
2 by the position of n, so
    P(n = rho mod b^3 | deficiency r)  ∝  sum_top W_top * w(u(top ∪ bottom(rho)))
with w(u) the exact probability that a uniform middle completes the edges to
deficiency r (model_mc.valid_middles). Summing A(rho)/b^3 times the interval
size reproduces the M1 expected count, which is asserted.
n mod (b+1) is exactly uniform under M1 (coprime to b^3; position-free), so
it is tested against uniform.

Statistic: S = sum over events of -log P_b(residue). Its null distribution is
obtained by parametric bootstrap from the exact P_b (no Monte Carlo
probability estimates, so no in-sample bias). A PIT-style rank is also
reported: under the model, the fraction of events whose residue is more
probable than a model draw is uniform.

Usage: python3 attack/p3-obstruction/scripts/exact_residue_test.py [--deficiency 2]
"""
import argparse
import json
import math
import sys

sys.dont_write_bytecode = True  # never write caches into critique/ or scripts/
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "critique/scripts"))
from common import BASES, HERE, intervals, load_events, m1_expected, shape  # noqa: E402
from model_mc import valid_middles  # noqa: E402
from tail_validation import top_configs  # noqa: E402


def bottom_masks(b, k=3):
    mod = b ** k
    r = np.arange(mod, dtype=object)
    masks = np.zeros(mod, dtype=np.uint64)
    for rho in range(mod):
        sq, cu = rho * rho % mod, rho ** 3 % mod
        m = 0
        for _ in range(k):
            sq, d1 = divmod(sq, b)
            cu, d2 = divmod(cu, b)
            m |= (1 << d1) | (1 << d2)
        masks[rho] = m
    return masks


def residue_weights(b, r):
    s, c = shape(b)
    m = b - 10
    wu = np.zeros(11)
    for u in range(1, 11):
        wu[u] = valid_middles(b, m, u, r)[0] / b ** m
    bm = bottom_masks(b)
    A = np.zeros(len(bm))
    total_w = 0
    for lo, hi, wgt in intervals(b):
        masks, weights = top_configs(b, lo, hi, s, c, 2)
        scale = wgt / (hi - lo + 1)
        for mk, w in zip(masks, weights):
            tm = np.uint64(mk if mk >= 0 else -1 - mk)
            u = np.bitwise_count(bm | tm).astype(np.int64)
            A += w * scale * wu[u]
        total_w += wgt
    expected = A.sum() / len(bm)   # per-residue weight already carries interval size
    return A / A.sum(), expected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deficiency", type=int, default=2)
    ap.add_argument("--reps", type=int, default=20000)
    args = ap.parse_args()
    r = args.deficiency
    rng = np.random.default_rng(2026)
    events = load_events()
    out = {"deficiency": r, "bases": {}, "tests": {}}
    S_obs = {1: 0.0, 2: 0.0, 3: 0.0}
    sims = {key: np.zeros(args.reps) for key in S_obs}
    pit = []
    for b in BASES:
        obs = [n for n, d in events[b] if d == r]
        P3, expected = residue_weights(b, r)
        e_ref = m1_expected(b, r)
        assert abs(expected / e_ref - 1) < 2e-3, (b, expected, e_ref)
        out["bases"][b] = {"observed": len(obs), "m1_expected_recomputed": expected}
        for k in (1, 2, 3):
            Pk = P3.reshape(-1, b ** k).sum(axis=0) if k < 3 else P3
            # P3 index is rho mod b^3; reshape rows = rho // b^k, cols = rho mod b^k
            logp = -np.log(np.maximum(Pk, 1e-300))
            S_obs[k] += sum(logp[n % b ** k] for n in obs)
            if obs:
                draws = rng.choice(len(Pk), size=(args.reps, len(obs)), p=Pk)
                sims[k] += logp[draws].sum(axis=1)
            if k == 1:
                order = np.argsort(Pk)
                for n in obs:
                    x = n % b
                    below = Pk[Pk < Pk[x]].sum()
                    tie = Pk[Pk == Pk[x]].sum()
                    pit.append(float(below + rng.random() * tie))
                out["bases"][b]["n_mod_b"] = {"model_top5": [[int(i), float(Pk[i])] for i in order[::-1][:5]],
                                              "observed": sorted(n % b for n in obs)}
        print(f"base {b}: observed {len(obs)}, M1 recomputed {expected:.2f} (ref {e_ref:.2f})", flush=True)
    for k in (1, 2, 3):
        p = float((sims[k] >= S_obs[k]).mean())
        out["tests"][f"n mod b^{k}"] = {"surprise_observed": S_obs[k], "null_mean": float(sims[k].mean()),
                                        "null_sd": float(sims[k].std()), "p_upper": p,
                                        "z": float((S_obs[k] - sims[k].mean()) / sims[k].std())}
        print(f"n mod b^{k}: surprise {S_obs[k]:.1f} vs exact-model {sims[k].mean():.1f} +- {sims[k].std():.1f}; "
              f"z {(S_obs[k]-sims[k].mean())/sims[k].std():+.2f}, p(>=) = {p:.3f}")
    from scipy import stats
    ks = stats.kstest(pit, "uniform")
    out["tests"]["n mod b PIT"] = {"n": len(pit), "mean": float(np.mean(pit)), "ks_p": float(ks.pvalue)}
    print(f"n mod b PIT: mean {np.mean(pit):.3f} (0.5 under model), KS p = {ks.pvalue:.3f}")
    # n mod (b+1): exactly uniform under M1; pooled test via per-event uniform PIT u = (n mod (b+1)) / (b+1)
    u = [((n % (b + 1)) + rng.random()) / (b + 1) for b in BASES for n, d in events[b] if d == r]
    ks2 = stats.kstest(u, "uniform")
    # pooled position test: 10 bins of (n mod (b+1))/(b+1)
    bins = np.histogram(u, bins=10, range=(0, 1))[0]
    e = len(u) / 10
    chi = float(((bins - e) ** 2 / e).sum())
    out["tests"]["n mod (b+1)"] = {"ks_p": float(ks2.pvalue), "decile_counts": bins.tolist(),
                                   "chi2_9dof": chi, "p": float(stats.chi2.sf(chi, 9))}
    print(f"n mod (b+1) vs uniform: KS p = {ks2.pvalue:.3f}; decile chi2 {chi:.1f} (9 dof) p = {stats.chi2.sf(chi, 9):.3f}")
    (HERE / f"results/exact_residue_def{r}.json").write_text(json.dumps(out, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
