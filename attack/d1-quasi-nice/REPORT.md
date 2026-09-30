# D1 report: exact k = 1 calibration on (1,2)-nice numbers

## Verdict

The digit-randomness model is confirmed at exact distinct-digit hits. This is not a solution to the nice-number problem: it neither finds a second nice number nor proves 69 unique. It is the most precise test yet of the model that says a second nice number exists (from about base 120) but is out of search reach.

- **Scale:** across every (1,2) base from 6 to 30, 1,930 exact hits were found and every one was re-verified.
- **Refined model:** the observed count is **0.990** of the model's expectation (95% interval 0.946–1.035, z = −0.45).
  - The largest per-base deviations are base 30 at −2.18σ and base 29 at +2.04σ. Both are inside the 2.5σ limit, they point in opposite directions, and there is no trend with the base.
- **Stop rule:** this meets stop rule 1 ("refined model within about 1σ pooled, no per-base outlier beyond 2.5σ"). The obstruction study (step 4) is **not** triggered.
- **First-pass shortfall:** the 55-against-77 gap came from the first model, not from arithmetic. Its crude formula ignored two things:
  - the clash between the last digits of n and n² (about 15%);
  - the correlation between the leading digits of n and n² (about 4%).
- **Near misses:** numbers missing one or two digits, about 727,000 events, match the same model to 0.04% and 0.02%. That holds only when the model keeps the digit-sum rule. Without it, the one-missing-digit count is off by 6%.

## What was done

1. **Brute-force check (Python, `brute.py`).** Bases 2–18 were run with no filters. Bands, hit counts and full near-miss histograms match the old `quasi_nice.c` for 6–18 and the new C codes.
2. **New exact search (`qn12.c`).** It fixes the top t and bottom j digits of n and prunes wherever the known digits of n and n² clash. The last free digit of n is forced by the digit-sum class. Runs are split into chunks that save as they finish (`run_chunks.sh`).
   - It also counts exactly K(A,J): the n in a valid class whose digits, together with the top A and bottom J digits of n², are all distinct. These counts give the refined model exactly.
   - K matches an independent Python count (`kexact.py`) for bases 6–17.
   - It reproduces the first pass exactly for bases 6–21.
3. **Independent recounts:**
   - Base 29 was re-run with different pruning (t4, j4, AP3): 858 hits, the same witness list, and identical K on the four grid entries the two runs share.
   - An exhaustive, unpruned C histogram (`nm12.c`) recounts bases 20, 21 and 24 as 10, 31 and 60 hits.
   - `verify_hits.py` re-verified all 1,930 witnesses with exact Python integers: 0 failures.
4. **Bases covered.** Base 27 is 3 mod 4, so the digit-sum rule allows no hits (Haskin's Theorem 3); the direction file's base-27 target doesn't apply. Bases 25 and 28 are 1 mod 3 and have no band. The file's figure of 5.4×10¹² roots for base 26 is wrong: the band holds 8.56×10¹¹. Bases 29 and 30 were added instead; they are cheap with the pruned search.

## Models compared

All models except naive and crude keep the digit-sum rule exactly.

| Model | What it holds exact | What it treats as random |
|---|---|---|
| naive | nothing | all b digits: N·b!/b^b |
| crude | the digit-sum class (first-pass formula) | everything else: N·roots·b!/b^b |
| M0 | last digit of n and of n²; both leading digits nonzero | other digits (the analogue of `twice_nice.model_expectation`) |
| M1(A,J) | all of n; top A and bottom J digits of n² | the other c−A−J digits of n² |
| M1e | top 2 and bottom 3 digits of both n and n² | the other b−10 digits (analogue of the (2,3) M1e) |

**M1(2,3) is the headline refined model.** How its values were obtained:
- **Bases 17–29:** exact, from the C search's K(A,J) counts.
- **Bases up to 21:** also computed by an exhaustive numpy pass over every candidate; the two agree to 10⁻⁶.
- **Base 30:** Monte Carlo with 20M samples, standard error 2.0 (0.2%); the exact M1(3,4) there is 924.83.
- **Cross-check:** Monte Carlo agrees with the exact values within its standard error for 24, 26 and 29.

The exact correction for the digit-sum class is included. It only matters at tiny bases, where the model is degenerate: at base 8, M1(2,3) leaves no free digits.

## Extended table

Poisson 95% intervals are exact (Garwood). z and p are under M1(2,3).

| b | (s,c) | N (band) | roots | naive | crude | M0 | M1(1,1) | **M1(2,3)** | M1(3,4) | M1e | obs | 95% CI | z | p |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 6 | (2,4) | 21 | 2 | 0.32 | 0.65 | 0.20 | 0.54 | – | – | – | 1 | 0.0–5.6 | | |
| 8 | (3,5) | 118 | 2 | 0.28 | 0.57 | 0.45 | 0.41 | 1.00* | – | – | 1 | 0.0–5.6 | 0.00 | 1.00 |
| 9 | (3,6) | 486 | 2 | 0.46 | 0.91 | 0.81 | 0.79 | 0.50* | – | – | 1 | 0.0–5.6 | +0.71 | 0.79 |
| 11 | (4,7) | 3,084 | 0 | 0.43 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0–3.7 | | |
| 12 | (4,8) | 14,750 | 2 | 0.79 | 1.58 | 1.13 | 1.14 | 0.57* | 0.50 | – | 0 | 0.0–3.7 | −0.76 | 1.00 |
| 14 | (5,9) | 1.05e5 | 2 | 0.83 | 1.65 | 1.23 | 1.11 | 1.10 | 0.67 | 1.10 | 0 | 0.0–3.7 | −1.05 | 0.66 |
| 15 | (5,10) | 5.63e5 | 0 | 1.68 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0–3.7 | | |
| 17 | (6,11) | 4.43e6 | 2 | 1.91 | 3.81 | 3.50 | 3.30 | 3.39 | 3.58 | 3.30 | 2 | 0.2–7.2 | −0.75 | 0.68 |
| 18 | (6,12) | 2.60e7 | 2 | 4.23 | 8.46 | 6.97 | 7.11 | 7.37 | 7.17 | 7.33 | 9 | 4.1–17.1 | +0.60 | 0.64 |
| 20 | (7,13) | 2.22e8 | 2 | 5.16 | 10.31 | 8.62 | 7.92 | 8.16 | 8.10 | 8.10 | 10 | 4.8–18.4 | +0.64 | 0.61 |
| 21 | (7,14) | 1.41e9 | 4 | 12.31 | 49.25 | 41.30 | 41.87 | 38.48 | 38.61 | 38.44 | 31 | 21.1–44.0 | −1.21 | 0.26 |
| **24** | (8,16) | 8.76e10 | 2 | 40.75 | 81.51 | 70.51 | 72.21 | 62.40 | 62.34 | 61.97 | **60** | 45.8–77.2 | −0.30 | 0.83 |
| **26** | (9,17) | 8.56e11 | 2 | 56.08 | 112.15 | 97.84 | 91.04 | 92.82 | 92.33 | 92.35 | **91** | 73.3–111.7 | −0.19 | 0.91 |
| **29** | (10,19) | 6.36e13 | 4 | 219.06 | 876.24 | 839.21 | 798.55 | 800.37 | 801.32 | 798.98 | **858** | 801.5–917.4 | +2.04 | 0.045 |
| **30** | (10,20) | 4.83e14 | 2 | 621.85 | 1243.69 | 937.51 | 949.48 | 932.60 (MC ±2.0) | 924.83 | 931.49 | **866** | 809.3–925.7 | −2.18 | 0.029 |

\* Degenerate: fewer than 4 free digits remain, so the "model" is nearly the exact count.

The base-30 deviation is −1.93σ under the exact M1(3,4).

## Pooled results

| Model | Obs, bases 6–30 | Expected | Ratio (95% CI) | z | Ratio, first-pass bases 6–21 | Ratio, new bases 24–30 |
|---|---:|---:|---|---:|---|---|
| naive | 1930 | 966.1 | 1.998 (1.910–2.089) | +31.0 | 1.94 (z +5.0) | 2.00 |
| crude (first pass) | 1930 | 2390.8 | 0.807 (0.772–0.844) | **−9.4** | 0.71 (z −2.5) | 0.81 |
| M0 | 1930 | 2009.3 | 0.961 (0.918–1.004) | −1.77 | 0.86 (z −1.15) | 0.964 (z −1.6) |
| M1(0,0): n exact only | 1930 | 2384.5 | 0.809 | −9.3 | 0.71 | 0.81 |
| M1(1,1) | 1930 | 1975.5 | 0.977 (0.934–1.022) | −1.02 | 0.86 | 0.981 |
| M1(2,2) | 1930 | 1952.6 | 0.988 | −0.51 | 0.88 | 0.992 |
| **M1(2,3)** | 1929† | 1948.8 | **0.990 (0.946–1.035)** | **−0.45** | 0.89 (z −0.84) | **0.993 (z −0.30)** |
| M1(3,4) | 1927† | 1939.4 | 0.994 (0.950–1.039) | −0.28 | 0.89 | 0.997 (z −0.13) |
| M1(4,5) | 1927† | 1937.3 | 0.995 | −0.23 | 0.90 | 0.998 |
| M1e | 1927† | 1943.1 | 0.992 (0.948–1.037) | −0.36 | 0.89 | 0.995 |

† These counts omit the bases where the model is undefined (c < A+J; base 6, and base 8 for the larger grids).

Restricted to bases 17–30, where the model has 6 or more free digits: 1,927 observed against 1,945.6 expected under M1(2,3), ratio 0.990, z −0.42.

## Other checks on the hits

- **Spread across bases (17–30, 8 bases):**

  | Model | χ² on 8 d.o.f. | p | Trend in log(obs/model) per base |
  |---|---:|---:|---|
  | M1(2,3) | 11.8 | 0.16 | −0.001 ± 0.011 |
  | M1(3,4) | 11.0 | 0.20 | about 0 |

  The ratio does not drift as the base grows (`extra_stats.py`).
- **Poisson spread within a base:** hits per chunk were compared with the exact per-chunk expectations.
  - Base 29 (200 chunks): χ² = 208, p = 0.32.
  - Base 30 (300 chunks): χ² = 342, p = 0.048, which is mild given two tests.
  - Neither shows clustering beyond Poisson.
- **Where the first-pass gap came from:** crude (77.2) → M0 (64.2) is the last-digit clash, a factor of about lastok/(b−1) ≈ 0.82–0.94, where lastok counts the last digits d with d² ≢ d (mod b). M1(1,1) and M1(2,3) (60.6) add the leading-digit correlations. For example, with c = 2s−1 and n starting with 1, n² starts with 1 about 41% of the time.
  - Holding all of n's digits exact changes nothing: M1(0,0) ≈ crude. Every correction comes from the edges of n².
  - The refinement ladder M1(1,1) → M1(4,5) changes the pooled expectation by only 2%, and every rung is within 1σ. The agreement does not depend on picking one edge depth.

## Near misses (by-product)

- **What was counted:** exhaustive histograms over every n in the band — bases 5–18 in Python, bases 20, 21 and 24 in C.
- **Model:** M1(2,3) with the digit-sum rule, summed exactly per n by a dynamic programme over the multiplicities of the middle digits, then Monte Carlo over n for bases 17 and up.
- **Check on the calculation:** its no-missing-digit column reproduces M1(2,3) exactly at bases 12 and 14.

| b | 1 missing: obs | model | 1 missing: without digit-sum rule | z | 2 missing: obs | model | z |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 34 | 33.2 | 34.5 | +0.14 | 500 | 503.9 | −0.17 |
| 14 | 64 | 47.7 | 51.7 | +2.36 | 1,068 | 1,028.9 | +1.22 |
| 15 | 170 | 148.5 | 137.9 | +1.77 | 3,041 | 3,078.5 | −0.68 |
| 17 | 208 | 216.7 | 231.0 | −0.59 | 6,741 | 6,730 | +0.13 |
| 18 | 548 | 532.4 | 566.8 | +0.68 | 18,828 | 18,887 | −0.43 |
| 20 | 780 | 745.6 | 782.6 | +1.26 | 32,940 | 33,014 | −0.40 |
| 21 | 1,773 | 1,777.9 | 2,065.5 | −0.12 | 98,250 | 98,380 | −0.39 |
| 24 | 8,313 | 8,383.4 | 8,779.6 | −0.76 | 553,572 | 553,445 | +0.12 |
| **Pooled, bases 12–24** | **11,890** | **11,885.4** | 12,649.6 (ratio 0.940) | **+0.04** | **714,940** | **715,068** | **−0.11** |

- **Precision:** one missing digit is tested to about 1%, and two missing digits to about 0.15%.
- **The digit-sum rule is essential:** in a valid class, a one-missing-digit string must swap a digit for one congruent to it mod b−1. So only 60 of the 8,313 base-24 cases lie in valid classes, which is why dropping the rule is off by 6%.
- **Correlation with the hit test:** as the direction file warns, near misses from the same base are correlated with the hits. They are reported separately and not pooled with them.

## Caveats (honest scope)

- **Weaker than the real problem:** here n's own digits are exactly uniform over the band, so only n²'s digits are "random". This tests the model on squares at exact distinct-digit events. The real problem, (2,3), also needs the cube, whose middle third is the hard part. The result supports the model's use there; it does not prove it.
- **Tiny bases:** bases up to 14 carry 3 hits in total. For them the edge models are nearly exact counts, so they add almost no evidence.
- **Monte Carlo:** base 30's headline M1(2,3) is Monte Carlo; its standard error of 0.2% is negligible against the 3.4% Poisson noise. Every other M1(2,3) value for bases 17 and up is exact.
- **Resolution limit:** the test excludes a suppression of exact distinct-digit events larger than about 5% (95%) at bases 17–30. A smaller effect, or one that only appears at much rarer events, cannot be ruled out by any feasible count.

## Files (attack/d1-quasi-nice/)

- **Search:** `qn12.c` (pruned search plus exact K(A,J)), `run_chunks.sh`.
- **Exhaustive counts:** `nm12.c`, `run_nm.sh`.
- **Independent checks:** `brute.py` (Python brute force), `kexact.py`, `verify_hits.py`.
- **Models and analysis:** `model12.py`, `nearmiss_model12.py`, `analyze12.py`, `nearmiss_analyze.py`, `extra_stats.py`.
- **Resume notes:** `STATE.json`, now marked complete.
- **Results:**
  - `results/hits_by_base.json` — the full witness lists, all 1,930.
  - `results/summary.json`, `results/analyze12_output.md` — tables and pooled statistics.
  - `results/nearmiss_summary.json`, `results/extra_stats.json`.
  - Per-chunk outputs for bases 29 and 30 (plus the base-29 cross-check) under `results/b29_*` and `results/b30_*`.
  - Base-24 near-miss chunks under `results/nm_b24/`.
- **Other:** the model outputs are the `results/model_*.jsonl` files; logs are in `logs/`.

Everything is complete. Nothing is running, and no existing files outside this folder were modified.

## Sources

- Direction and first pass: attack/directions/D1-quasi-nice-calibration.md, attack/directions/quasi_nice.c.
- B. Haskin, Theorems 1–4 (band and digit-sum obstructions for general exponent pairs): [nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean).
- The (2,3) edge models and the digit-sum coupling it mirrors: critique/scripts/tail_validation.py, digit_sum_coupling.py, twice_nice.py; attack/p3-analogues/model.py (M1e).
