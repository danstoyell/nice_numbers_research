#!/usr/bin/env python3
"""Residual gain of the overlap join over the public client, bases 57-64.

Client: exact per-n operation rates sampled with client_count256
(sample_client.py -> client_sample.json), times N. Operations = MSD analyses
+ stride visits + full checks.

Join: operations = top calls + bottom calls + digit-sum lookups + matches +
survivors, for a search region of S consecutive n and prefixes of t digits,
residues of k digits, o = t + k - L > 0 shared digits:

  top calls    = sum_{j=1..t} b * (S / b^(L-j+1)) * p_top(j-1, cap k)   (prefixes finer than S)
  bottom calls = sum_{j=1..k} b * min(b^(j-1), S) * p_bot(j-1)          (rebuilt per region)
  |T| = S / b^(L-t) * p_top(t, k),  |B| = min(b^k, S) * p_bot(k)
  lookups      = min(|T|, |B|) * (#digit-sum classes)
  matches      = S * p_match(t, k),  survivors = S * p_surv(t, k)

Two sources for the rates p: "mc" = measured by join_mc (exact certification
rules, uniform random n; join_mc.json), and "analytic" = uniform-digit model
of attack/p1-algorithm/cost_model.py (p_top(j) = P(2(j-1)), p_bot(k) = P(2k),
matches = F/N * P(2(t-1)) * P(2k | last pair)). Regions: S = N (whole
interval, P1's setting; needs a job type other than contiguous ranges) and
S = the production field size 1e14 (the client's chunk interface: the bottom
list is rebuilt for every field). Totals = per-region cost * N / S.

Usage: python3 model_gain.py            Output: model_gain.json and tables.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "critique/scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
from reachability import filtered_counts, digit_sum_roots, log_expected  # noqa: E402
from verify import candidate_intervals  # noqa: E402

LN10 = math.log(10)
FIELD = 1e14                     # production nice-only field size at base 57 (data.nicenumbers.net, 2026-09-27)
UNIT = {"top_calls": 1, "bottom_calls": 1, "lookups": 1, "matches": 1, "survivors": 1}
# Sensitivity weights (ns per operation): P1's measured C costs for the join
# (top 40, bottom 10, pair 5, full check 100); for the client a stride visit
# is weighted like a join pair (5), a full check like a join survivor (100),
# an MSD analysis 1000 (4 wide products, ~2b digit extractions, Hall matching).
JOIN_NS = {"top_calls": 40, "bottom_calls": 10, "lookups": 5, "matches": 5, "survivors": 100}
CLIENT_NS = {"analyses": 1000, "visits": 5, "full_checks": 100}


def lp(b, g, start=0):
    return sum(math.log1p(-i / b) for i in range(start, g)) if g <= b else -math.inf


def ndig(n, b):
    c = 0
    while n:
        n //= b
        c += 1
    return c


def base_info(b):
    iv, = candidate_intervals(b)
    lo, hi = iv["lo"], iv["hi"]
    z, nz = filtered_counts(b, lo, hi)
    return {"b": b, "lo": lo, "hi": hi, "N": hi - lo + 1, "L": ndig(hi, b), "F": z + nz,
            "roots": len(digit_sum_roots(b)), "lE": log_expected(b, z, nz)}


class AnalyticRates:
    def __init__(self, info):
        self.i = info
        self.b = info["b"]

    def top(self, j, cap):
        return math.exp(lp(self.b, max(2 * (j - 1), 0))) if j > 0 else 1.0

    def bot(self, j):
        return math.exp(lp(self.b, 2 * j)) if j > 0 else 1.0

    def match(self, t, k):
        return self.i["F"] / self.i["N"] * math.exp(lp(self.b, 2 * (t - 1)) + lp(self.b, 2 * k, 2))

    def surv(self, t, k):
        return self.i["F"] / self.i["N"] * math.exp(lp(self.b, 2 * (t - 1) + 2 * k, 2))


class MCRates:
    def __init__(self, info, mc):
        self.i, self.mc, self.b = info, mc, info["b"]
        self.n = mc["n"]
        self.an = AnalyticRates(info)

    def top(self, j, cap):
        return self.mc["top"][j][cap] / self.n if j > 0 else 1.0

    def bot(self, j):
        return self.mc["bot"][j] / self.n if j > 0 else 1.0

    def match(self, t, k):
        c = self.mc["match"][t][k]
        return c / self.n if c >= 20 else None

    def surv(self, t, k):
        c = self.mc["surv"][t][k]
        if c >= 20:
            return c / self.n
        m = self.match(t, k)   # too few events: analytic survivors scaled by the measured/analytic match ratio
        return self.an.surv(t, k) * (m / self.an.match(t, k) if m else 1.0)


def join_cost(info, R, S, t, k):
    b, L, N = info["b"], info["L"], info["N"]
    m = math.log(S) / math.log(b)
    if L - t >= m or t + k <= L or k >= L:
        return None
    pm = R.match(t, k)
    if pm is None:
        return None
    tc = sum(b * S / b ** (L - j + 1) * R.top(j - 1, k) for j in range(1, t + 1) if L - j + 1 < m)
    T = S / b ** (L - t) * R.top(t, k)
    bc = sum(b * min(b ** (j - 1), S) * R.bot(j - 1) for j in range(1, k + 1))
    Bs = min(b ** k, S) * R.bot(k)
    c = {"t": t, "k": k, "o": t + k - L, "top_calls": tc, "bottom_calls": bc,
         "lookups": min(T, Bs) * info["roots"], "matches": S * pm, "survivors": S * R.surv(t, k),
         "T": T, "B": Bs}
    scale = N / S
    for x in ("top_calls", "bottom_calls", "lookups", "matches", "survivors", "T", "B"):
        c[x + "_total"] = c[x] * scale
    return c


def best_join(info, R, S, w=UNIT):
    best = None
    for t in range(2, info["L"] + 1):
        for k in range(1, info["L"]):
            c = join_cost(info, R, S, t, k)
            if c is None:
                continue
            c["cost"] = sum(w[x] * c[x + "_total"] for x in w)
            c["ops"] = sum(c[x + "_total"] for x in UNIT)
            if best is None or c["cost"] < best["cost"]:
                best = c
    return best


def main():
    samples = json.loads((HERE / "client_sample.json").read_text()) if (HERE / "client_sample.json").exists() else {}
    mcs = json.loads((HERE / "join_mc.json").read_text()) if (HERE / "join_mc.json").exists() else {}
    out = {"field_size": FIELD, "bases": {}}
    hdr = f"{'b':>3} {'rates':>8} {'region':>6} | {'join (t,k,o)':>12} {'log10 ops':>9} | " + " | ".join(
        f"{c:>7}" for c in ("cpu", "gpu62k", "gpu250k", "gpu500k"))
    print("Gain = client ops / join ops (unit operations); in brackets the ns-weighted gain")
    print(hdr)
    for b in (57, 58, 60, 62, 64):
        info = base_info(b)
        N = info["N"]
        rates = {"analytic": AnalyticRates(info)}
        if str(b) in mcs:
            rates["mc"] = MCRates(info, mcs[str(b)])
        row = {"N": N, "L": info["L"], "F": info["F"], "digit_sum_classes": info["roots"],
               "log10_expected_nice": info["lE"] / LN10, "client": {}, "join": {}}
        for cfg in ("cpu", "gpu62k", "gpu250k", "gpu500k"):
            s = samples.get(f"{b}:{cfg}")
            if s:
                pn = s["per_n"]
                row["client"][cfg] = {"ops": s["total_ops"], "log10_ops": math.log10(s["total_ops"]),
                                      "ns": N * sum(CLIENT_NS[x] * pn[x] for x in CLIENT_NS),
                                      "per_n": pn, "rel_se": s["rel_se_ops"], "cert_per_visit": s["cert_per_visit"]}
        for rname, R in rates.items():
            for region, S in (("N", N), ("1e14", FIELD)):
                j = best_join(info, R, S)
                jw = best_join(info, R, S, JOIN_NS)
                key = f"{rname}:{region}"
                row["join"][key] = {"unit_best": j, "ns_best": jw,
                                    "gain": {c: v["ops"] / j["ops"] for c, v in row["client"].items()},
                                    "gain_ns": {c: v["ns"] / jw["cost"] for c, v in row["client"].items()}}
                g = row["join"][key]
                cells = " | ".join(f"{g['gain'].get(c, float('nan')):6.1f} [{g['gain_ns'].get(c, float('nan')):4.1f}]"
                                   for c in ("cpu", "gpu62k", "gpu250k", "gpu500k"))
                print(f"{b:>3} {rname:>8} {region:>6} | ({j['t']:>2},{j['k']:>2},{j['o']:>2}) {math.log10(j['ops']):9.2f} | {cells}")
        for c, v in row["client"].items():
            print(f"    client {c}: log10 ops {v['log10_ops']:.2f} (+-{100 * v['rel_se']:.0f}%), cert/visit {v['cert_per_visit']:.1f}")
        out["bases"][b] = row
    (HERE / "model_gain.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
