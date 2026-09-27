#!/usr/bin/env python3
"""Deficiency-1 events, and whether the suppression grows toward exact hits.

1. Lists every deficiency-1 number in bases 10-50 (exhaustive for 10-49 and
   for the base-50 chunks with histograms) with its missing and repeated digit
   and where the two copies sit.
2. Expected deficiency-1 counts: M1 times the exact digit-sum coupling factor
   (critique/scripts/digit_sum_coupling.py's coupling_ratio, recomputed here
   for every base).
3. Observed / expected by deficiency and base range, and a likelihood
   comparison of three hypotheses for the suppression factors rho_r:
     H0: rho_r = 1 for all r;
     Hc: a constant rho at deficiencies 1 and 2 (the "13% shortfall" read as real);
     Hg: rho_1 <= rho_2 <= rho_3 (an obstruction growing toward exact hits),
         fitted by isotonic maximum likelihood.
4. A Bayes factor from the out-of-sample data alone (bases 49-50) for
   "rho_2 = 0.867 (the in-sample ratio)" against "rho_2 = 1".

Usage: python3 attack/p3-obstruction/scripts/def1_and_trend.py
"""
import json
import math
import sys

sys.dont_write_bytecode = True  # never write caches into critique/ or scripts/
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "critique/scripts"))
from common import BASES, HERE, ROOT, digits, load_events, m1_expected  # noqa: E402
from digit_sum_coupling import coupling_ratio  # noqa: E402

SMALL = [10, 12, 13, 14, 15, 17, 18, 19]


def poisson_ll(o, e):
    return o * math.log(e) - e - math.lgamma(o + 1) if e > 0 else (0.0 if o == 0 else -math.inf)


def main():
    tv = {r["base"]: {x["deficiency"]: x for x in r["tail"]}
          for r in json.loads((ROOT / "critique/results/tail-validation.json").read_text())["rows"]}
    nm = {r["base"]: r for r in json.loads((HERE / "results/near_misses.json").read_text())["rows"]}
    events = load_events()
    out = {"def1_events": [], "expected": {}, "ratios": {}, "trend": {}}
    # 1. deficiency-1 events, all bases
    def1 = []
    for b in SMALL:
        rec = json.loads((ROOT / "critique/results/histogram-recompute.json").read_text())
        row = next(r for r in rec["rows"] if r["base"] == b)
        def1 += [(b, int(e["n"])) for e in row["near_misses_at_most_two_missing"] if e["distinct"] == b - 1]
    for b in BASES:
        def1 += [(b, n) for n, d in events[b] if d == 1]
    # base 10's single deficiency-1 number: recompute exhaustively (the histogram-recompute
    # list covers it, but check the count against the histogram anyway)
    print("deficiency-1 numbers:")
    for b, n in sorted(def1):
        sq, cu = digits(n * n, b), digits(n ** 3, b)
        allv = sq + cu
        miss = [d for d in range(b) if d not in allv][0]
        rep = next(d for d in range(b) if allv.count(d) == 2)
        ps = [i for i, x in enumerate(sq) if x == rep]
        pc = [i for i, x in enumerate(cu) if x == rep]
        where = "square" if not pc else "cube" if not ps else "split"
        pos = [f"sq[{i}]" for i in ps] + [f"cu[{i}]" for i in pc]
        e = {"base": b, "n": str(n), "missing": miss, "repeated": rep, "placement": where,
             "positions_msd_first": pos, "square_len": len(sq), "cube_len": len(cu),
             "n_mod_b": n % b, "n_mod_b_minus_1": n % (b - 1)}
        out["def1_events"].append(e)
        print(f"  base {b:2d}  n = {n:>16d}  missing {miss:2d}  repeated {rep:2d} ({where}; {', '.join(pos)})")
    # 2. expectations
    exp = {}
    for b in SMALL + BASES:
        c1, c2 = coupling_ratio(b, 1), coupling_ratio(b, 2)
        if b in tv:
            e = {r: tv[b][r]["m1_expected"] for r in (0, 1, 2, 3, 4)}
            o = {r: tv[b][r]["observed"] for r in (0, 1, 2, 3, 4)}
        else:
            nd = json.loads((HERE / "results/new_data_test.json").read_text())[str(b)]
            key = "uniform" if b == 49 else "prefix"
            e = {r: nd["m1_expected"][key][str(r)] for r in (0, 1, 2, 3, 4)}
            o = {r: nd["observed"][str(r)] for r in (0, 1, 2, 3, 4)}
        exp[b] = {"observed": o, "m1": e, "coupling": {1: c1, 2: c2},
                  "coupled": {1: e[1] * c1, 2: e[2] * c2, 3: e[3], 4: e[4]}}
    out["expected"] = exp
    groups = {"10-19 (small bases)": SMALL, "20-48 (critique sample)": [b for b in BASES if b <= 48],
              "49-50 (out of sample)": [49, 50], "20-50": BASES}
    print("\nobserved / expected (M1 x exact digit-sum coupling at r = 1, 2; M1 at r = 3, 4):")
    for name, bs in groups.items():
        row = {}
        for r in (1, 2, 3, 4):
            o = sum(exp[b]["observed"][r] for b in bs)
            e = sum(exp[b]["coupled"][r] for b in bs)
            z = (o - e) / math.sqrt(e)
            p_le = sum(math.exp(poisson_ll(k, e)) for k in range(o + 1)) if e < 2000 else None
            row[r] = {"observed": o, "expected": e, "ratio": o / e, "z": z, "poisson_P_le_obs": p_le}
        out["ratios"][name] = row
        print(f"  {name:24s} " + "  ".join(f"r={r}: {v['observed']}/{v['expected']:.1f} = {v['ratio']:.3f} (z {v['z']:+.2f})"
                                             for r, v in row.items()))
    # 3. hypotheses, bases 20-50 (pooled per deficiency; per-base Poisson likelihoods)
    bs = BASES
    def total_ll(rho):
        return sum(poisson_ll(exp[b]["observed"][r], rho[r] * exp[b]["coupled"][r]) for b in bs for r in (1, 2, 3))
    O = {r: sum(exp[b]["observed"][r] for b in bs) for r in (1, 2, 3)}
    E = {r: sum(exp[b]["coupled"][r] for b in bs) for r in (1, 2, 3)}
    h0 = {1: 1.0, 2: 1.0, 3: 1.0}
    rc = (O[1] + O[2]) / (E[1] + E[2])
    hc = {1: rc, 2: rc, 3: 1.0}
    # isotonic MLE for rho_1 <= rho_2 <= rho_3 (pool adjacent violators on O/E, capped at 1 is not imposed)
    blocks = [[O[r], E[r], [r]] for r in (1, 2, 3)]
    changed = True
    while changed:
        changed = False
        for i in range(len(blocks) - 1):
            if blocks[i][0] / blocks[i][1] > blocks[i + 1][0] / blocks[i + 1][1]:
                blocks[i] = [blocks[i][0] + blocks[i + 1][0], blocks[i][1] + blocks[i + 1][1], blocks[i][2] + blocks[i + 1][2]]
                del blocks[i + 1]
                changed = True
                break
    hg = {r: blk[0] / blk[1] for blk in blocks for r in blk[2]}
    ll0, llc, llg = total_ll(h0), total_ll(hc), total_ll(hg)
    out["trend"] = {"bases": "20-50", "O": O, "E": E,
                    "H0": {"rho": h0, "loglik": ll0},
                    "Hc_constant_rho_at_r_le_2": {"rho": hc, "loglik": llc, "2dlogL_vs_H0": 2 * (llc - ll0)},
                    "Hg_monotone_growing_toward_exact": {"rho": hg, "loglik": llg, "2dlogL_vs_H0": 2 * (llg - ll0)}}
    print(f"\nH0 (no suppression)             loglik {ll0:.2f}")
    print(f"Hc (constant rho={rc:.3f} at r<=2)  loglik {llc:.2f}  (2 dlogL = {2*(llc-ll0):.2f}, 1 extra parameter)")
    print("Hg (rho_1<=rho_2<=rho_3, isotonic MLE) rho = " + ", ".join(f"{r}: {v:.3f}" for r, v in sorted(hg.items()))
          + f"  loglik {llg:.2f} (2 dlogL = {2*(llg-ll0):.2f})")
    # deficiency-1 power: probability of seeing >= observed if rho_1 = rho_2(in-sample) or lower
    e1 = E[1]
    for rho in (1.0, 0.867, 0.5, 0.25):
        p = 1 - sum(math.exp(poisson_ll(k, rho * e1)) for k in range(O[1]))
        out["trend"].setdefault("def1_P_ge_observed", {})[str(rho)] = p
        print(f"  P(def-1 count >= {O[1]} | rho_1 = {rho}) = {p:.3f}   (expected {rho*e1:.2f})")
    # 4. Bayes factor from out-of-sample data alone
    o2 = sum(exp[b]["observed"][2] for b in (49, 50))
    e2 = sum(exp[b]["coupled"][2] for b in (49, 50))
    bf = math.exp(poisson_ll(o2, e2) - poisson_ll(o2, 0.867 * e2))
    power = sum(math.exp(poisson_ll(k, 0.867 * e2)) for k in range(0, 10 ** 4) if (k - e2) / math.sqrt(e2) < -2)
    out["out_of_sample_def2"] = {"observed": o2, "expected": e2, "z": (o2 - e2) / math.sqrt(e2),
                                 "bayes_factor_no_suppression_vs_0.867": bf,
                                 "power_of_2sigma_rule_if_rho_0.867": power}
    print(f"\nout-of-sample deficiency 2 (bases 49-50): {o2} vs {e2:.2f} expected, z = {(o2-e2)/math.sqrt(e2):+.2f}; "
          f"Bayes factor (rho=1 : rho=0.867) = {bf:.2f}; P(z < -2 | rho = 0.867) = {power:.3f}")
    (HERE / "results/def1_and_trend.json").write_text(json.dumps(out, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
