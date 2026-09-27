#!/usr/bin/env python3
"""Exponent bookkeeping for Path 2 (existence proof).  Single core, numpy/scipy only.

Everything here concerns the *reference model* (i.i.d. uniform digits) or exact
identities; nothing here is evidence about actual nice numbers.

Sections
  1. candidate count N_b, model probability, required power saving eta*(b)
  2. threshold for square-root cancellation to suffice
  3. composition collision rate rho_b  (generic Parseval / L2 on the torus)
  4. absolute mass of the model on the torus  int |phi|^m  vs the target m!/b^m
     (shows upper bounds alone can never close: the main term is produced by
      oscillation, so an asymptotic with exponentially small error is needed)
  5. Cramer rate for |phi(theta)| and the "major region" threshold kappa_0
  6. Fourier L1 of the permutation indicator on Z/b^b (small b, exact FFT)
  7. derived thresholds (Fourier-L1, cylinder, Bonferroni, Weyl/ETK, union bound)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import optimize, special

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

OUT = Path(__file__).resolve().parent / "results" / "bookkeeping.json"


def admissible(b):
    return b % 4 != 3 and b % 5 != 1 and b >= 4


def log_interval_length(b):
    """ln N_b, N_b = |I_b|, from the exact endpoint exponents (obstructions.length_interval)."""
    q, rem = divmod(b - 2, 5)
    hi_frac, gap = {0: (1 / 3, 1 / 3), 1: (1 / 2, 1 / 6),
                    2: (2 / 3, 1 / 6), 3: (1.0, 1 / 3)}[rem]
    lb = math.log(b)
    return (q + hi_frac) * lb + math.log1p(-math.exp(-gap * lb))


def log_model_probability(b):
    """ln of the uncorrected reference probability b!/b^b (leading-zero and
    digit-sum corrections change this by a factor bounded by O(b); see
    research/existence-counting.md for the corrected version)."""
    return math.lgamma(b + 1) - b * math.log(b)


# ---------------------------------------------------------------- section 1, 2
def section_required_saving():
    rows = []
    for b in [10, 57, 150, 500, 1000, 10**4, 22027, 10**5, 10**6, 10**9, 10**12, 10**20]:
        lnN = log_interval_length(b)
        lnp = log_model_probability(b)
        # sup-norm target: |S - N Phi| <= N^(1-eta) <= (N p)/2
        eta_sup = (math.log(2) - lnp) / lnN
        rows.append({"b": b, "ln_N": lnN, "log10_N": lnN / math.log(10),
                     "ln_model_prob": lnp, "log10_expected": (lnN + lnp) / math.log(10),
                     "eta_star_sup": eta_sup, "five_over_ln_b": 5 / math.log(b)})
    # square-root cancellation threshold: sqrt(N) * slack < N p
    thresholds = {}
    for label, slack in [("sqrtN", lambda b: 0.0),
                         ("sqrt(N b ln b)", lambda b: 0.5 * math.log(b * math.log(b)))]:
        first = None
        for b in range(10, 200000):
            if not admissible(b):
                continue
            lnN = log_interval_length(b)
            if 0.5 * lnN + slack(b) < lnN + log_model_probability(b):
                # require it to hold for the next 50 admissible bases too
                ok = all(0.5 * log_interval_length(c) + slack(c)
                         < log_interval_length(c) + log_model_probability(c)
                         for c in range(b, b + 200) if admissible(c))
                if ok:
                    first = b
                    break
        thresholds[label] = first
    return {"rows": rows, "sqrt_cancellation_sufficient_from_b": thresholds,
            "e^10": math.exp(10)}


# ------------------------------------------------------- power series helper
def log_coeff_power(m, b, kmax=None):
    """ln [x^m] A(x)^b with A(x) = sum_k x^k/(k!)^2, via saddle-point rescaling and
    exact (float, no cancellation) truncated convolution powers."""
    if kmax is None:
        kmax = m
    ks = np.arange(kmax + 1)
    loga = -2 * special.gammaln(ks + 1)

    def mean_at(logx):
        w = loga + ks * logx
        w -= w.max()
        p = np.exp(w)
        return (ks * p).sum() / p.sum()
    target = m / b
    logx0 = optimize.brentq(lambda t: mean_at(t) - target, -60, 60)
    w = loga + ks * logx0
    lse = np.logaddexp.reduce(w)
    p = np.exp(w - lse)                 # probability vector (tilted)
    # b-fold convolution power truncated at degree m, by binary powering
    result = np.zeros(m + 1)
    result[0] = 1.0
    base = p[: m + 1].copy()
    e = b
    while e:
        if e & 1:
            result = np.convolve(result, base)[: m + 1]
        e >>= 1
        if e:
            base = np.convolve(base, base)[: m + 1]
    val = result[m]
    return math.log(val) + b * lse - m * logx0


def section_collision_rate():
    rows = []
    for b in [10, 20, 50, 100, 200, 400, 800, 1600]:
        lc = log_coeff_power(b, b)
        lrho = 2 * math.lgamma(b + 1) - 2 * b * math.log(b) + lc
        rows.append({"b": b, "ln_rho": lrho, "rate_per_b": lrho / b})
    # limiting rate: -2 + ln(A(x0)/x0), x0 A'(x0)/A(x0) = 1
    ks = np.arange(200)
    loga = -2 * special.gammaln(ks + 1)

    def mean_at(logx):
        w = loga + ks * logx
        w -= w.max()
        p = np.exp(w)
        return (ks * p).sum() / p.sum()
    lx = optimize.brentq(lambda t: mean_at(t) - 1, -10, 10)
    rate = -2 + np.logaddexp.reduce(loga + ks * lx) - lx
    return {"rows": rows, "limit_rate": float(rate),
            "needed_rate_for_generic_parseval": -2.0,
            "missing_factor_rate": float(-(rate / 2) - 1)}


# ------------------------------------------------------------- section 4, 5
def log_abs_mass(mdig, b):
    """ln int_{T^b} |phi(theta)|^mdig dtheta for mdig even, phi = (1/b) sum_a e(theta_a).
    = ln( (k!)^2 [x^k] A(x)^b / b^(2k) ), k = mdig/2."""
    k = mdig // 2
    return 2 * math.lgamma(k + 1) + log_coeff_power(k, b) - 2 * k * math.log(b)


def cramer_rate(kappa):
    """I(kappa) = sup_l (l*kappa - ln I0(l)) for the mean of i.i.d. uniform unit vectors."""
    f = lambda l: -(l * kappa - (np.log(special.i0e(l)) + l))
    res = optimize.minimize_scalar(f, bounds=(0, 1e6), method="bounded",
                                   options={"xatol": 1e-10})
    return -res.fun


def section_abs_mass():
    rows = []
    for beta in [1.0, 0.6]:
        for b in [50, 100, 200, 400, 800, 1600]:
            mdig = int(round(beta * b))
            if mdig % 2:
                mdig += 1
            lmass = log_abs_mass(mdig, b)
            ltarget = math.lgamma(mdig + 1) - mdig * math.log(b)
            rows.append({"beta": beta, "b": b, "m": mdig,
                         "ln_abs_mass_per_b": lmass / b,
                         "ln_target_per_b": ltarget / b,
                         "excess_per_b": (lmass - ltarget) / b})
    # limiting exponents from the Cramer rate
    kappas = np.linspace(0.01, 0.99, 981)
    I = np.array([cramer_rate(k) for k in kappas])
    out = {"rows": rows, "limits": {}}
    for beta in [1.0, 0.6]:
        vals = beta * np.log(kappas) - I
        j = int(np.argmax(vals))
        target = beta * math.log(beta) - beta
        above = kappas[vals > target]
        out["limits"][str(beta)] = {
            "max_over_kappa_of_beta_ln_kappa_minus_I": float(vals[j]),
            "argmax_kappa": float(kappas[j]),
            "target_rate_beta_ln_beta_minus_beta": target,
            "excess_rate": float(vals[j] - target),
            "asymptotics_needed_for_kappa_in": [float(above.min()), float(above.max())]
            if above.size else None,
            "measure_rate_of_that_region": float(cramer_rate(float(above.min())))
            if above.size else None,
        }
    out["cramer_rate_samples"] = {f"{k:.2f}": cramer_rate(k) for k in
                                  [0.1, 0.2, 0.3, 0.45, 0.5, 0.7, 0.9]}
    return out


# ------------------------------------------------------------------ section 6
def section_fourier_l1():
    from itertools import permutations
    rows = []
    for b in range(3, 8):
        M = b ** b
        ind = np.zeros(M)
        pw = [b ** i for i in range(b)]
        for perm in permutations(range(b)):
            ind[sum(d * p for d, p in zip(perm, pw))] = 1.0
        F = np.fft.fft(ind)            # P_hat(a) = sum_{x in P} e(-a x / M)
        P = math.factorial(b)
        L1 = np.abs(F).sum()            # = sum_a |P_hat(a)|
        R = L1 / P                      # (sum |c_a|) / c_0
        rows.append({"b": b, "M": M, "P": P, "R_L1_over_main": R,
                     "ln_R_over_ln_M": math.log(R) / math.log(M),
                     "M_over_sqrtP": M / math.sqrt(P),
                     "R_over_(M/sqrtP)": R / (M / math.sqrt(P))})
    return rows


# ------------------------------------------------------------------ section 7
def section_derived():
    d = {}
    # Fourier L1 of 1_P ~ M/sqrt|P| relative to main term; saving needed from S(a):
    # N^eta > M / sqrt(P)  ->  eta > (ln M - 0.5 ln P)/ln N  ~ 5/2 + 5/(2 ln b)
    for b in [100, 10**4, 10**8]:
        lnM = b * math.log(b)
        lnP = math.lgamma(b + 1)
        lnN = log_interval_length(b)
        eta_full = (lnM - 0.5 * lnP) / lnN
        # bottom 2L digits exact (bilinear n = H b^j + L): only the 3L = 0.6 b
        # remaining digits are Fourier-expanded
        m = 0.6 * b
        eta_bilinear = (m * math.log(b) - 0.5 * math.lgamma(m + 1)) / lnN
        d[f"fourier_L1_eta_needed_b={b}"] = {"all_digits": eta_full,
                                             "top_60_percent_only": eta_bilinear}
    # middle-block completion probability (3L digits must be a permutation of a given 3L-set)
    d["middle_completion_rate_per_b"] = 0.6 * (math.log(0.6) - 1)
    # union-bound (W*) requirement: N^eta >= 3^{|Mid|} e^b, |Mid| <= b
    d["Wstar_eta_times_ln_b"] = 5 * (1 + math.log(3))
    # Bonferroni remainder at the information cap r = L = b/5 for collision pairs
    # (mean number of collisions mu = (b-1)/2):  mu^L / L!  ~ exp((b/5)(1+ln(5/2)))
    d["collision_bonferroni_remainder_rate_at_depth_L"] = 0.2 * (1 + math.log(2.5))
    # Weyl + Erdos-Turan-Koksma coverage: |T| < (2 sigma / 5) b
    d["weyl_ETK_max_fraction_of_positions"] = {"sigma=1/6 (Vinogradov MVT, d=3)": 2 / 30,
                                               "sigma=1/(11*9*ln3) (DMR Lemma 3)":
                                                   2 / (5 * 11 * 9 * math.log(3)),
                                               "sigma=1/2 (square-root)": 1 / 5}
    # split of the pandigital exponent b!/b^b = prod_{j<b}(1-j/b) at 2L = 0.4 b:
    #   bottom 2L output digits distinct (model)            int_0^0.4 ln(1-x) dx
    #   bottom 2L distinct, rigorous line-lemma lower bound int_0^0.2 ln(1-4x) dx
    #   remaining 3L digits complete the permutation (model) int_0.4^1 ln(1-x) dx
    F = lambda u: (u * math.log(u) - u) if u > 0 else 0.0   # antiderivative of ln u
    d["edge_split_rates_per_b"] = {
        "bottom_40pct_model": F(1.0) - F(0.6),
        "bottom_40pct_rigorous_line_lemma": (F(1.0) - F(0.2)) / 4,
        "middle_60pct_model": F(0.6) - F(0.0),
    }
    # DMR q0(3) bound
    d["DMR_q0(3)_ln_upper_bound"] = 67 * 27 * math.log(3) ** 2
    d["eta_star_at_b=q0(3)"] = 5 / (67 * 27 * math.log(3) ** 2)
    return d


def main():
    res = {"required_saving": section_required_saving()}
    print(json.dumps(res["required_saving"], indent=1))
    res["collision_rate"] = section_collision_rate()
    print(json.dumps(res["collision_rate"], indent=1))
    res["abs_mass"] = section_abs_mass()
    print(json.dumps(res["abs_mass"], indent=1))
    res["fourier_L1_permutation_indicator"] = section_fourier_l1()
    print(json.dumps(res["fourier_L1_permutation_indicator"], indent=1))
    res["derived"] = section_derived()
    print(json.dumps(res["derived"], indent=1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
