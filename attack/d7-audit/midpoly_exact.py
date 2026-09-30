#!/usr/bin/env python3
"""D7 audit of middle-digits/midpoly.c `coeff` mode: recompute one row with exact
arithmetic, replaying midpoly's splitmix64 stream draw for draw.

For `./midpoly coeff 30 6 t k 1 P 300000 7` this reproduces, per sampled batch c:
  - the measured domain size (exact integer cubes);
  - Lemma 1 itself, with the REDUCED residues x0, th1, th2, th3 (midpoly's own
    "identity check" only re-expands (c + b^k m)^3, which is the binomial theorem);
  - the 64-bin histograms of x0 and th1, exactly and as midpoly computes them in double;
  - the polynomial model with the same uniform draws px0, pth1 (exact dyadic
    rationals), in exact rational arithmetic and in IEEE double exactly as midpoly's
    expression evaluates it (no FMA);
  - the iid control (to confirm the replay is draw-for-draw exact).
It compares everything with the stored row in middle-digits/results/coeff.jsonl.

Usage: python3 midpoly_exact.py t k P [samples] [seed]
"""
import json, math, sys
from pathlib import Path

MASK = (1 << 64) - 1
ROOT = Path(__file__).resolve().parents[2]


class SplitMix:
    def __init__(self, seed): self.s = seed & MASK
    def rnd(self):
        self.s = (self.s + 0x9E3779B97F4A7C15) & MASK
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)


def main():
    t, k, P = map(int, sys.argv[1:4])
    S = int(sys.argv[4]) if len(sys.argv) > 4 else 300000
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 7
    b, L, f = 30, 6, 1
    assert t + k + f == L
    g = SplitMix(seed)
    M = b ** f
    modP = b ** (P + 1)
    e1, e2, e3 = P + 1 - k, P + 1 - 2 * k, P + 1 - 3 * k
    Pmin, Pmax = b ** (t - 1), b ** t
    bk = b ** k
    E = max(e2, e3, 0)
    D = (1 << 53) * b ** E
    nb = 64
    h0x = [0] * nb; h1x = [0] * nb; h0d = [0] * nb; h1d = [0] * nb
    dm = [0] * (b + 1); dpx = [0] * (b + 1); dpd = [0] * (b + 1); di = [0] * (b + 1)
    lemma_bad = 0; poly_diff_batches = 0; hist_idx_diff = 0
    for _ in range(S):
        Ptop = Pmin + g.rnd() % (Pmax - Pmin)
        R = g.rnd() % bk
        c = Ptop * b ** (k + f) + R
        c3 = c ** 3
        r0 = c3 % modP
        r1 = (3 * c * c) % b ** e1 if e1 > 0 else 0
        r2 = (3 * c) % b ** e2 if e2 > 0 else 0
        # histograms: exact index and midpoly's double index
        i0x = nb * r0 // modP; i1x = nb * r1 // b ** e1
        i0d = int(float(r0) / float(modP) * nb); i1d = int(float(r1) / float(b ** e1) * nb)
        h0x[i0x] += 1; h1x[i1x] += 1; h0d[min(i0d, nb - 1)] += 1; h1d[min(i1d, nb - 1)] += 1
        hist_idx_diff += (i0x != i0d) + (i1x != i1d)
        seen = set()
        for m in range(M):
            n = c + bk * m
            d = (n ** 3 // b ** P) % b
            seen.add(d)
            # Lemma 1 with reduced residues, all over the common denominator b^(P+1)
            Y = r0
            if e1 > 0: Y += r1 * b ** k * m
            if e2 > 0: Y += r2 * b ** (2 * k) * m * m
            if e3 > 0: Y += b ** (3 * k) * m ** 3
            if (b * (Y % modP)) // modP != d: lemma_bad += 1
        dm[len(seen)] += 1
        # polynomial model: same draws as midpoly
        a0 = g.rnd() >> 11; a1 = g.rnd() >> 11
        px0 = a0 * (1.0 / 9007199254740992.0); pth1 = a1 * (1.0 / 9007199254740992.0)
        th2 = float(r2) / float(b ** e2) if e2 > 0 else 0.0
        th3 = 1.0 / float(b ** e3) if e3 > 0 else 0.0
        sx = set(); sd = set(); differ = False
        for m in range(M):
            Yn = a0 * b ** E + a1 * m * b ** E
            if e2 > 0: Yn += r2 * b ** (E - e2) * (1 << 53) * m * m
            if e3 > 0: Yn += b ** (E - e3) * (1 << 53) * m ** 3
            dx = (b * (Yn % D)) // D
            fm = float(m)
            y = px0 + pth1 * fm + th2 * fm * fm + th3 * fm * fm * fm
            y -= math.floor(y)
            dd = int(y * b)
            if dd >= b: dd = b - 1
            sx.add(dx); sd.add(dd); differ |= dx != dd
        poly_diff_batches += differ
        dpx[len(sx)] += 1; dpd[len(sd)] += 1
        g.rnd()                                   # qth2 (poly_uniform model), not recomputed
        si = set(g.rnd() % b for _ in range(M))
        di[len(si)] += 1
    ref = None
    for line in (ROOT / "attack/middle-digits/results/coeff.jsonl").open():
        r = json.loads(line)
        if (r["t"], r["k"], r["P"]) == (t, k, P): ref = r
    dev = lambda h: max(abs(x * nb / S - 1) for x in h)
    tv = lambda p, q: sum(abs(x - y) for x, y in zip(p, q)) / (2 * S)
    out = {
        "row": [t, k, P], "samples": S,
        "lemma1_reduced_residue_mismatches": lemma_bad,
        "measured_hist_equals_json": ref is not None and dm == ref["dom_hist_measured"],
        "iid_hist_equals_json": ref is not None and di == ref["dom_hist_iid"],
        "poly_double_hist_equals_json": ref is not None and dpd == ref["dom_hist_poly"],
        "poly_batches_where_double_and_exact_digits_differ": poly_diff_batches,
        "poly_exact_hist_equals_double_hist": dpx == dpd,
        "maxdev_x0": {"exact": round(dev(h0x), 4), "double": round(dev(h0d), 4), "json": ref and ref["maxdev_x0_64bins"]},
        "maxdev_th1": {"exact": round(dev(h1x), 4), "double": round(dev(h1d), 4), "json": ref and ref["maxdev_th1_64bins"]},
        "hist_index_differences": hist_idx_diff,
        "mean_distinct": {"measured": sum(d * x for d, x in enumerate(dm)) / S,
                           "poly_exact": sum(d * x for d, x in enumerate(dpx)) / S,
                           "json_poly": ref and ref["mean_distinct"]["poly_exact_th2"]},
        "tv_measured_vs_poly": {"exact": round(tv(dm, dpx), 4), "json": ref and ref["tv_measured_vs"]["poly_exact_th2"]},
    }
    print(json.dumps(out))
    (Path(__file__).with_name("results")).mkdir(exist_ok=True)
    with open(Path(__file__).with_name("results") / "midpoly_exact.jsonl", "a") as fh:
        fh.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
