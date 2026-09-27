#!/usr/bin/env python3
"""Compare the structure of the observed deficiency-2 near misses with exact
conditional draws from the random-digit model (model_mc.py).

For every feature and category k, two expectations are reported:
  abs   = sum_b E_b * coupling_b * p_b(k)   (M1 count x digit-sum factor x model share)
  shape = sum_b O_b * p_b(k)                (model share at the observed per-base totals)
obs/abs locates *where* a rate shortfall sits (a configuration-specific
obstruction would give obs/abs << 0.87 in one category and ~1 elsewhere);
the chi-square of obs against shape tests the configuration mix alone.
Features with base-dependent categories (n mod b, n mod b-1, n mod b+1,
digit-sum class) use a likelihood "surprise" statistic, calibrated by
parametric bootstrap from the model draws.

Usage: python3 attack/p3-obstruction/scripts/analyze_structure.py
"""
import json
import math
import pickle
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASES, HERE, digits, intervals, load_events, m1_expected, shape  # noqa: E402

T, K = 2, 3


def zone(i, length):
    if i < T:
        return "top"
    if i >= length - K:
        return "bottom"
    return "middle"


def features(b, n, sq, cu):
    """Categorical features of one deficiency-2 event (sq, cu MSD-first)."""
    s, c = len(sq), len(cu)
    cnt = Counter(list(sq) + list(cu))
    reps = sorted(d for d, k in cnt.items() if k > 1)
    missing = [d for d in range(b) if d not in cnt]
    triple = any(k == 3 for k in cnt.values())
    f = {}
    f["type"] = "triple" if triple else "two doubles"
    places, zones, adjacent, dist_same = [], [], 0, []
    for d in reps:
        ps = [i for i, x in enumerate(sq) if x == d]
        pc = [i for i, x in enumerate(cu) if x == d]
        if triple:
            places.append(f"sq{len(ps)}cu{len(pc)}")
        else:
            places.append("within square" if not pc else "within cube" if not ps else "split")
        for i in ps:
            zones.append("sq-" + zone(i, s))
        for i in pc:
            zones.append("cu-" + zone(i, c))
        for pos in (ps, pc):
            for a, z in zip(pos, pos[1:]):
                adjacent += z - a == 1
                dist_same.append(z - a)
    f["placement (per repeated value)"] = places
    f["pattern"] = " + ".join(sorted(places))
    f["zone of each repeated copy"] = zones
    n_edge = sum(1 for z in zones if not z.endswith("middle"))
    f["repeated copies in edge positions"] = str(min(n_edge, 3)) + ("+" if n_edge >= 3 else "")
    f["some repeat adjacent in one power"] = "yes" if adjacent else "no"
    f["0 missing"] = "yes" if 0 in missing else "no"
    f["b-1 missing"] = "yes" if b - 1 in missing else "no"
    f["1 missing"] = "yes" if 1 in missing else "no"
    f["0 repeated"] = "yes" if 0 in reps else "no"
    f["missing value / b (quintile)"] = [str(min(4, 5 * d // b)) for d in missing]
    f["repeated value / b (quintile)"] = [str(min(4, 5 * d // b)) for d in reps]
    f["parity of missing pair"] = {0: "both even", 1: "mixed", 2: "both odd"}[sum(d % 2 for d in missing)]
    f["leading digit of n^2"] = "1" if sq[0] == 1 else "2" if sq[0] == 2 else ">=3"
    f["leading digit of n^3"] = "1" if cu[0] == 1 else "2" if cu[0] == 2 else ">=3"
    f["last digit of n is 0"] = "yes" if n % b == 0 else "no"
    for q in (2, 3, 4, 5, 6, 7, 8, 9, 11, 13):
        f[f"n mod {q}"] = str(n % q)
    return f


def tally(rows, key):
    out = Counter()
    for f in rows:
        v = f[key]
        for x in (v if isinstance(v, list) else [v]):
            out[x] += 1
    return out


def main():
    mc = pickle.loads((HERE / "results/model_mc_def2.pkl").read_bytes())["bases"]
    events = load_events()
    obs_rows = defaultdict(list)
    obs_n = defaultdict(list)
    for b, evs in events.items():
        for n, d in evs:
            if d != 2:
                continue
            sq, cu = digits(n * n, b), digits(n ** 3, b)
            obs_rows[b].append(features(b, n, sq, cu))
            obs_n[b].append(n)
    mc_rows = {b: [features(b, n, sq, cu) for n, sq, cu, _ in mc[b]["samples"]] for b in BASES}
    mc_sep = {b: [features(b, n, sq, cu) for n, sq, cu, sep in mc[b]["samples"] if sep] for b in BASES}
    E = {b: m1_expected(b) for b in BASES}
    coup = {b: mc[b]["coupling_factor"] for b in BASES}
    O = {b: len(obs_rows[b]) for b in BASES}
    report = {"totals": {}, "features": {}, "base_specific": {}, "by_base_class": {}}
    for label, bs in (("20-48", [b for b in BASES if b <= 48]), ("49-50", [49, 50]), ("20-50", BASES)):
        o = sum(O[b] for b in bs)
        e1 = sum(E[b] for b in bs)
        ec = sum(E[b] * coup[b] for b in bs)
        report["totals"][label] = {"observed": o, "M1": e1, "M1_x_digit_sum_coupling_(MC)": ec,
                                   "ratio_M1": o / e1, "z_M1": (o - e1) / math.sqrt(e1),
                                   "ratio_coupled": o / ec, "z_coupled": (o - ec) / math.sqrt(ec)}
        print(f"bases {label}: observed {o}, M1 {e1:.1f} (ratio {o/e1:.3f}, z {(o-e1)/math.sqrt(e1):+.2f}); "
              f"with digit-sum coupling {ec:.1f} (ratio {o/ec:.3f}, z {(o-ec)/math.sqrt(ec):+.2f})")
    keys = list(next(iter(obs_rows.values()))[0].keys())
    print()
    for key in keys:
        obs = Counter()
        for b in BASES:
            obs.update(tally(obs_rows[b], key))
        cats = set(obs)
        mcs = {b: tally(mc_rows[b], key) for b in BASES}
        for b in BASES:
            cats |= set(mcs[b])
        per_event = {b: sum(mcs[b].values()) / len(mc_rows[b]) for b in BASES}
        absx, shp = Counter(), Counter()
        for b in BASES:
            tot = len(mc_rows[b])
            for k in cats:
                p = mcs[b][k] / tot
                absx[k] += E[b] * coup[b] * p
                shp[k] += O[b] * p
        cats = sorted(cats, key=lambda k: -shp[k])
        # chi-square on shape, pooling categories with expectation < 5
        chi, dof, pool_o, pool_e = 0.0, -1, 0, 0.0
        for k in cats:
            if shp[k] < 5:
                pool_o += obs[k]
                pool_e += shp[k]
                continue
            chi += (obs[k] - shp[k]) ** 2 / shp[k]
            dof += 1
        if pool_e > 0:
            chi += (pool_o - pool_e) ** 2 / pool_e
            dof += 1
        multi = any(v != 1 for v in per_event.values())
        p = stats.chi2.sf(chi, dof) if dof > 0 else float("nan")
        report["features"][key] = {
            "categories": {str(k): {"observed": obs[k], "expected_abs": absx[k], "expected_shape": shp[k],
                                    "obs_over_abs": obs[k] / absx[k] if absx[k] else None}
                           for k in cats},
            "shape_chi2": chi, "dof": dof, "p": p, "multi_valued": multi}
        print(f"{key}: shape chi2 {chi:.1f} on {dof} dof, p = {p:.3f}" + (" (items per event > 1; p approximate)" if multi else ""))
        for k in cats[:12]:
            print(f"    {str(k):>28s}: obs {obs[k]:4d}  shape-exp {shp[k]:7.1f}  abs-exp {absx[k]:7.1f}  "
                  f"obs/abs {obs[k]/absx[k] if absx[k] else float('nan'):.2f}")
    # separate-congruence subset: does imposing digitsum(n^2)=n^2 separately change the placement mix?
    print("\nseparate square/cube congruences (subset of draws):")
    for key in ("type", "placement (per repeated value)", "zone of each repeated copy"):
        a, s_ = Counter(), Counter()
        for b in BASES:
            ta, ts = tally(mc_rows[b], key), tally(mc_sep[b], key)
            na, ns = len(mc_rows[b]), max(1, len(mc_sep[b]))
            for k in set(ta) | set(ts):
                a[k] += O[b] * ta[k] / na
                s_[k] += O[b] * ts[k] / ns
        print(f"  {key}: " + ", ".join(f"{k}: {a[k]:.1f} -> {s_[k]:.1f}" for k in sorted(a, key=lambda k: -a[k])[:8]))
        report.setdefault("separate_congruence_shape", {})[key] = {str(k): [a[k], s_[k]] for k in a}
    # base-specific categorical features: likelihood surprise with parametric bootstrap
    rng = random.Random(3)
    print("\nbase-specific residues (likelihood surprise; bootstrap p = P(model surprise >= observed)):")
    lohi = {b: (min(x[0] for x in intervals(b)), max(x[1] for x in intervals(b))) for b in BASES}
    extract = {
        "n mod b": (lambda b, n: n % b, lambda b: b),
        "n mod b-1": (lambda b, n: n % (b - 1), lambda b: b - 1),
        "n mod b+1": (lambda b, n: n % (b + 1), lambda b: b + 1),
        "n mod b^2 (last two digits)": (lambda b, n: n % (b * b), lambda b: b * b),
        "position in checked range (decile)":
            (lambda b, n: min(9, 10 * (n - lohi[b][0]) // (lohi[b][1] - lohi[b][0] + 1)), lambda b: 10),
    }
    for name, (fx, ncats) in extract.items():
        probs, draws = {}, {}
        for b in BASES:
            vals = [fx(b, x[0]) for x in mc[b]["samples"]]
            cnt = Counter(vals)
            ncat = ncats(b)
            tot = len(vals)
            probs[b] = lambda v, cnt=cnt, tot=tot, ncat=ncat: (cnt[v] + 0.5) / (tot + 0.5 * ncat)
            draws[b] = vals
        s_obs = sum(-math.log(probs[b](fx(b, n))) for b in BASES for n in obs_n[b])
        sims = []
        for _ in range(2000):
            s_sim = 0.0
            for b in BASES:
                for _ in range(O[b]):
                    s_sim += -math.log(probs[b](rng.choice(draws[b])))
            sims.append(s_sim)
        p = sum(x >= s_obs for x in sims) / len(sims)
        mean = sum(sims) / len(sims)
        sd = (sum((x - mean) ** 2 for x in sims) / len(sims)) ** 0.5
        report["base_specific"][name] = {"surprise_observed": s_obs, "model_mean": mean, "model_sd": sd, "bootstrap_p": p}
        print(f"  {name}: surprise {s_obs:.1f} vs model {mean:.1f} +- {sd:.1f}; p = {p:.3f}")
    # dependence of the rate on b mod q
    print("\nrate by base class (observed / M1 x coupling):")
    for q in (2, 3, 4, 5, 6):
        rows = {}
        for b in BASES:
            r = rows.setdefault(b % q, [0, 0.0])
            r[0] += O[b]
            r[1] += E[b] * coup[b]
        chi = sum((o - e * sum(O.values()) / sum(E[b] * coup[b] for b in BASES)) ** 2 /
                  (e * sum(O.values()) / sum(E[b] * coup[b] for b in BASES)) for o, e in rows.values())
        p = stats.chi2.sf(chi, len(rows) - 1)
        report["by_base_class"][f"b mod {q}"] = {"classes": {str(k): {"observed": o, "expected": e, "ratio": o / e}
                                                             for k, (o, e) in sorted(rows.items())},
                                                 "heterogeneity_chi2": chi, "p": p}
        print(f"  b mod {q}: " + ", ".join(f"{k}: {o}/{e:.1f}={o/e:.2f}" for k, (o, e) in sorted(rows.items()))
              + f"   heterogeneity p = {p:.2f}")
    (HERE / "results/structure_def2.json").write_text(json.dumps(report, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
