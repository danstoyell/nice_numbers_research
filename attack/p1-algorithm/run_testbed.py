#!/usr/bin/env python3
"""Run edge vs overlap-join on the k-nice testbed and nice numbers (K=1).

For each case: pick configurations with the random-digit model, run the C
enumerator (2 threads), verify every reported hit with exact Python integers
(independent of the C code), compare with the known complete solution lists,
and record counts, timings, and model predictions.

Usage: python3 run_testbed.py thrice 9 14      (K=3 bases 9..14)
       python3 run_testbed.py twice 5 20
       python3 run_testbed.py nice 20 40
Results are appended/merged into testbed.json.
"""
import json
import math
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import candidate_intervals  # noqa: E402

BIN = HERE / "overlap"
OUT = HERE / "testbed.json"
THREADS = 2
# measured per-operation costs (ns, one core), used only to rank configurations
C_TOP, C_BOT, C_PAIR, C_FULL = 40.0, 10.0, 5.0, 100.0
EDGE_FULL_LIMIT = 2e9      # above this many edge leaves, count leaves only (ops are the metric)


def pk_table(b, K, gmax):
    """P_K(g) for g <= gmax: g uniform digits, no value more than K times."""
    base = [Fraction(1, math.factorial(j)) for j in range(K + 1)]
    poly = [Fraction(1)]
    for _ in range(b):
        new = [Fraction(0)] * min(len(poly) + K, gmax + 1)
        for i, a in enumerate(poly):
            for j, c in enumerate(base):
                if i + j < len(new):
                    new[i + j] += a * c
        poly = new
    return [float(poly[g] * math.factorial(g) / Fraction(b) ** g) if g < len(poly) else 0.0
            for g in range(gmax + 1)]


def ndig(n, b):
    c = 0
    while n:
        n //= b
        c += 1
    return c


def is_k_nice(n, b, K):
    cnt = Counter()
    for x in (n * n, n ** 3):
        while x:
            x, d = divmod(x, b)
            cnt[d] += 1
    return len(cnt) == b and all(v == K for v in cnt.values())


def cases(kind, lo_b, hi_b):
    if kind == "nice":
        for b in range(lo_b, hi_b + 1):
            ivs = candidate_intervals(b)
            if not ivs or b % 4 == 3:
                continue
            iv, = ivs
            yield b, 1, iv["lo"], iv["hi"], iv["square_digits"], iv["cube_digits"], ([69] if b == 10 else [])
        return
    K = {"twice": 2, "thrice": 3}[kind]
    rows = json.loads((ROOT / f"critique/results/{kind}-nice.json").read_text())["rows"]
    for r in rows:
        if r.get("searched") and lo_b <= r["base"] <= hi_b:
            yield (r["base"], K, int(r["lo"]), int(r["hi"]), r["square_digits"], r["cube_digits"],
                   sorted(int(x) for x in r["solutions"]))


def model(b, K, lo, hi, L, P):
    N = hi - lo + 1
    out = {"edge": [], "join": []}
    for t in range(1, L):
        k = L - t
        g = 2 * (t - 1) + 2 * k
        tl = N / b ** (L - t) * P[2 * (t - 1)]
        bl = b ** k * P[2 * k]
        leaves = N * P[g]
        # trie visits ~ |B| * sum_j (top nodes at depth j jointly ok) ~ leaves * (1 + 1/b + ...)
        cost = C_TOP * b * tl / b + C_BOT * bl + C_PAIR * leaves * (1 + 1 / b) + C_FULL * leaves
        out["edge"].append({"t": t, "k": k, "cert": g, "T": tl, "B": bl, "leaves": leaves, "ns": cost})
    for t in range(2, L + 1):
        for k in range(1, L):
            if t + k <= L:
                continue
            gT = 2 * (t - 1)
            gB = 2 * k
            if gT + gB >= len(P):
                continue
            tl = N / b ** (L - t) * P[gT]
            tcalls = b * N / b ** (L - t + 1) * P[max(gT - 2, 0)]
            bl = b ** k * P[gB]
            bcalls = b * b ** (k - 1) * P[max(gB - 2, 0)]
            matches = N * P[gT] * P[gB]
            surv = N * P[gT + gB]
            cost = C_TOP * tcalls + C_BOT * bcalls + C_PAIR * matches + C_FULL * surv
            out["join"].append({"t": t, "k": k, "o": t + k - L, "cert": gT + gB, "T": tl, "B": bl,
                                "matches": matches, "survivors": surv, "ns": cost})
    return out


def choose_p(b, o, bl):
    for p in range(0, o + 1):
        if b ** (o - p) <= 3e7 and bl / b ** p <= 4e7:
            return p
    return None


def run(args):
    res = subprocess.run([str(BIN)] + [str(a) for a in args], capture_output=True, text=True)
    if res.returncode:
        raise RuntimeError(res.stderr)
    return json.loads(res.stdout)


def main():
    kind, lo_b, hi_b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    n_join = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    db = json.loads(OUT.read_text()) if OUT.exists() else {}
    for b, K, lo, hi, s, c, known in cases(kind, lo_b, hi_b):
        if hi ** 3 >= 2 ** 128 or ndig(lo, b) != ndig(hi, b):
            continue
        L = ndig(hi, b)
        if L < 3:
            continue
        P = pk_table(b, K, K * b)
        m = model(b, K, lo, hi, L, P)
        row = {"kind": kind, "base": b, "mult": K, "lo": lo, "hi": hi, "N": hi - lo + 1, "L": L,
               "square_digits": s, "cube_digits": c, "known_solutions": known,
               "model_final_probability": P[K * b] if K * b < len(P) else None}
        # edge: best split by model, run it (full checks when affordable)
        e = min(m["edge"], key=lambda x: x["ns"])
        full = 1 if e["leaves"] <= EDGE_FULL_LIMIT else 0
        er = run(["edge", b, K, lo, hi, s, c, e["t"], e["k"], THREADS, full])
        er["model"] = e
        if full:
            got = sorted(er["solutions"])
            assert got == known, (b, K, got, known)
        row["edge"] = er
        # join: best few by model
        joins = []
        for j in sorted(m["join"], key=lambda x: x["ns"])[: 3 * n_join]:
            p = choose_p(b, j["o"], j["B"])
            if p is None:
                continue
            jr = run(["join", b, K, lo, hi, s, c, j["t"], j["k"], p, THREADS])
            jr["model"] = j
            got = sorted(jr["solutions"])
            for n in got:
                assert is_k_nice(n, b, K), (b, K, n)
            assert got == known, (b, K, got, known)
            joins.append(jr)
            if len(joins) >= n_join:
                break
        row["joins"] = joins
        best = min(joins, key=lambda x: x["sec_wall"])
        row["best_join"] = {k: best[k] for k in ("t", "k", "overlap", "partition_digits", "top_calls",
                                                 "bottom_calls", "matches", "survivors", "sec_wall")}
        row["verified_exact"] = True
        edge_ops = er["top_calls"] + er["bottom_calls"] + er["trie_visits"] + er["leaves"]
        join_ops = best["top_calls"] + best["bottom_calls"] + best["matches"] + best["survivors"]
        row["ratio_full_checks"] = er["leaves"] / max(best["survivors"], 1)
        row["ratio_ops"] = edge_ops / join_ops
        edge_sec = er["sec_walk"] + er["sec_top"] + er["sec_bottom"]
        if not full:  # add measured-rate estimate for the unperformed full checks
            edge_sec += er["leaves"] * C_FULL * 1e-9 / THREADS
            row["edge_seconds_includes_estimated_full_checks"] = True
        row["edge_seconds"] = edge_sec
        row["ratio_seconds"] = edge_sec / max(best["sec_wall"], 1e-3)
        db[f"{kind}-{b}"] = row
        OUT.write_text(json.dumps(db, indent=1) + "\n")
        print(f"{kind} b={b} K={K} N={row['N']:.2e} L={L} sols={len(known)} | edge t,k={e['t']},{e['k']} "
              f"leaves={er['leaves']:.3e} {edge_sec:.1f}s | join t,k,p={best['t']},{best['k']},{best['partition_digits']} "
              f"matches={best['matches']:.3e} surv={best['survivors']:.3e} {best['sec_wall']:.1f}s | "
              f"ratio full={row['ratio_full_checks']:.1f} ops={row['ratio_ops']:.2f} sec={row['ratio_seconds']:.2f}",
              flush=True)


if __name__ == "__main__":
    main()
