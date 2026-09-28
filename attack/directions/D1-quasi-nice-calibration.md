# D1. Exact k = 1 calibration of the distinct-digit model on (1,2)-nice numbers

## Goal

Test the random-digit model on **exact hits with distinct digits**, using the
exponent pair (1, 2): n and n² together use every base-b digit exactly once.
Resolve the shortfall seen in the first pass (55 hits against 77 expected in
bases 6–21).

## Why it matters

Every exact-hit test of the model so far allowed repeated digits (twice- and
thrice-nice, [experiments §3](../../critique/experiments.md)); at distinct
digits only near misses were available, and those showed a 13% shortfall at
two missing digits that later vanished on new data
([p3-obstruction](../p3-obstruction/REPORT.md)). The pair (1, 2) has the
same distinct-digit condition, the same kind of digit-sum congruence
(n + n² ≡ b(b−1)/2 mod b−1), the same last-digit clash structure (Haskin's
Theorems 1–4 are stated for general exponent pairs), and hundreds of exact
hits within reach of a few CPU-hours. Whether the model is right at k = 1
exact events is the single most informative cheap measurement left.

- If the refined model matches within Poisson noise across hundreds of hits,
  it is the strongest evidence yet that nothing suppresses distinct-digit
  events, and the uniqueness question is settled to the standard the model
  allows.
- If a shortfall survives the refined model, it is the first evidence of an
  obstruction, and the direction becomes: which configurations are missing,
  and does the shortfall grow with rarity.

## What is known (first pass, this session)

`quasi_nice.c` enumerates the exact band (s digits of n, c digits of n² with
s + c = b, so c ∈ {2s−1, 2s}) and checks every root; every hit is a genuine
permutation of 0..b−1. Bases b ≡ 1 (mod 3) have no band (Haskin's Theorem 1
with (e1+e2) | e1(b−1)); bases b ≡ 3 (mod 4) have no digit-sum roots
(Theorem 3) and indeed 0 hits.

| b | (s, c) | Roots N | Digit-sum roots | E naive = N·b!/b^b | E conditional | Hits |
|---:|---|---:|---:|---:|---:|---:|
| 6 | (2, 4) | 21 | 2 | 0.32 | 0.65 | 1 |
| 8 | (3, 5) | 118 | 2 | 0.28 | 0.57 | 1 |
| 9 | (3, 6) | 486 | 2 | 0.46 | 0.91 | 1 |
| 11 | (4, 7) | 3,084 | 0 | 0.43 | 0 | 0 |
| 12 | (4, 8) | 14,750 | 2 | 0.79 | 1.59 | 0 |
| 14 | (5, 9) | 105,324 | 2 | 0.83 | 1.65 | 0 |
| 15 | (5, 10) | 563,305 | 0 | 1.68 | 0 | 0 |
| 17 | (6, 11) | 4,434,364 | 2 | 1.91 | 3.81 | 2 |
| 18 | (6, 12) | 25,995,465 | 2 | 4.23 | 8.46 | 9 |
| 20 | (7, 13) | 222,216,702 | 2 | 5.16 | 10.31 | 10 |
| 21 | (7, 14) | 1,408,058,799 | 4 | 12.31 | 49.25 | 31 |
| **Total** | | | | 28.4 | **77.2** | **55** |

"E conditional" is the crude conditional model N · roots · b!/b^b · b/(b − #idempotents),
i.e. the digit-sum classes that can be nice are enumerated exactly and the
rest of the digits are uniform. Observed/expected = 0.71, about 2.5σ low as a
Poisson count; base 21 alone is 31 against 49. The naive model, which ignores
the congruence, under-predicts (55 against 28), so the truth of the model
question is decided by the edge and congruence corrections, exactly as it
was for the (2,3) near misses.

Witnesses are in `results/quasi_nice_6_22.jsonl` (first 64 per base). Example:
base 6, n = 20 = "32"₆, n² = 400 = "1504"₆.

## Plan

1. **Refined model.** Build the analogue of the critique's M1 for (1, 2): exact
   distribution of the leading digit of n over the band (a known interval)
   and of the leading digits of n² (computable from the band by integer
   roots), exact joint law of the trailing digits (n mod b³, n² mod b³) with
   the digit-sum class coupling, remaining digits uniform among legal strings
   of the right class. The machinery is in `critique/scripts/tail_validation.py`,
   `digit_sum_coupling.py` and `model_calibration.py`; the (2,3) models there
   over-predicted exact events by about 4.5% before edge corrections.
2. **More data.** Extend exact counts to b = 24 (1.1×10¹¹ roots, about 20
   minutes with a stride filter), 26 (5.4×10¹², a few hours), 27 (7.6×10¹²).
   Expected hits: about 100, 350·roots, 190·roots. Add the digit-sum stride to
   `quasi_nice.c` (only 2–4 residues of b−1 survive) and thread it.
3. **Compare** per base and pooled, with Poisson intervals. Also record the
   deficiency-1 and deficiency-2 near misses for (1, 2) as a by-product; they
   give a much larger sample for the same edge model.
4. **If the shortfall survives** (≥ 3σ pooled under the refined model with
   ≥ 300 hits): tabulate which digit values and positions collide in the
   near misses; compare with the old (2,3) deficiency-2 data; run the k = 2
   version of (1, 2) (every digit twice) to see whether the effect is
   specific to distinct digits; check whether the ratio trends with b.

## Deliverables

A report with the table above extended (base, band, roots, naive, crude
conditional, refined expectation, observed, Poisson interval), the pooled
ratio and z-score under each model, the witness lists, and a verdict.

## Stop rules

- Refined model within about 1σ pooled and no per-base outlier beyond 2.5σ:
  close, and record "the distinct-digit model is confirmed at exact hits."
- Shortfall of 3σ or more under the refined model with ≥ 300 hits: escalate
  to the obstruction study of step 4 and report to the repository owner; this
  would be the first such signal in the project.

## Pitfalls

- Leading zeros: n has none by construction; n² has none because its length
  is fixed by the band. Do not count strings with leading zeros as legal in
  the model.
- The band is not the whole decade: for c = 2s−1 or 2s the interval is cut
  by integer square roots; use exact roots, as `quasi_nice.c` does.
- Counts of "quasi-nice" numbers reported elsewhere (Conflux's post,
  nicenumbers.net) may use different conventions; compute everything here.
- Sigma inflation: exact-hit counts are Poisson, but near-miss counts from
  the same base are correlated with them; test hits and near misses
  separately.
