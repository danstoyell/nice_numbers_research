# The structure of the middle digits of a cube

> **Corrected 2026-09-28** after the [D7 audit](../d7-audit/REPORT.md): Theorem A now assumes P + 1 ≤ 2L (it is false without it), Proposition A′'s proof runs Weyl's argument directly, and several measured claims below are restated more precisely. No conclusion changes.

2026-09-28. What structure, if any, do the digits of n³ in the cube's middle
third have, as a function of the digits of n? The earlier reports proved that no
fixed-value certificate from the two ends reaches those digits
([algorithm report §2](../p1-algorithm/REPORT.md)), and the H1 test showed
that set-valued domains carry nothing either. This report gives the positive
description that explains both, proves what can be proved about it, and checks
every claim on data.

## Summary

- **Along any search batch, a middle digit is the digit-coding of a
  polynomial sequence of degree at most three in the batch offset** (Lemma 1,
  exact). Its linear coefficient is a digit-tail of 3c², its quadratic
  coefficient a digit-tail of 3c, and its cubic coefficient an exact power of
  1/b, where c encodes the fixed prefix and suffix. Digits along a batch are
  therefore never independent random digits; they are Weyl sequences.
- **The polynomial model with random linear coefficient and exact quadratic
  and cubic coefficients reproduces the measured distribution of domain sizes
  to total-variation distance 0.002–0.011** at 17 of the 18 middle positions and batch
  shapes tested (0.027 at (2, 3), P = 6; [D6](../d6-wall-theory/REPORT.md) gives a model that closes it),
  where the iid model is off by 0.01–0.68 (§3). It also
  explains the heavy lower tail of small domains that H1 recorded (2–3 times
  the iid rate) and the positions where the cube has *more* distinct values
  along a batch than random digits would (20.9 against 19.15 in base 30).
- **The coefficients are equidistributed over batches wherever Weyl's
  inequality applies** (Theorem A, with proof), which for search-shaped batches
  is the upper half of the middle third. Below that the linear coefficient is
  a digit-tail of 6·Ptop·R + 3R², a structured mixture that produces nearly
  periodic digit sequences for residue-structured R. Both regimes are
  measured (§2) and neither yields a certificate.
- **Degenerate batches are rare**: a middle digit takes at most three values
  along a batch of b roots in 10⁻⁶ to 10⁻³ of the (batch, position) pairs
  (§4), against the rigorous but weak bound 6/b of Proposition A′. They are
  the lattice certificates the algorithm report costed at one digit per factor
  b; here they are seen directly, and they are the likely source of the extra
  rejections H1 measured (not checked batch by batch).
- **Over a large batch every middle digit is uniform** (Theorem B; measured
  deviations 0.001 against the heuristic Weyl scale N^(−1/4) = 0.03; the t = 2 rows
  lie outside Theorem B's hypothesis t ≤ (1−η)L/3), and **changing any root
  digit re-randomizes every output digit above it** with probability 1 − 1/b
  except at the two positions immediately above, whose exact change
  probabilities follow from the gcd structure, and the smooth top two
  (Theorem C; measured 0.967 against 0.9667 in base 30).
- **Bearing on the goal.** This is the structural theory the wall was
  missing. It replaces "no known method" with a description of exactly what
  the middle digits are, shows that the only structure present is the one
  edge and lattice methods already exploit, and identifies (§7) the single
  algebraic event that could break it, which the sparsity and family theorems
  already exclude. It gives no algorithm and no candidate.

## 1. The structure lemma

Fix the base b and the root length L. A batch fixes the top t digits and the
bottom k digits of the root and frees f = L − t − k digits at positions
k, …, k+f−1. Writing c for the root with the free block set to zero,

    n(m) = c + b^k m,   0 ≤ m < b^f,   c = Ptop·b^(k+f) + R,   b^(t−1) ≤ Ptop < b^t,   0 ≤ R < b^k.

**Lemma 1.** For every position P ≥ k the digit of n(m)³ at position P equals

    ⌊ b · { x₀ + θ₁ m + θ₂ m² + θ₃ m³ } ⌋,

where {·} is the fractional part and

    x₀ = (c³ mod b^(P+1)) / b^(P+1),
    θ₁ = (3c² mod b^(P+1−k)) / b^(P+1−k),
    θ₂ = (3c mod b^(P+1−2k)) / b^(P+1−2k)   if P+1 > 2k, else 0,
    θ₃ = 1 / b^(P+1−3k)                       if P+1 > 3k, else 0.

For the square the same holds with (c² mod b^(P+1))/b^(P+1), (2c mod
b^(P+1−k))/b^(P+1−k) and 1/b^(P+1−2k).

*Proof.* n(m)³ = c³ + 3c²b^k m + 3c b^(2k) m² + b^(3k) m³, and the digit at
position P of an integer X is ⌊b·{X/b^(P+1)}⌋. Each term's contribution to
{X/b^(P+1)} is its residue modulo b^(P+1) divided by b^(P+1); a term divisible
by b^(P+1) contributes nothing. ∎

Checked exactly: `midpoly coeff` recomputes the digit from the expanded terms
c³ + 3c²b^k m + 3c b^(2k) m² + b^(3k) m³ for every root of every sampled batch
(0 mismatches in 5.4 million batches). The reduced-residue form above was
checked in exact arithmetic on 900,000 batches (27 million roots) by the D7
audit (`attack/d7-audit/midpoly_exact.py`): 0 mismatches.

**Zones.** Along a batch, the cube's digit at P is: fixed (P < k); the coding
of a pure rotation by θ₁ (k ≤ P < 2k); a quadratic sequence (2k ≤ P < 3k); a
cubic sequence with an exactly known cubic coefficient (P ≥ 3k). The term
θ₃m³ wraps around the circle only while P + 1 < 3k + 3f; above that it is a
smooth drift. Likewise θ₂m² wraps only while θ₂ ≳ b^(−2f).

**Where the coefficients come from.** Expanding c = Ptop·b^(k+f) + R,

    3c² = 3Ptop² b^(2k+2f) + 6 Ptop R b^(k+f) + 3R²,
    c³  = Ptop³ b^(3k+3f) + 3Ptop²R b^(2k+2f) + 3Ptop R² b^(k+f) + R³.

So θ₁ involves Ptop² only when P ≥ 3k + 2f, and Ptop at all only when
P ≥ 2k + f; below that it is a digit-tail of 6·Ptop·R + 3R², or of 3R² alone.
x₀ involves Ptop³ only when P + 1 > 3(k+f). For the balanced batches a search
uses (t ≈ k ≈ L/2), the thresholds 3k + 2f and 3(k+f) sit near 1.5L: the
upper half of the middle third sees the full cubic and quadratic terms in
Ptop; the lower half sees Ptop only linearly or quadratically.

## 2. The coefficients over batches: measured regimes

Base 30, L = 6 (the nice-number interval), one free digit, three batch shapes;
300,000 random batches per row. "Max deviation" is the largest relative
deviation of a 64-bin histogram from uniform (sampling noise 0.015). The
domain-size columns compare, for the digit at P along the batch, the measured
number of distinct values with the polynomial model (x₀ and θ₁ uniform, θ₂ and
θ₃ the batch's exact values) and with b independent uniform digits.

<!-- COEFF -->
| (t, k) | P | Terms active | Range of θ₂ | Max deviation of x₀ | of θ₁ | Mean distinct values: measured | polynomial model | iid | TV distance measured vs polynomial | vs iid | P(D ≤ 3): measured | polynomial |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| (3, 2) | 6 | linear, quadratic, cubic | 1 | 0.178 | 0.751 | 19.103 | 19.099 | 19.150 | 0.0106 | 0.0472 | 0.0e+00 | 1.7e-05 |
| (3, 2) | 7 | linear, quadratic, cubic | 1 | 0.065 | 0.149 | 19.123 | 19.125 | 19.150 | 0.0035 | 0.0115 | 0.0e+00 | 0.0e+00 |
| (3, 2) | 8 | linear, quadratic, cubic | 1 | 0.092 | 0.039 | 19.082 | 19.067 | 19.150 | 0.0043 | 0.0699 | 0.0e+00 | 0.0e+00 |
| (3, 2) | 9 | linear, quadratic, cubic | 1 | 0.034 | 0.071 | 19.063 | 19.061 | 19.150 | 0.0027 | 0.0881 | 2.7e-05 | 2.7e-05 |
| (3, 2) | 10 | linear, quadratic, cubic | 0.1 | 0.029 | 0.185 | 19.072 | 19.055 | 19.150 | 0.0043 | 0.0852 | 3.3e-06 | 0.0e+00 |
| (3, 2) | 11 | linear, quadratic, cubic | 0.00333 | 0.027 | 0.194 | 19.733 | 19.716 | 19.150 | 0.0073 | 0.1943 | 4.6e-04 | 3.0e-04 |
| (2, 3) | 6 | linear, quadratic | 1 | 0.039 | 0.264 | 19.666 | 19.900 | 19.150 | 0.0269 | 0.3888 | 1.3e-02 | 6.4e-03 |
| (2, 3) | 7 | linear, quadratic | 1 | 0.039 | 0.275 | 19.076 | 19.118 | 19.150 | 0.0087 | 0.1200 | 7.9e-04 | 2.5e-04 |
| (2, 3) | 8 | linear, quadratic | 1 | 0.043 | 0.119 | 19.052 | 19.076 | 19.150 | 0.0040 | 0.0912 | 1.2e-04 | 2.0e-05 |
| (2, 3) | 9 | linear, quadratic, cubic | 1 | 0.033 | 0.042 | 19.108 | 19.105 | 19.150 | 0.0031 | 0.0423 | 3.3e-06 | 3.3e-06 |
| (2, 3) | 10 | linear, quadratic, cubic | 1 | 0.040 | 0.032 | 19.124 | 19.125 | 19.150 | 0.0024 | 0.0121 | 0.0e+00 | 0.0e+00 |
| (2, 3) | 11 | linear, quadratic, cubic | 1 | 0.044 | 0.108 | 19.076 | 19.070 | 19.150 | 0.0034 | 0.0692 | 0.0e+00 | 0.0e+00 |
| (4, 1) | 6 | linear, quadratic, cubic | 1 | 0.061 | 0.155 | 19.062 | 19.065 | 19.150 | 0.0046 | 0.0888 | 2.6e-04 | 4.0e-05 |
| (4, 1) | 7 | linear, quadratic, cubic | 1 | 0.078 | 0.059 | 19.057 | 19.068 | 19.150 | 0.0032 | 0.0889 | 7.0e-05 | 2.3e-05 |
| (4, 1) | 8 | linear, quadratic, cubic | 0.1 | 0.071 | 0.051 | 19.061 | 19.061 | 19.150 | 0.0037 | 0.0865 | 0.0e+00 | 3.3e-06 |
| (4, 1) | 9 | linear, quadratic, cubic | 0.00333 | 0.040 | 0.044 | 19.720 | 19.731 | 19.150 | 0.0025 | 0.1908 | 3.7e-04 | 2.9e-04 |
| (4, 1) | 10 | linear, quadratic, cubic | 0.000111 | 0.043 | 0.047 | 20.823 | 20.820 | 19.150 | 0.0051 | 0.6741 | 8.0e-03 | 8.1e-03 |
| (4, 1) | 11 | linear, quadratic, cubic | 3.7e-06 | 0.031 | 0.113 | 20.914 | 20.885 | 19.150 | 0.0044 | 0.6814 | 9.1e-03 | 9.4e-03 |

Sampling noise for the 64-bin deviations: 0.015. Samples per row: 300,000 batches of 30 roots.
<!-- /COEFF -->

Reading the table:

- x₀ deviates from uniform by 0.03–0.09 except at (3, 2), P = 6 (0.18). θ₁ is
  not uniform to sampling accuracy (0.015) in any row: 0.04–0.19 where Ptop²
  enters it (P ≥ 3k + 2f), up to 0.75 elsewhere. At this size the threshold
  does not separate the rows ((2, 3) at P = 9–10, below it: 0.03–0.04; (3, 2)
  at P = 10–11, above it: 0.19, reproduced in exact arithmetic). Theorem A is
  asymptotic in t and says nothing quantitative at t ≤ 4. Where θ₁ is far from
  uniform below the threshold, its histogram shows the arithmetic
  of 6·Ptop·R + 3R² modulo b^(P+1−k): for R sharing factors with b the value is
  close to a rational with a small denominator, and the digit sequence along
  the batch is nearly periodic.
- The polynomial model matches the measured domain sizes to within 0.03 (0.04 at (2, 3), P = 7) in
  the mean and 0.002–0.011 in total variation in every row but one (the
  quadratic-zone position P = 6 of shape (2, 3), where θ₂ takes only the ten
  values j/10 and θ₁ is also structured: 0.027). The iid model is wrong in
  detail everywhere and badly wrong where θ₂ is small: there the sequence is
  nearly a rotation, rotations spread their points evenly, and the cube shows
  20.9 distinct values among 30 against the iid 19.15.
- The residual deviations in the rows that meet Theorem A's hypothesis ((3, 2)
  at P ≥ 9 and (4, 1) at P ≥ 6), 0.03–0.08 for x₀ and 0.04–0.19 for θ₁, are the
  finite-size cancellation of quadratic and cubic Weyl sums of length
  N_P ≈ 2.6×10⁴; they shrink like a power of N_P.

## 3. Domain sizes: the H1 data against the two models

H1 recorded, for every surviving batch of b roots and every middle-third
position, the number of distinct values the digit takes. The exact iid
distribution is P(D = d) = C(b, d)·d!·S(b, d)/b^b (Stirling numbers).

<!-- H1 -->
| Case | f | Positions measured | Mean distinct: measured | iid exact | Total-variation distance measured vs iid | P(D ≤ b/2): measured | iid | Largest single-bin relative deviation (bins with iid prob > 1e-4) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| thrice-13 (4,3) | 1 | 58,086,616 | 8.4100 | 8.4076 | 0.0502 | 6.66e-02 | 4.20e-02 | 28.762 at d=4 |
| thrice-14 (4,4) | 1 | 997,053,174 | 9.0057 | 9.0393 | 0.0445 | 1.18e-01 | 9.00e-02 | 5.473 at d=5 |
| twice-15 (3,2) | 1 | 1,979,316 | 9.6701 | 9.6710 | 0.0453 | 5.46e-02 | 3.39e-02 | 12.116 at d=5 |
| twice-17 (3,3) | 1 | 16,092,790 | 10.8751 | 10.9346 | 0.0453 | 5.63e-02 | 2.74e-02 | 21.229 at d=6 |
| twice-19 (4,3) | 1 | 393,016,672 | 12.2334 | 12.1984 | 0.0759 | 5.27e-02 | 2.22e-02 | 24.059 at d=7 |
| nice-25 (2,2) | 1 | 520,440 | 15.9131 | 15.9901 | 0.0506 | 3.57e-02 | 1.19e-02 | 19.544 at d=10 |
| nice-30 (3,2) | 1 | 27,305,718 | 19.1516 | 19.1502 | 0.0640 | 4.07e-02 | 1.57e-02 | 11.553 at d=13 |
| nice-30 (2,3) | 1 | 26,689,620 | 19.1924 | 19.1502 | 0.1044 | 5.62e-02 | 1.57e-02 | 12.711 at d=25 |
<!-- /H1 -->

The means agree with iid to 0.03–0.4%, which is why H1's headline numbers
looked iid; the distributions do not: the measured law puts 1.3–3 times more
mass on domains of at most b/2 values, and up to 29 times more on individual
small bins, than iid does. Per position (§2) the polynomial model closes that
gap. The same lemma explains H1's "other" (edge-adjacent) domains, which are
rotation sequences with rational-looking θ₁ and hence often tiny.

## 4. Degenerate batches

<!-- TAIL -->
| Case | b | (batch, position) pairs | P(D = 1) | P(D ≤ 2) | P(D ≤ 3) | Proposition A′ bound 6/b | iid P(D ≤ 3) |
|---|---:|---:|---:|---:|---:|---:|---:|
| thrice-13 (4,3) | 13 | 58,086,616 | 1.1e-05 | 1.4e-04 | 8.0e-04 | 0.46 | 1.5e-06 |
| thrice-14 (4,4) | 14 | 997,053,174 | 8.5e-06 | 1.4e-04 | 5.8e-04 | 0.43 | 1.6e-07 |
| twice-15 (3,2) | 15 | 1,979,316 | 5.1e-07 | 8.9e-05 | 4.4e-04 | 0.40 | 1.5e-08 |
| twice-17 (3,3) | 17 | 16,092,790 | 2.3e-06 | 3.3e-05 | 2.1e-04 | 0.35 | 1.1e-10 |
| twice-19 (4,3) | 19 | 393,016,672 | 1.7e-06 | 2.1e-05 | 3.7e-04 | 0.32 | 5.7e-13 |
| nice-25 (2,2) | 25 | 520,440 | 0.0e+00 | 3.8e-06 | 2.3e-05 | 0.24 | 2.2e-20 |
| nice-30 (3,2) | 30 | 27,305,718 | 0.0e+00 | 2.6e-07 | 1.6e-06 | 0.20 | 4.1e-27 |
| nice-30 (2,3) | 30 | 26,689,620 | 4.3e-05 | 1.1e-04 | 1.3e-03 | 0.20 | 4.1e-27 |
<!-- /TAIL -->

A middle digit constant along a batch (D = 1) is the lattice certificate of
the algorithm report, seen in the wild: it needs the rotation θ₁ to be within
about 1/b² of a value cancelling the drift, and it occurs in 10⁻⁷ to 4×10⁻⁵ of
the (batch, position) pairs. Even D ≤ 3 stays below 1.3×10⁻³. Such a batch can
be rejected only if its few values collide with certified digits, so the total
saving from all degenerate batches is a fraction of a percent of the work,
which is what H1 measured directly (at most 9 roots in a million).

## 5. Theorems

**Notation.** e(x) = exp(2πix). Weyl's inequality (Vaughan, *The
Hardy–Littlewood Method*, Lemma 2.4): if f(u) = αu^d + … has degree d ≥ 2 and
|α − a/q| ≤ q^(−2) with gcd(a, q) = 1, then for every ε > 0

    Σ_{u=1}^{N} e(f(u)) ≪_ε N^(1+ε) (1/q + 1/N + q/N^d)^(1/2^(d−1)).

In particular, if N^η ≤ q ≤ N^(d−η) for some η > 0, the sum is ≪ N^(1−η/2^(d−1)+ε).
The Erdős–Turán–Koksma inequality bounds the discrepancy of a point set in T^r
by 1/H plus a weighted sum of its exponential sums with frequencies of size at
most H.

**Theorem A (equidistribution of the batch coefficients).** Fix b, L, a batch
shape (t, k, f) and a position P with 3(k+f) + ηt ≤ P + 1 ≤ 2L and k ≥ ηt for some
η > 0. As the batch parameter c = Ptop·b^(k+f) + R ranges over all
b^(t−1)(b−1)·b^k batches, the pair (x₀, θ₁) of Lemma 1 is equidistributed in
T², with discrepancy ≪_ε N_P^(−η/8+ε), N_P = b^(t−1)(b−1).

*Proof.* By Erdős–Turán–Koksma in dimension 2 it suffices to bound, for
(h₁, h₂) ≠ 0 with |h_i| ≤ H,

    S(h) = Σ_R Σ_Ptop e( h₁ c³/b^(P+1) + h₂ · 3c²/b^(P+1−k) ).

Fix R. As a polynomial in Ptop the phase has degree 3 if h₁ ≠ 0, with leading
coefficient h₁ b^(3k+3f)/b^(P+1) = h₁/b^(P+1−3k−3f); its reduced denominator
q satisfies b^(P+1−3k−3f)/H ≤ q ≤ b^(P+1−3k−3f). The hypothesis gives
q ≥ b^(ηt)/H ≥ N_P^(η/2) once H ≤ N_P^(η/4), and the hypothesis P + 1 ≤ 2L gives
q ≤ b^(2t−k−f) ≤ N_P^(2+o(1)) ≤ N_P^(3−η). Weyl's inequality with d = 3 gives
|Σ_Ptop| ≪ N_P^(1−η/8+ε). If h₁ = 0 the phase has degree 2 in Ptop with
leading coefficient 3h₂/b^(P+1−3k−2f); the exponent is at least f + ηt, the
reduced denominator lies in [b^(ηt)/(3H), b^(2t−k)] ⊂ [N_P^(η/2), N_P^(2−η)]
because k ≥ ηt, and Weyl with d = 2 gives |Σ_Ptop| ≪ N_P^(1−η/4+ε). Summing
over the b^k values of R and applying Erdős–Turán–Koksma with H = N_P^(η/8)
gives the discrepancy bound. ∎

*Remark (D7 audit, 2026-09-28).* The upper bound P + 1 ≤ 2L is necessary: at
P + 1 = 3L the other hypotheses hold, but x₀ = c³/b^(P+1) is smooth in c
(P(x₀ < ½) = 0.787 in base 30 for every t).

*Remarks.* (i) The theorem is about the two coefficients that Lemma 1 does not
pin down arithmetically; θ₂ and θ₃ are exact rationals with denominators
b^(P+1−2k) and b^(P+1−3k), and θ₂ is equidistributed on its natural range by
the same argument with a linear phase whenever that range is [0, 1). (ii) For
search-shaped batches the hypothesis P + 1 ≥ 3(k+f) + ηt covers the upper half
of the middle third. Below it, θ₁ is the digit-tail of 6·Ptop·R + 3R² modulo
b^(P+1−k) and the Ptop-sum is a complete geometric or Gauss sum whose size
depends on gcd(6R, b^(P+1−2k−f)): the structured regime of §2. (iii) The
saving N_P^(−η/8) is tiny at b = 30, L = 6, which is why §2 still shows
deviations of a few percent there; it is a genuine power saving in L.

**Proposition A′ (degenerate domains).** Under the hypotheses of Theorem A,
for one free digit and any 1 ≤ s ≤ b/2, the fraction of batches in which the
digit at P takes at most s distinct values along the batch is at most
2s/b + o(1) as t → ∞ (the o(1) depends on b).

*Proof.* Fix m ≠ m′ and write x_m = x₀ + θ₁m + θ₂m² + θ₃m³. For (g₁, g₂) ≠ 0
the phase g₁x_m + g₂x_m′ equals h₁x₀ + h₂θ₁ + h₃θ₂ + const, with h₁ = g₁+g₂,
h₂ = g₁m+g₂m′, h₃ = g₁m²+g₂m′², and (h₁, h₂) ≠ 0 because m ≠ m′. The θ₂ term
e(3h₃c/b^(P+1−2k)) is linear in Ptop and θ₃ is constant, so they change only
lower-order coefficients in the proof of Theorem A, on which Weyl's bound does
not depend. That proof therefore applies with |h₁| ≤ 2H and |h₂| ≤ 2(b−1)H,
and (x_m, x_m′) is equidistributed on T², uniformly over the C(b, 2) pairs.
(Pushing Theorem A forward does not suffice: the translation θ₂m² + θ₃m³
varies with the batch. D7 audit, 2026-09-28.) The two digits coincide with probability
1/b + o(1). Hence the expected number of coinciding pairs among the b points
is (b−1)/2 + o(b). If the digits take at most s values, convexity gives at
least s·C(b/s, 2) ≥ b(b−s)/(2s) coinciding pairs, and Markov's inequality
gives a bound of s(b−1)/(b(b−s)) + o(1) ≤ 2s/b + o(1). ∎

The bound 2s/b is far from the measured 10⁻⁶–10⁻³ (§4); the truth needs the
quadratic and cubic terms, which destroy near-periodicity unless they are
themselves nearly rational. The proposition's role is to make "rare" a
theorem; the measurement supplies the size.

**Theorem B (large batches).** Fix η > 0. For a batch of all roots with a
fixed prefix of t ≤ (1−η)L/3 digits, N = b^(L−t) members, and any position
L ≤ P < 2L, the frequency of each digit value at P over the batch is
1/b + O(N^(−η/8+ε)).

*Proof.* With n = Ptop·b^f + u, u < N = b^f, the phase h n³/b^(P+1) is a cubic
in u with leading coefficient h/b^(P+1), reduced denominator in
[b^(P+1)/H, b^(P+1)] ⊂ [N^(η/2), N^(3−η)] since P + 1 ≤ 2L ≤ (3−η)f under the
hypothesis on t. Weyl with d = 3 and Erdős–Turán in one dimension give the
claim. ∎

**Theorem C (sensitivity).** Fix η > 0 and a digit position i of the root.
For n uniform in [b^(L−1), b^L) and δ ∈ {1, …, b−1} such that n + δb^i lies in
the same range, and any output position p of the cube with
i + ηL ≤ p ≤ min(i + (2−η)L, (3−η)L), the digit at p of (n + δb^i)³ differs
from that of n³ with probability 1 − 1/b + O(N^(−η/8+ε)), N = b^L.

*Proof.* The pair ({n³/b^(p+1)}, {(n+δb^i)³/b^(p+1)}) is equidistributed in T²:
a frequency (h₁, h₂) with h₁ + h₂ ≠ 0 gives a cubic in n with leading
coefficient (h₁+h₂)/b^(p+1) and reduced denominator in [N^η, N^(3−η)] since
ηL ≤ p + 1 ≤ (3−η)L; a frequency with h₂ = −h₁ ≠ 0 gives the quadratic
−h₁(3n²δb^i + 3nδ²b^(2i) + δ³b^(3i))/b^(p+1) with leading denominator
b^(p+1−i)/gcd, which lies in [N^η, N^(2−η)] under the hypothesis on p. Weyl
and Erdős–Turán–Koksma give the discrepancy, and the event "same digit" is a
union of b squares of side 1/b. ∎

Outside the theorem's range the behaviour is exact and different: at position
i ≥ 1 itself the cube's digit changes by 3n₀²δ modulo b (with n₀ the bottom
digit; the change is exactly 3n₀²δ·b^i modulo b^(i+1), with no carry), so it
changes with probability P(b ∤ 3n₀²δ), which the gcd count with δ ≠ 0 puts
at 219/290 = 0.755 in base 30 (24/29 = 0.828 for the square's 2n₀δ), matching
the measured 0.755 and 0.828 (D7 audit). At i = 0 the bottom digit is n₀³ modulo b,
which always changes when cubing is a bijection modulo b. At the top two
affected positions the change Δ/b^(p+1) is smaller than one, so the digit
changes with probability about b·Δ/b^(p+1).

## 6. Measurements for Theorems B and C

<!-- BATCH -->
| Fixed top digits t | Prefix | Batch size N | Heuristic Weyl scale N^(−1/4) | iid noise | Max deviation of a digit frequency from 1/b over the middle third (positions 6–11) | Bottom positions 0–5 | Top three positions |
|---:|---:|---:|---:|---:|---:|---|---|
| 2 | 755 | 810,000 | 0.0333 | 0.000199 | 0.0009 | 0.0000, 0.0300, 0.0306, 0.0000, 0.0011, 0.0010 | 0.014 (30 values), 0.440 (3 values), 0.967 (1 values) |
| 2 | 640 | 810,000 | 0.0333 | 0.000199 | 0.0006 | 0.0000, 0.0300, 0.0306, 0.0000, 0.0012, 0.0011 | 0.011 (30 values), 0.625 (3 values), 0.967 (1 values) |
| 2 | 603 | 810,000 | 0.0333 | 0.000199 | 0.0006 | 0.0000, 0.0300, 0.0306, 0.0000, 0.0011, 0.0009 | 0.016 (30 values), 0.708 (3 values), 0.967 (1 values) |
| 1 | 20 | 24,300,000 | 0.0142 | 0.000036 | 0.0001 | 0.0000, 0.0300, 0.0306, 0.0000, 0.0011, 0.0011 | 0.001 (30 values), 0.015 (30 values), 0.685 (3 values) |
<!-- /BATCH -->

The positions 1 and 2 show a fixed deviation of 0.03: for n ranging over
complete residue classes those digits are exactly the digits of n³ modulo b³,
whose value distribution is not uniform (the map is not a bijection modulo
900). Position 0 is uniform because cubing is a bijection modulo 30. This is
bottom-edge structure, certified and used by every search.

<!-- SENS -->
Base 30, roots of 6 digits, 3,000,000 random changes of one digit; a random new digit would change each position with probability 0.9667. A change at root position i reaches the square's positions i … i+L and the cube's positions i … i+2L (the size of 2nδ·b^i and 3n²δ·b^i); above that the change is smooth.

| Changed root digit i | Square: position i | i+1 | mean over i+2 … i+L−2 | i+L−1 | i+L | Cube: position i | i+1 | mean over i+2 … i+2L−2 | i+2L−1 | i+2L |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.93 | 0.97 | 0.965 | 0.97 | 0.99 | 1.00 | 0.97 | 0.966 | 0.97 | 0.98 |
| 1 | 0.83 | 0.97 | 0.967 | 0.97 | 0.99 | 0.76 | 0.92 | 0.967 | 0.97 | 0.98 |
| 2 | 0.83 | 0.97 | 0.969 | 0.97 | 0.99 | 0.76 | 0.91 | 0.966 | 0.97 | 0.98 |
| 3 | 0.83 | 0.97 | 0.969 | 0.97 | 0.99 | 0.75 | 0.91 | 0.965 | 0.97 | 0.98 |
| 4 | 0.83 | 0.97 | 0.967 | 0.97 | 0.99 | 0.76 | 0.91 | 0.965 | 0.97 | 0.98 |
| 5 | 0.84 | 0.97 | 0.967 | 0.97 | 1.00 | 0.77 | 0.91 | 0.965 | 0.97 | 0.98 |
<!-- /SENS -->

## 7. Reading the theory against the goal

- **What structure the middle digits have.** Exactly the polynomial structure
  of Lemma 1: along the direction of any free block they are degree-≤3 Weyl
  sequences whose coefficients are digit-tails of 3c², 3c and c³. The
  degree-1 zone (positions k ≤ P < 2k) is the bottom-up "line lemma" of the
  existence report and the engine of Theorem 7 in Haskin's
  [nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean), where one
  new input digit moves the next output digit of each power affinely and a
  greedy choice keeps 2d low slots distinct; Lemma 1 extends that to every
  position, with the quadratic and cubic zones and their exact coefficients.
- **Why it cannot be used.** Certifying a middle digit for a batch means
  making its rotation number θ₁ small, i.e. making a chosen digit-tail of 3c²
  small. A run of r small digits in 3c² at the right place costs a factor b^r
  in the density of admissible c (Theorem A makes the digit-tails uniform),
  and buys r frozen digits: cost equals gain, which is the lattice
  accounting of the algorithm report, now with the mechanism visible. Making
  many digit-tails small at once means c² having a long run of small or equal
  digits in its middle, which forces c to be sparse or of the form
  round(b^j·√A); the sparsity theorem and the structured-family report exclude
  both, and Lemma 1 shows the free block would destroy the run anyway (its
  term 2c·b^k·m has digits across the whole run).
- **What the cryptographic view adds.** The middle digits of a product are the
  "middle product", whose hardness underlies Middle-Product LWE
  ([Roşca, Sakzad, Stehlé, Steinfeld](https://eprint.iacr.org/2017/628)); a
  search for a root whose middle digits satisfy a combinatorial condition is a
  preimage search, and the overlap join is its birthday attack. Theorems A–C
  are the statements that the function has no local weakness of the kinds a
  search could use; they do not prove one-wayness, which is out of reach.
- **What would break the wall.** A batch shape or a family of c for which the
  digit-tails of 3c² at many middle positions are simultaneously small at a
  density cost below b per position. Lemma 1 says this is the only door;
  Theorem A says it is closed in the regime where analysis reaches; the
  measurements say it is closed where it does not.

## Files

- `midpoly.c`: measurements (modes `coeff`, `sens`, `batch`); `models.py`:
  exact iid occupancy against the H1 histograms; `summarize.py`: the tables.
- `results/coeff.jsonl`, `results/sens.json`, `results/batch.jsonl`,
  `results/domain_models.json`.

Reproduce:

```sh
clang -O3 -march=native -o midpoly midpoly.c -lm
for tk in "3 2" "2 3" "4 1"; do set -- $tk; for P in 6 7 8 9 10 11; do ./midpoly coeff 30 6 $1 $2 1 $P 300000 7; done; done > results/coeff.jsonl
./midpoly sens 30 234613921 728999999 6 3000000 11 > results/sens.json
for s in 1 2 3; do ./midpoly batch 30 234613921 728999999 6 2 $s; done > results/batch.jsonl; ./midpoly batch 30 234613921 728999999 6 1 5 >> results/batch.jsonl
python3 summarize.py
```
