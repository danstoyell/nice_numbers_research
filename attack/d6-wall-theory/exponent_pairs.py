#!/usr/bin/env python3
"""Reachability for a general exponent pair (e1, e2) (D6 note, step 3).
For an L-digit root, digit p of n^e is reachable from the bottom only with p+1 root digits and from the
top only with about eL-p leading digits; the window reachable from neither end is [L, (e-1)L).
Uncertified fraction:  edges (t+k=L): 1 - 2/E;  overlap-join ceiling: sum (e_i-2)^+ / E,  E = e1+e2.
Random-model cost per solution ~ b^M/M!, M = rho*b  ->  ln(cost)/b -> rho*(1 - ln rho)."""
import json, math
def kappa(r): return 0.0 if r == 0 else r * (1 - math.log(r))
rows = []
for e1, e2 in [(1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (2, 5), (3, 5), (4, 5)]:
    E = e1 + e2; re = 1 - 2 / E; rc = (max(e1 - 2, 0) + max(e2 - 2, 0)) / E
    rows.append({"pair": [e1, e2], "E": E, "wall_positions": {f"n^{e}": ([1, e - 1] if e > 2 else None) for e in (e1, e2)},
                 "uncertified_edges": re, "uncertified_ceiling": rc, "kappa_edges": kappa(re), "kappa_ceiling": kappa(rc)})
    print(f"({e1},{e2}) E={E}: uncertified edges {re:.3f} (kappa {kappa(re):.3f}), ceiling {rc:.3f} (kappa {kappa(rc):.3f}), certified at ceiling {1-rc:.0%}")
json.dump(rows, open("results/exponent_pairs.json", "w"), indent=1)
