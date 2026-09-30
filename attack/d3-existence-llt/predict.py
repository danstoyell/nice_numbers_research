#!/usr/bin/env python3
"""Compare k-(1,2)-nice counts with the multinomial-mode prediction.

Reads results/counts_*.jsonl (output of count_knice.c) and writes
results/comparison.json and a markdown table to stdout.

Predictions for a base b and multiplicity k (band = the exact set of roots n
for which n and n^2 have s and c digits with s + c = kb):

  basic   = band * rho * P_mult,
            P_mult = (kb)! / ((k!)^b * b^(kb))   (mode of the uniform multinomial),
            rho    = #{x mod b-1 : x + x^2 = k*b(b-1)/2 (mod b-1)}
            (the digit-sum congruence concentrates the mass on rho of the b-1
            residue classes of n + n^2, each with (b-1) times the density).

  refined = the same with the e_b lowest and e_t highest digits of n and of n^2
            given their exact joint law (lowest digits from n mod b^e_b; highest
            digits from n uniform on the band), the remaining digits iid uniform,
            and the congruence conditioned exactly in that model:
            band * (rho/(b-1)) * P(X = k*1) / P(sum_d d X_d = t mod b-1).

Both are heuristics: they are what a local limit theorem in the regime
k -> infinity (b fixed) predicts to leading order (basic) and with the O(1/k)
edge corrections included (refined).  1 core, a few seconds.
"""
import json, math, glob, sys, os
from fractions import Fraction
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def digits(x, b, length):
    out = []
    for _ in range(length):
        out.append(x % b)
        x //= b
    return out  # least significant first


def rho(b, k):
    if b == 2:
        return 1, 0
    m = b - 1
    t = (k * b * (b - 1) // 2) % m
    return sum(1 for x in range(m) if (x + x * x) % m == t), t


def log_pmult(m, y, b):
    """log of multinomial pmf with m trials, uniform over b cells, at y."""
    if any(v < 0 for v in y) or sum(y) != m:
        return None
    return math.lgamma(m + 1) - sum(math.lgamma(v + 1) for v in y) - m * math.log(b)


def edge_law(b, s, c, lo, hi, eb, et, grid=1 << 16):
    """Joint law of the count vector contributed by the eb lowest and et highest
    digits of n (s digits) and of n^2 (c digits), n uniform on [lo, hi).
    Low and high parts treated as independent.  Returns Counter{tuple: prob},
    and also the law of the digit-sum of the edge digits mod b-1 is implicit."""
    low = Counter()
    M = b ** eb
    for r in range(M):
        v = [0] * b
        for d in digits(r, b, eb):
            v[d] += 1
        for d in digits((r * r) % M, b, eb):
            v[d] += 1
        low[tuple(v)] += Fraction(1, M)
    high = Counter()
    band = hi - lo
    G = min(grid, band)
    for j in range(G):
        n = lo + (band * (2 * j + 1)) // (2 * G)
        v = [0] * b
        for d in digits(n // b ** (s - et), b, et):
            v[d] += 1
        for d in digits((n * n) // b ** (c - et), b, et):
            v[d] += 1
        high[tuple(v)] += 1
    law = Counter()
    for vl, pl in low.items():
        for vh, ch in high.items():
            law[tuple(a + bb for a, bb in zip(vl, vh))] += float(pl) * ch / G
    return law


def refined_prediction(b, k, s, c, lo, hi, eb, et):
    law = edge_law(b, s, c, lo, hi, eb, et)
    m_mid = s + c - 2 * (eb + et)
    target = [k] * b
    p_hit = 0.0
    for v, p in law.items():
        y = [target[d] - v[d] for d in range(b)]
        lp = log_pmult(m_mid, y, b)
        if lp is not None:
            p_hit += p * math.exp(lp)
    if b == 2:
        return (hi - lo) * p_hit
    # model probability that sum_d d*X_d = t (mod b-1): edge law x (uniform digits)^m_mid
    m = b - 1
    r, t = rho(b, k)
    # distribution of edge digit-sum mod m
    edge_mod = [0.0] * m
    for v, p in law.items():
        edge_mod[sum(d * v[d] for d in range(b)) % m] += p
    # middle: each uniform digit d contributes d mod m; convolve m_mid times via characters
    p_cong = 0.0
    for j in range(m):
        w = complex(math.cos(2 * math.pi * j / m), math.sin(2 * math.pi * j / m))
        mid_char = (sum(w ** d for d in range(b)) / b) ** m_mid
        edge_char = sum(edge_mod[a] * w ** a for a in range(m))
        p_cong += (edge_char * mid_char * w ** (-t)).real / m
    return (hi - lo) * (r / m) * p_hit / p_cong


def main():
    rows = []
    seen = set()
    for f in sorted(glob.glob(os.path.join(HERE, "results", "counts_*.jsonl"))):
        for line in open(f):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if not d.get("band"):
                continue
            key = (d["b"], d["k"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(d)
    rows.sort(key=lambda d: (d["b"], d["k"]))
    out = []
    print("| b | k | s | c | band | tested | hits | observed count (est.) | rho | basic prediction | obs/basic | refined prediction | obs/refined | refined, 3 edge digits | obs/refined3 |")
    print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for d in rows:
        b, k, s, c, lo, hi = d["b"], d["k"], d["s"], d["c"], d["lo"], d["hi"]
        band = hi - lo
        r, t = rho(b, k)
        pm = math.exp(math.lgamma(k * b + 1) - b * math.lgamma(k + 1) - k * b * math.log(b))
        basic = band * r * pm
        eb = et = 1 if s <= 5 else 2
        ref = refined_prediction(b, k, s, c, lo, hi, eb, et)
        ref3 = refined_prediction(b, k, s, c, lo, hi, 3, 3) if s >= 8 else float("nan")
        obs = d["hits"] * band / d["tested"]
        err = (math.sqrt(d["hits"]) * band / d["tested"]) if d["hits"] else float("nan")
        rec = dict(b=b, k=k, s=s, c=c, band=band, tested=d["tested"], hits=d["hits"],
                   observed=obs, observed_sd=err, sampled=d["sampled"], rho=r, t=t, P_mult=pm,
                   basic=basic, ratio_basic=obs / basic, refined=ref, ratio_refined=obs / ref,
                   refined3=ref3, ratio_refined3=obs / ref3,
                   edge_digits=dict(low=eb, high=et))
        out.append(rec)
        est = f"{obs:,.0f} ± {err:,.0f}" if d["sampled"] else f"{obs:,.0f}"
        print(f"| {b} | {k} | {s} | {c} | {band:,} | {d['tested']:,} | {d['hits']:,} | {est} | {r} | {basic:,.1f} | {obs/basic:.3f} | {ref:,.1f} | {obs/ref:.3f} | {ref3:,.1f} | {obs/ref3:.3f} |")
    json.dump(out, open(os.path.join(HERE, "results", "comparison.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
