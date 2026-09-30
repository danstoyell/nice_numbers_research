#!/usr/bin/env python3
"""Per-position decomposition of H1's degenerate-batch tail (results/tails_*.json from `tails h1`)."""
import json, sys
H1 = {"twice-15": (5.1e-07, 8.9e-05, 4.4e-04, 1979316), "twice-17": (2.3e-06, 3.3e-05, 2.1e-04, 16092790),
      "thrice-13": (1.1e-05, 1.4e-04, 8.0e-04, 58086616), "nice-30 (3,2)": (0.0, 2.6e-07, 1.6e-06, 27305718),
      "nice-30 (2,3)": (4.3e-05, 1.1e-04, 1.3e-03, 26689620)}
files = [("twice-15", "tails_twice15.json"), ("twice-17", "tails_twice17.json"), ("thrice-13", "tails_thrice13.json"),
         ("nice-30 (3,2)", "tails_nice30_32.json"), ("nice-30 (2,3)", "tails_nice30_23.json")]
summary = []
for name, fn in files:
    r = json.load(open("results/" + fn)); b, L, t, k = r["b"], r["L"], r["t"], r["k"]; f = L - t - k
    agg = [0] * (b + 1); rows = []
    for p in r["positions"]:
        P = p["P"]; h = p["hist"]; hs = p["hist_structured_model"]
        for cl in (0, 1):
            for d, x in enumerate(h[cl]): agg[d] += x
        full, tr = h[0], h[1]; nfull, ntr = sum(full), sum(tr)
        e2 = P + 1 - 2 * k; rho = min(1.0, 3 * b ** L / b ** e2) if e2 > 0 else 0.0
        j = P + 1 - 2 * k - f
        reg = "prefix-free" if j <= 0 else ("linear" if j <= k + f else "Ptop^2")
        rows.append({"P": P, "theta1_regime": reg, "theta3_exp": P + 1 - 3 * k, "rho_theta2": rho,
                     "full": nfull, "full_D1": full[1], "full_Dle3": sum(full[:4]), "struct_D1": hs[0][1], "struct_Dle3": sum(hs[0][:4]),
                     "trunc": ntr, "trunc_Dle3": sum(tr[:4])})
    tot = sum(agg)
    s = {"case": name, "b": b, "t": t, "k": k, "positions": tot, "P_D1": agg[1] / tot, "P_Dle2": sum(agg[:3]) / tot, "P_Dle3": sum(agg[:4]) / tot,
         "H1_table": H1[name], "rows": rows}
    summary.append(s)
    print(f"\n{name}: positions {tot:,}  P(D=1) {s['P_D1']:.2e}  P(D<=2) {s['P_Dle2']:.2e}  P(D<=3) {s['P_Dle3']:.2e}   H1 table: {H1[name]}")
    for x in rows:
        print(f"  P={x['P']:2d} th1:{x['theta1_regime']:<11} th3=b^-{x['theta3_exp']:<3} rho2={x['rho_theta2']:.2g}  full {x['full']:>9,} D=1 {x['full_D1']:>5} (struct {x['struct_D1']:>5})  D<=3 {x['full_Dle3']:>6} (struct {x['struct_Dle3']:>6})   trunc {x['trunc']:>6} D<=3 {x['trunc_Dle3']:>5}")
json.dump(summary, open("results/tail_summary.json", "w"), indent=1)
