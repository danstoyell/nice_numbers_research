# Path 3, test 2: exact k-nice counts at rarer bases

2026-09-26 to 09-29. This is pre-registered test 2 of Path 3 in [research-directions.md](../../critique/research-directions.md#the-only-lead-the-deficiency-2-shortfall). The question: if a real obstruction exists, it should suppress exact hits more and more as they get rarer. Do exact k-nice counts fall below the random-digit model as the per-candidate probability p falls?

## Verdict

**The result closes the uniqueness question as far as this test can. It does not reopen it.**

1. **The new data match the model.** Every target base was searched completely: thrice-nice 16 and 18, twice-nice 24, 25 and 26. Each of the 867 new hits was re-verified with exact Python integers.
   - Against the exact-edge model M1e: 867 observed vs 896.7 expected, ratio **0.967 (95% CI 0.90–1.03)**, P(≤ 867) = 0.16.
   - Every new base is within 1.5σ of M1e.
   - The rarest regime, p < 10⁻¹² (twice 24–26, 1.5–2 decades below anything tested before), gives **93 observed vs 88.4 expected (1.05; 0.85–1.29)**.
2. **The pre-registered model M0 shows a deficit, and it is a model gap.** Under M0 the new bases give 867 vs 966.6 (0.897), and thrice 18 alone is 533 vs 610.4 (−3.1σ). M0 is too coarse, as the critique already found for near misses (M0 was 12–15% high there):
   - using the exact top-2 and bottom-3 digits of n² and n³ lowers thrice 18 to 568.6 and thrice 16 to 239.7;
   - M1e itself is calibrated on near misses in the same bases to within 1–4%;
   - under M1e, thrice 18 is −1.5σ and thrice 16 is +0.1σ.
3. **No trend toward rarer events that could lead to a proof.** Let ratio = scale × 10^(β(log₁₀ p − x̄)), where β > 0 means suppression grows as p falls.
   - One scale across all 25 bases (the pre-registered form): **β = +0.023 ± 0.024** (M1e) and +0.011 ± 0.024 (M0). Consistent with zero.
   - A separate scale for each k (a refinement added after seeing the data): β = +0.054 ± 0.027 (M1e, one-sided p = 0.022) and +0.040 ± 0.026 (M0, p = 0.064).
   - That marginal slope comes only from the small bases with p > 10⁻⁷. With only p < 10⁻⁷ (12 bases, 925 hits) it is +0.024 ± 0.036.
   - The new rare data **lowered** it. The old data alone gave +0.128 ± 0.069. Extrapolating that old trend predicted 650 hits at the new bases; 867 were observed, against 897 for the flat model. An obstruction that bites harder on rarer events predicts the opposite.
4. **What a nonexistence proof would need.** Extrapolate the same form to nice numbers (k = 1). Removing every nice number from bases 58–300 needs β ≥ 0.18, and bases 58–600 need β ≥ 0.30. The data give β ≤ 0.105 at 95% even under the most permissive fit, so these are excluded at about 4.6σ and 9σ.
   - A trend inside the error bars (β ≈ 0.05) could suppress the roughly 345 nice numbers the model expects through base 150. It still leaves more than 10⁸ at base 300.
   - Caveat: this extrapolates across more than 100 decades of p. An obstruction that switches on only below p ≈ 10⁻¹³ cannot be tested by any analogue we can enumerate, and nothing in the data hints at one.

Together with the obstruction agent's out-of-sample kill of the deficiency-2 lead (20 vs 18.3 on bases 49–50; [p3-obstruction/REPORT.md](../p3-obstruction/REPORT.md)), **both Path 3 stop conditions are met.** The (1,2)-nice calibration ([d1-quasi-nice/REPORT.md](../d1-quasi-nice/REPORT.md): 1,930 hits at 0.990 of its refined model) points the same way.

## Results by base

- p is the M0 expectation divided by the number of integers in the interval.
- Bold bases are new; thrice 16 was run concurrently by the critique with `histogram.c` and reproduced exactly here.
- M1e Monte Carlo standard errors are 0.2–0.4% (e.g. 568.6 ± 0.9, 46.15 ± 0.09) and are ignored in the tails.
- Bases with zero M0 expectation are provable zeros (digit-sum congruence) and are left out: thrice 11 was searched and gave 0 hits.

| k | Base | Candidates | log₁₀ p | Observed | M0 | Obs/M0 | M1e | Obs/M1e (95% CI) | P(≤obs) M1e | P(≥obs) M1e |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 2 | 5 | 10 | −1.50 | 0 | 0.32 | 0.00 | — | — | — | — |
| 2 | 6 | 30 | −2.32 | 0 | 0.14 | 0.00 | — | — | — | — |
| 2 | 7 | 50 | −2.45 | 1 | 0.18 | 5.64 | 0.08 | 13.3 (0.34–73.8) | 0.997 | 0.073 |
| 2 | 9 | 670 | −3.68 | 0 | 0.14 | 0.00 | 0.13 | 0.00 (0–29.5) | 0.882 | 1.000 |
| 2 | 10 | 5,358 | −4.10 | 1 | 0.42 | 2.37 | 0.43 | 2.32 (0.06–12.9) | 0.930 | 0.350 |
| 2 | 11 | 17,921 | −4.60 | 0 | 0.45 | 0.00 | 0.40 | 0.00 (0–9.2) | 0.670 | 1.000 |
| 2 | 12 | 36,856 | −5.52 | 0 | 0.11 | 0.00 | 0.09 | 0.00 (0–42) | 0.916 | 1.000 |
| 2 | 14 | 716,121 | −6.58 | 1 | 0.19 | 5.25 | 0.18 | 5.48 (0.14–30.6) | 0.985 | 0.167 |
| 2 | 15 | 6,771,952 | −6.82 | 1 | 1.02 | 0.98 | 0.95 | 1.06 (0.03–5.88) | 0.755 | 0.612 |
| 2 | 16 | 2.55×10⁷ | −7.38 | 1 | 1.06 | 0.94 | 0.87 | 1.15 (0.03–6.42) | 0.784 | 0.580 |
| 2 | 17 | 6.01×10⁷ | −7.80 | 1 | 0.95 | 1.05 | 0.93 | 1.08 (0.03–6.02) | 0.763 | 0.604 |
| 2 | 19 | 1.51×10⁹ | −8.70 | 4 | 2.98 | 1.34 | 2.95 | 1.35 (0.37–3.47) | 0.823 | 0.343 |
| 2 | 20 | 1.62×10¹⁰ | −9.91 | 4 | 1.99 | 2.01 | 1.92 | 2.08 (0.57–5.34) | 0.954 | 0.129 |
| 2 | 21 | 6.65×10¹⁰ | −9.96 | 5 | 7.24 | 0.69 | 6.63 | 0.75 (0.24–1.76) | 0.351 | 0.790 |
| 2 | 22 | 1.73×10¹¹ | −10.70 | 5 | 3.50 | 1.43 | 3.43 | 1.46 (0.47–3.40) | 0.866 | 0.262 |
| 2 | **24** | 5.32×10¹² | −12.13 | 6 | 3.97 | 1.51 | 3.40 | 1.76 (0.65–3.84) | 0.942 | 0.130 |
| 2 | **25** | 6.28×10¹³ | −12.21 | 48 | 39.07 | 1.23 | 38.89 | 1.23 (0.91–1.64) | 0.934 | 0.087 |
| 2 | **26** | 2.77×10¹⁴ | −12.75 | 39 | 49.50 | 0.79 | 46.15 | 0.85 (0.60–1.16) | 0.164 | 0.872 |
| 3 | 5 | 51 | −2.34 | 0 | 0.23 | 0.00 | 0.18 | 0.00 (0–20.7) | 0.837 | 1.000 |
| 3 | 6 | 137 | −2.66 | 0 | 0.30 | 0.00 | 0.21 | 0.00 (0–17.5) | 0.810 | 1.000 |
| 3 | 8 | 4,798 | −3.83 | 0 | 0.71 | 0.00 | 0.47 | 0.00 (0–7.9) | 0.628 | 1.000 |
| 3 | 9 | 63,778 | −4.30 | 7 | 3.22 | 2.17 | 2.85 | 2.46 (0.99–5.06) | 0.991 | 0.026 |
| 3 | 10 | 535,841 | −4.81 | 10 | 8.37 | 1.20 | 8.11 | 1.23 (0.59–2.27) | 0.805 | 0.297 |
| 3 | 13 | 1.21×10⁸ | −6.96 | 16 | 13.15 | 1.22 | 11.89 | 1.35 (0.77–2.18) | 0.904 | 0.148 |
| 3 | 14 | 2.08×10⁹ | −7.62 | 38 | 50.21 | 0.76 | 45.67 | 0.83 (0.59–1.14) | 0.143 | 0.889 |
| 3 | **16** | 1.02×10¹¹ | −8.59 | 241 | 263.67 | 0.91 | 239.7 | 1.01 (0.88–1.14) | 0.551 | 0.475 |
| 3 | **18** | 9.37×10¹² | −10.19 | 533 | 610.39 | 0.87 | 568.6 | 0.94 (0.86–1.02) | 0.069 | 0.936 |

The M0 Poisson tails for the new bases are:

| Base | P(≤obs) under M0 | P(≥obs) under M0 |
|---|---:|---:|
| Twice 24 | 0.89 | 0.21 |
| Twice 25 | 0.93 | 0.092 |
| Twice 26 | 0.074 | 0.95 |
| Thrice 16 | 0.085 | 0.93 |
| Thrice 18 | **0.0014** | 1.00 |

**Pooled** (Garwood 95% CIs):

| Set | Observed | M0 | Obs/M0 | M1e | Obs/M1e |
|---|---:|---:|---|---:|---|
| Previously tested (critique) | 95 | 96.9 | 0.98 (0.79–1.20) | 88.4 | 1.08 (0.87–1.31) |
| New bases | 867 | 966.6 | 0.90 (0.84–0.96) | 896.7 | 0.97 (0.90–1.03) |
| New, k = 2 (bases 24–26) | 93 | 92.5 | 1.00 (0.81–1.23) | 88.4 | 1.05 (0.85–1.29) |
| New, k = 3 (bases 16, 18) | 774 | 874.1 | 0.89 (0.82–0.95) | 808.3 | 0.96 (0.89–1.03) |
| p < 10⁻¹⁰ | 631 | 706.4 | 0.89 (0.82–0.97) | 660.5 | 0.96 (0.88–1.03) |
| All bases | 962 | 1063.5 | 0.90 (0.85–0.96) | 985.1 | 0.98 (0.92–1.04) |

Twice 25 and 26 together give 87 observed vs 85.0 (M1e) and 88.6 (M0).

The full solution lists are in `results/run_k2_b24.json`, `run_k2_b25.json`, `run_k2_b26.json` and `run_k3_b18.json`, and in `results/analysis.json` for every base. The twice-nice 24 solutions are 9402707085281, 9970741307144, 10338026074971, 10957030544901, 12745356312259 and 12850463146172.

## Trend fits

The fit is Poisson maximum likelihood with μᵢ = Eᵢ · s · 10^(β(log₁₀ pᵢ − x̄)). The 95% intervals come from the profile likelihood. The code is in `analyze.py`, with outputs in `results/analysis.json` and `analysis.txt`.

| Fit | β per decade of p | 95% CI | One-sided p (β > 0) |
|---|---|---|---|
| All bases, one scale, M0 (pre-registered form) | +0.011 ± 0.024 | −0.035 to 0.057 | 0.32 |
| All bases, one scale, M1e | +0.023 ± 0.024 | −0.024 to 0.070 | 0.16 |
| All bases, scale per k, M0 | +0.040 ± 0.026 | −0.012 to 0.090 | 0.064 |
| All bases, scale per k, M1e | **+0.054 ± 0.027** | 0.000 to 0.105 | 0.022 |
| Scale per k, M1e, only p < 10⁻⁷ (12 bases, 925 hits) | +0.024 ± 0.036 | −0.048 to 0.094 | 0.26 |
| Scale per k, M1e, old data only | +0.128 ± 0.069 | −0.013 to 0.258 | 0.031 |
| k = 2 only, M1e | +0.077 ± 0.053 | −0.036 to 0.175 | 0.075 |
| k = 3 only, M1e | +0.047 ± 0.031 | −0.015 to 0.106 | 0.065 |

**How to read the one marginal fit** (scale per k, M1e, p = 0.022):

- It is one of several fit variants tried, so it has look-elsewhere cost.
- It depends on the smallest bases, where the uniform-middle model is weakest and expectations are below 1.
  - Thrice 9 (7 hits vs 2.85) carries much of it; dropping it gives +0.040 ± 0.028.
  - Restricting to p < 10⁻⁷ gives +0.024 ± 0.036.
- The new rare bases pulled it down, from 0.128 to 0.054. Under the old-data trend the new bases should have given 650 hits (scale per k, M1e); 867 were observed. The flat M1e prediction was 897.
- Its size cannot matter: β ≈ 0.05 is a factor of 1.13 per decade of p.

**Slope needed for uniqueness** (same form, scale 1 at x̄ = −9.76, applied to the critique's k = 1 expectations from `reachability.json`):

| Bases emptied | Model expectation there | β needed | Excess over the per-k M1e fit |
|---|---:|---:|---|
| 58–150 | 345 | 0.050 | not excluded |
| 58–200 | 2.8×10⁷ | 0.102 | 1.8σ |
| 58–300 | 6.2×10²⁰ | 0.179 | 4.6σ |
| 58–600 | 1.0×10⁷⁵ | 0.303 | 9.2σ |

Against the one-scale M1e fit these are 1.1σ, 3.3σ, 6.5σ and 11.8σ. The needed β keeps growing with the base, and a nonexistence proof must empty all of them.

## The thrice-18 shortfall

The observed 533 is 0.873 of M0 (610.4, P(≤) = 0.0014). The gap was traced as follows.

- **It is modelling, mostly the low digits.** M1e at several edge depths (Monte Carlo, `model.py`; `results/m1e_depth.json`):

  | Exact edges used | Expected count |
  |---|---:|
  | M0 (last digit only; leading digits uniform) | 610.4 |
  | Top 1, bottom 1 | 603.2 |
  | Top 2, bottom 1 | 593.6 |
  | Top 1, bottom 3 | 577.4 |
  | Top 2, bottom 3 (M1e) | 568.6 |
  | Top 3, bottom 4 | 564–566 |
  | Top 4, bottom 5 | 566.3 |
  | Top 5, bottom 6 | 568.2 |

  The second and third lowest digits account for about −4%, the second-highest digit about −1.6% and the leading digit about −1.2%. Deeper edges change nothing more than 1%. The same effect lowers thrice 16 from 263.7 to 239.7 (observed 241) and thrice 14 from 50.2 to 45.7 (observed 38).
- **Splitting the digit-sum congruence changes nothing.** M0 and M1e impose only n² + n³ ≡ digit sum (mod b−1). The separate congruences for the square and the cube were also imposed with an exact generating function (`model.py`: `split_ratio`, `m2split`, checked by brute force). The expectation changed by exactly 0 at bases 14–24.
- **M1e is calibrated on near misses in the same bases.** `nearmiss.c` counts every candidate's distance D = Σ|c_v − k|, and `nearmiss_model.py` computes M1e's prediction per D bin; the generating function was checked by brute force.

  | Base (coverage) | D = 0 | D = 2 | D = 4 | D = 6 |
  |---|---|---|---|---|
  | 14 (full) | 38 / 46.3 | 2,846 / 2,902 (0.981) | 100,652 / 101,050 (0.996) | 1,325,135 / 1,330,754 (0.996) |
  | 16 (5% of residues) | 7 / 11.9 | 450 / 444.0 (1.014) | 23,354 / 23,696 (0.986) | 407,828 / 411,431 (0.991) |
  | 18 (2% of residues) | 12 / 11.2 | 1,197 / 1,247 (0.960) | 71,726 / 72,386 (0.991) | 1,645,023 / 1,657,555 (0.992) |

  The near-miss counts from `nearmiss.c` matched a Python brute force exactly at thrice 9 and 10. M1e runs about 1% high at D = 4–6, which is model resolution, like the critique's M1. Allowing for that, thrice 18 is about −1.3σ.
- **The hits have no structure.** Against M1e, their last digits give χ² = 20.8 on 16 degrees of freedom, and their position deciles in the interval give χ² = 4.9 on 9.

## Enumerator and soundness

`knice.c` walks every residue class R mod S = (b−1)·b^J that survives two sound filters, as the arithmetic progression n = N₀ + R + S·t over the whole interval. Each step works on 32 classes at once in NEON byte lanes.

- **Arithmetic.** n² and n³ are base-b digit arrays, taken mod b^s and mod b^c, advanced by exact finite differences:
  - D₂ = 2nS + S², D₃ = 3n²S + 3nS² + S³, E₃ = 6nS² + 6S³;
  - the constants are 2S² and 6S³.
  - All increments are multiples of b^J, so the low J digits are fixed per class.
- **Filters,** both necessary conditions for a k-nice n:
  - *Digit-sum:* n²(n+1) ≡ k·b(b−1)/2 (mod b−1).
  - *Low digits:* no value appears more than k times among the lowest J digits of n² and n³.
- **Hit test.** A random-weight byte hash of all moving digits is compared with the class's target. It is exact for any k-nice n, and about 1/256 of candidates pass to an exact count. Hits must also lie in [lo, hi].
- **Self-check.** After each group, the final arrays are compared with a from-scratch recomputation. Any mismatch aborts; none occurred in about 6.2×10¹³ lane-steps.
- **Speed.** About 2.1 ns per candidate per P-core thread after the digit-sum filter, 40–70× faster than `histogram.c`. Thrice 16 takes 18 s wall, where `histogram.c` took 1,412 s.

**Validation** (`validate.py`, `results/validation.json`, 142 checks, all identical):

- Every searched row of `twice-nice.json` (bases 5–22) and `thrice-nice.json` (bases 5–16, including the critique's 241 thrice-16 solutions), at J = 1, 2, 3 and the production J.
- 54 of those runs had the filters off, meaning every residue was walked.
- 14 were compared against a Python brute force.

**Cross-checks on production runs** (`xcheck.py`, `results/xcheck.json`), all identical:

| Base | Sub-interval rerun with a different J | Chunks rerun with filters off |
|---|---|---|
| Thrice 18 | 5% with J = 4: 30/30 hits | 10 chunks: 2/2 hits |
| Twice 26 | 3% with J = 5: 2/2 hits | 5 chunks, 6.9×10¹¹ lane-steps: 0/0 |
| Twice 24 | 10%: 0/0 | 20 chunks: 0/0 |

Every reported hit passed `is_k_nice` with exact Python integers. The 39 twice-26 hits also passed `scripts/verify.py`'s `digits`.

## Scope, cost and budget

- **Coverage:** 100% of every target interval. Lane-steps per run:

  | Run | Lane-steps |
  |---|---:|
  | Twice 24 | 3.3×10¹¹ |
  | Thrice 18 | 1.0×10¹² |
  | Twice 25 | 1.25×10¹³ |
  | Twice 26 | 4.8×10¹³ |

- **Threads:** at most 5 for thrice 18 and twice 24, and 4 for twice 25 and 26.
- **Wall time:**

  | Run | Wall time |
  |---|---|
  | Twice 24 | 3.6 min |
  | Thrice 18 | 88 min (machine oversubscribed: load up to 65, swap full) |
  | Twice 25 | 3.4 h |
  | Twice 26 | about 13.5 h by the driver's clock, spread over 47 h elapsed (sleep and contention) |

- **Budget overrun:** this exceeded the 12 h cap. The coordinator let twice 26 finish.
- **Not run:** twice 27 (26 expected, 7.8×10¹⁴ candidates) and thrice 20 (9,357 expected, 2.6×10¹⁵ candidates) were out of budget.
- **Model notes:**
  - M0 is exactly the critique's `model_expectation` code. Partial-coverage support is exact (`m0_partial`) but was not needed.
  - M1e is a Monte Carlo refinement (2×10⁵ samples per base). The primary conclusions hold under both models.

## Files (attack/p3-analogues/)

- **Enumerator and drivers:**
  - `knice.c`: the enumerator.
  - `run.py`: compiles, runs with a checkpoint log, verifies in Python and summarises.
  - `campaign.sh`, `campaign2.sh`: the production run scripts.
  - `logs/`: per-chunk checkpoint logs.
- **Checks:**
  - `validate.py` → `results/validation.json`.
  - `xcheck.py` → `results/xcheck.json`.
- **Models:**
  - `model.py`: M0 via the critique code, M1e, partial coverage and the split-congruence check.
  - Outputs: `results/model.json`, `results/m1e_depth.json`, `results/m1e_depth34.json`.
- **Near misses:** `nearmiss.c` and `nearmiss_model.py` → `results/nearmiss.json`.
- **Analysis:** `analyze.py` → `results/analysis.json` and `results/analysis.txt` (table, fits, robustness, pooled sets, needed slope).
- **Run results:** `results/run_k2_b24.json`, `run_k2_b25.json`, `run_k2_b26.json`, `run_k3_b18.json`.

## Sources

- Pre-registered test and stop rule: [critique/research-directions.md, Path 3](../../critique/research-directions.md#the-only-lead-the-deficiency-2-shortfall).
- Earlier analogue counts, the M0 model and the M1 near-miss calibration: [critique/experiments.md §2–3](../../critique/experiments.md); [twice-nice.json](../../critique/results/twice-nice.json), [thrice-nice.json](../../critique/results/thrice-nice.json), [twice_nice.py](../../critique/scripts/twice_nice.py).
- k = 1 expectations for the needed-slope calculation: [critique/results/reachability.json](../../critique/results/reachability.json).
- Deficiency-2 lead closed out of sample: [attack/p3-obstruction/REPORT.md](../p3-obstruction/REPORT.md).
- (1,2)-nice exact calibration at 0.990: [attack/d1-quasi-nice/REPORT.md](../d1-quasi-nice/REPORT.md).
- Exact Poisson confidence intervals: F. Garwood, "Fiducial limits for the Poisson distribution", *Biometrika* 28 (1936) 437–442, [doi:10.1093/biomet/28.3-4.437](https://doi.org/10.1093/biomet/28.3-4.437).
