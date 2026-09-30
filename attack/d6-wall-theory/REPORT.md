# D6. Completing the middle-digit theory: the structured regime, degenerate batches, general exponents

2026-09-27. Direction [D6](../directions/D6-complete-wall-theory.md). This extends [middle-digits](../middle-digits/REPORT.md) and uses its notation:
- base b, root length L;
- batch shape (t, k, f), with c = Ptop·b^(k+f) + R;
- the Lemma 1 coefficients x₀, θ₁, θ₂, θ₃.

Steps 1–3 of the plan are done. Step 4 was not written; §4 gives the reason. Step 5 was covered by D7's audit.

## Summary

**Proved**

- **Theorem S: the structured regime has an exact law.**
  - In the range where the prefix enters θ₁ linearly (2k+f ≤ P < 3k+2f), θ₁ = {3R²/b^J + 6R·Ptop/b^j}, with J = P+1−k and j = P+1−2k−f.
  - When j ≤ t−1, the prefix sum is a complete sum. Given R, θ₁ is then exactly uniform on a coset of the subgroup of order q_R = b^j/gcd(6R, b^j).
  - Its Fourier coefficients are incomplete quadratic Gauss sums over the R divisible by D_h = b^j/gcd(6h, b^j).
  - For j ≤ k they equal gcd(6h, b^j)/b^j · ∫₀¹ e(hλ₁x²) dx, with error at most 6π|h|/b^(f+j), where λ₁ = 3b^(k−f−j).
  - So θ₁ has the law of W + λ₁X² (a lattice smeared by a Fresnel profile): W is uniform on a random subgroup and X is uniform on [0, 1).
  - The proof is five lines, with no case analysis.
- **Theorems D1–D4 and Proposition D5: degenerate batches.** A batch has b roots; D is the number of distinct values a middle digit takes along it.
  - *Rotation* (θ₂ = 0): P(D = 1) = 1/(b(b−1)) exactly, and (2s−1)/(b(b−1)) ≤ P(D ≤ s) ≤ 16s²/b² for s < b/4 (three-gap theorem).
  - *Full quadratic* ((x₀, θ₁, θ₂) uniform): P(D = 1) = 2A_b/b⁵ exactly for b ≥ 10, with A_b → A = 34/9 (closed form).
    - D = 1 forces θ₂ to lie within about 4/b³ of n/2, and θ₁ within 2/b² of the same n/2, for n ∈ {0, 1}.
    - For general s: P(D ≤ s) ≤ about s²/b², by counting coinciding triples. This replaces Proposition A′'s 2s/b.
  - *Cubic zone:* D = 1 is impossible when θ₃ = b⁻¹ (b ≥ 10), θ₃ = b⁻² (b ≥ 15) or θ₃ = b⁻³ (b ≥ 25).
  - *Lattice position P = 2k:* here θ₂ lies in (1/b)ℤ exactly, and the rate is P(θ₂ ∈ {0, ½})/(b(b−1)). That is order b⁻³, not b⁻⁵.
- **§3: general exponent pair (e₁, e₂).**
  - Lemma 1 for n^e has e+1 zones.
  - Theorem S_e holds with classes gcd(e(e−1)R^(e−2), b^j).
  - Theorem A_e holds for e ≥ 3 under P+1 ≤ (e−1)L.
  - The wall of n^e is the positions [L, (e−1)L).
  - An overlap join can certify at most (min(e₁,2) + min(e₂,2))/(e₁+e₂) of the output digits. The cost exponent is ρ(1 − ln ρ), with ρ = Σ(eᵢ−2)⁺/(e₁+e₂).
  - For (2,3) this gives 0.522 and 0.906, the algorithm report's two figures.

**Measured only**

- **Theorem S confirmed.**
  - The mixture histogram equals brute force over all 23.49 million batches: integer equality in 4096 bins in every row where the theorem applies.
  - The same equality holds in 23 more rows in bases 7–14 (f = 1, 2), and in 12 rows for exponents 2, 4 and 5.
  - The Fourier formula matches to ≤ 3×10⁻¹³ in every row with j ≤ k+f.
  - The exact laws reproduce all 18 rows of `coeff.jsonl` within sampling noise. For example, the exact deviation is 0.747 against 0.751 measured, and 0.278 against 0.275.
- **Uniform-quadratic constants for s ≥ 2.** The measured b⁵·P(D ≤ s) is about 9, 120, 520 and 1650 for s = 1–4, at every base from 10 to 40 (roughly 7s⁴/b⁵). Order b⁻⁵ is proved only for s = 1.
- **H1's tail table explained position by position.**
  - Re-enumeration reproduces all five rows exactly.
  - At the generic positions, the observed rates match the model rates for s ≤ 3 within about 10%. For example, thrice-13 at P = 8 has 189 constant digits against 188.2 predicted.
  - Cubic-zone positions, and positions whose θ₂ the search interval keeps away from {0, ½}, give 0.
  - The 800-fold gap between nice-30 (2,3) and nice-30 (3,2) is one lattice position, P = 2k = 6. It holds 99.9% of the (2,3) tail.
  - A model that keeps each batch's exact (θ₁, θ₂, θ₃) and draws x₀ uniformly fits the domain-size law at every position to total variation ≤ 0.002. The report's model reaches up to 0.027.

**Bearing on the goal:** none. This completes the description. Put as sizes: a middle digit is constant along a b-root batch with frequency about 7.6/b⁵ per generic position, and order b⁻³ at the single position P = 2k when that position falls in the middle third. It yields no candidate and no algorithm.

## 0. How D7's correction of Theorem A affects this note

D7 found that Theorem A fails without the hypothesis P+1 ≤ 2L.

- **Not affected.** None of Theorem S, Theorems D1–D4 or Proposition D5 uses Theorem A. Theorem S is an exact identity for complete sums. D1–D4 and D5 are statements about the polynomial model.
- **Proposition A″ (§2.5)** uses a triple extension of Theorem A. I state it with P+1 ≤ 2L built in.
- **Theorem A_e (§3)** is stated with P+1 ≤ (e−1)L. My check of its ranges uses that bound, and for e = 3 it is D7's corrected theorem.

No result here relied on the wider range.

## 1. The structured regime

**Notation.** Let J = P+1−k, so that θ₁ = (3c² mod b^J)/b^J. Let j = P+1−2k−f and N_P = (b−1)b^(t−1).

From 3c² = 3Ptop²b^(2k+2f) + 6·Ptop·R·b^(k+f) + 3R² there are three regimes:
- **j ≤ 0** (P < 2k+f): θ₁ = {3R²/b^J}. It does not depend on the prefix.
- **1 ≤ j ≤ k+f** (2k+f ≤ P < 3k+2f): θ₁ = {3R²/b^J + 6R·Ptop/b^j}. It is linear in the prefix.
- **j > k+f:** Ptop² enters θ₁. This is the Weyl regime of Theorem A.

The plan's range 2(k+f) ≤ P < 3(k+f) is where x₀ is quadratic in the prefix. For θ₁, whose law the plan asks for, the prefix-linear range is the one above.

**Theorem S.** Let 1 ≤ j ≤ min(t−1, k+f), with (Ptop, R) uniform on [b^(t−1), b^t) × [0, b^k).

(i) *Conditional law.* Given R, θ₁ is uniform on the q_R points 3R²/b^J + i/q_R, where q_R = b^j/gcd(6R, b^j). So θ₁'s law is the mixture Σ_d w_d μ_d over the divisor classes d = gcd(6R, b^j).

(ii) *Fourier form.* For every integer h,

    E e(hθ₁) = b^(−k) Σ_{0 ≤ R < b^k, D_h | R} e(3hR²/b^J),   D_h = b^j/gcd(6h, b^j).

(iii) *Limit law.* If also j ≤ k, then

    | E e(hθ₁) − (gcd(6h, b^j)/b^j)·F(hλ₁) | ≤ 6π|h|/b^(f+j),

where F(μ) = ∫₀¹ e(μx²) dx and λ₁ = 3b^(k−f−j). The main term is exactly the Fourier transform of ν, the law of W + λ₁X² mod 1:
- X is uniform on [0, 1), independent of W;
- W is uniform on the subgroup (1/q)ℤ/ℤ, where q = b^j/gcd(6R′, b^j) and R′ is uniform mod b^j.

(iv) *Weights.* The weights w_d are multiplicative over the primes p dividing b. For each p, v_p(gcd(6R, b^j)) = min(v_p(6) + v_p(R), j·v_p(b)), with P(v_p(R) ≥ a) = p^(−a), independently across p (for j ≤ k).

*Proof.*
- (i) N_P is a multiple of b^j and the prefix range is an interval. So Ptop mod b^j takes every residue equally often, and 6R·Ptop mod b^j is then uniform on the multiples of gcd(6R, b^j).
- (ii) The average of e(h·) over the subgroup of order q is 1[q | h]. Also q_R | h ⟺ b^j | 6hR ⟺ D_h | R.
- (iii) Write R = D_h·r with r < M = b^k/D_h. Then 3hD_h²r²/b^J = hλ₁(r/M)². The Riemann sum (1/M)Σ φ(r/M), with φ(x) = e(hλ₁x²), differs from ∫₀¹ φ by at most (1/M)∫|φ′| = 2π|h|λ₁/M. Dividing by D_h gives 6π|h|b^(−f−j). For ν, E e(hW) = P(D_h | R′) = 1/D_h, by independence.
- (iv) This is the Chinese remainder theorem. ∎

**Sizes.** By van der Corput's lemma, |F(μ)| ≤ min(1, 4/√(π|μ|)), and |F(μ)| ~ 1/(2√(2|μ|)) for large |μ| (Fresnel asymptotics). Hence

    |θ̂₁(h)| ≤ (gcd(6h, b^j)/b^j)·min(1, 4/√(π|h|λ₁)) + 6π|h|b^(−f−j),

and the main term is attained. Two consequences:
- **Where the large coefficients are.** They sit at the frequencies h where gcd(6h, b^j) is large. In base 30, shape (3,2), P = 6, the coefficient at h = 150 is predicted as F(15) ≈ 0.091 and measured at 0.0876.
- **Where θ₁ is far from uniform.** When λ₁ ≲ 1 (j ≥ k−f), the offsets do not wrap around the circle, and each divisor class puts 1/√-shaped spikes at the points of its subgroup. When λ₁ ≫ 1 the classes are smeared; at resolution 1/B the remaining deviation is about √(B/λ₁), coming from the spike at 0.

**The other regimes, in exact Fourier form.**
- *Prefix sum incomplete* (t ≤ j ≤ k+f): E e(hθ₁) = b^(−k) Σ_R e(3hR²/b^J)·K(6hR/b^j). Here K is the normalized Dirichlet kernel over the prefix interval, with |K(β)| ≤ min(1, 1/(2N_P‖β‖)).
- *Prefix-free* (j ≤ 0): θ₁'s law is the pushforward of R ↦ {3R²/b^J}.
  - If J ≤ k, its Fourier coefficients are b^(−J)·G(3h, b^J), complete Gauss sums.
  - Otherwise they are incomplete Gauss sums, bounded by completion.

Both forms were verified to 10⁻¹² (`max_fourier_formula_error` in `results/theta1_*.jsonl`).

**Confirmation against `coeff.jsonl`** (b = 30, L = 6, f = 1). The "exact" column is the maximum relative deviation of the 64-bin θ₁ histogram over all 23.49 million batches. The "measured" column comes from the report's 300,000 samples: per-bin noise is 0.015, so the maximum over 64 bins is about 0.04.

| (t,k) | P | j | Regime | Exact | Measured |
|---|---:|---:|---|---:|---:|
| (3,2) | 6 | 2 | linear, complete | 0.747 | 0.751 |
| (3,2) | 7 | 3 | linear, incomplete | 0.147 | 0.149 |
| (3,2) | 8 / 9 / 10 / 11 | 4–7 | Ptop² | 0.013 / 0.040 / 0.169 / 0.205 | 0.039 / 0.071 / 0.185 / 0.194 |
| (2,3) | 6 | 0 | prefix-free | 0.273 | 0.264 |
| (2,3) | 7 | 1 | linear, complete | 0.278 | 0.275 |
| (2,3) | 8 / 9 / 10 | 2–4 | linear, incomplete | 0.125 / 0.023 / 0.010 | 0.119 / 0.042 / 0.032 |
| (2,3) | 11 | 5 | Ptop² | 0.085 | 0.108 |
| (4,1) | 6–11 | 4–9 | Ptop² | 0.153, 0.030, 0.046, 0.043, 0.006, 0.104 | 0.155, 0.059, 0.051, 0.044, 0.047, 0.113 |

**The limit law ν against the exact law** (`limit_law.py`). The last column divides the largest Fourier difference by the bound in (iii).

| b | (t,k,f) | P | λ₁ | Maximum deviation: exact | ν | Max \|ΔFourier\| / bound |
|---:|---|---:|---:|---:|---:|---:|
| 30 | (3,2,1) | 6 | 0.1 | 0.747 | 0.714 | 0.47 |
| 30 | (2,3,1) | 7 | 90 | 0.278 | 0.259 | 0.00 |
| 10 | (4,3,2) | 8 / 9 / 10 | 3 / 0.3 / 0.03 | 1.381 / 0.833 / 0.369 | 1.393 / 0.792 / 0.344 | ≤ 0.47 |
| 12 | (3,3,2) | 8 / 9 | 3 / 0.25 | 3.056 / 2.162 | 3.038 / 2.157 | ≤ 0.45 |
| 12 | (4,3,1) | 7 | 36 | 1.056 | 0.890 | 0.00 |

The bound in (iii) holds in all 18 limit-law rows (ratio ≤ 0.47). The histogram-level agreement is looser where b^(f+j) is small, as for b = 12 at P = 7.

## 2. Degenerate batches

Setting: f = 1, so a batch has b roots, m = 0, …, b−1. Write y_m = x₀ + θ₁m + θ₂m² + θ₃m³; the digit is ⌊b·y_m⌋, and D is the number of distinct digits.

**Theorem D1 (rotation).** Let θ₂ = θ₃ = 0 and (x₀, θ₁) be uniform on T². Then P(D = 1) = 1/(b(b−1)), and for 1 ≤ s < b/4,

    (2s−1)/(b(b−1)) ≤ P(D ≤ s) ≤ 16s²/b².

*Proof.*
- **P(D = 1).** D = 1 forces ‖θ₁‖ < 1/b. The b points then span an arc of length (b−1)|θ₁| < 1, and D = 1 exactly when that arc lies in one cell. For fixed θ₁ this has x₀-probability (1 − b(b−1)|θ₁|)⁺; integrating gives 1/(b(b−1)).
- **Lower bound.** This is the same computation, using arcs that fit in at most s cells.
- **Upper bound.**
  - Let U = Σ_gaps min(b·g, 1), which equals b times the measure of ⋃[y_m, y_m + 1/b). Always D ≥ U/2.
  - By the three-gap theorem, with q₊ = argmin{mθ} and q₋ = argmax{mθ} over 1 ≤ m < b, the gaps are a = {q₊θ} (b − q₊ of them), a′ = 1 − {q₋θ} (b − q₋ of them) and a + a′ (q₊ + q₋ − b of them). This exact multiplicity form holds in 3000 of 3000 random cases (`three_gap_check.py`).
  - Take a ≤ a′ and suppose U ≤ 2s < b/2.
  - Then a < 1/b; otherwise U = b.
  - Also a′ ≥ 1/b; otherwise every gap is below 2/b and U ≥ b/2.
  - So the q₊ gaps of types a′ and a+a′ each contribute 1, giving q₊ ≤ 2s. And (b − q₊)·b·a ≤ 2s gives ‖q₊θ‖ = a ≤ 4s/b².
  - The union over q ≤ 2s of these windows has measure at most 16s²/b². ∎

**Measured rotation constants.** b²·P(D ≤ s) ≈ 1.04, 3.7–4.1, 7.6–8.3 and 13–15 for s = 1–4, at b = 10–40.

**Lemma (support).** Let (x₀, θ₁, θ₂) be arbitrary, θ₃ = 0 and b ≥ 10. If D = 1, then for some n ∈ {0, 1}:
- θ₂ = n/2 + ε with |ε| < 1/(bR²), where R = ⌊(b−1)/2⌋;
- θ₁ ≡ n/2 + δ with |δ| < 2/b;
- the real polynomial p(m) = δm + εm² satisfies |p(m)| < 1/b for all m < b.

*Proof.*
- If all points lie in one cell, the second differences y_{m+2r} − 2y_{m+r} + y_m lie in (−2/b, 2/b) and are congruent to 2r²θ₂. So ‖2r²θ₂‖ < 2/b for every r ≤ R.
- Write 2θ₂ = n + 2ε. By induction on r, |2r²ε| < 2/b, since |2(r+1)²ε| < 8/b ≤ 1 − 2/b. Hence |ε| < 1/(bR²).
- Next, θ₁m + θ₂m² ≡ m(θ₁ − n/2) + εm², because m(m+1)/2 is an integer.
- Induction on m, with step at most 3/b + 2/R² < 1 − 1/b, turns ‖p(m)‖ < 1/b into |p(m)| < 1/b. ∎

**Theorem D2 (full quadratic, D = 1).** Let (x₀, θ₁, θ₂) be uniform on T³, θ₃ = 0 and b ≥ 10. Then

    P(D = 1) = 2A_b/b⁵,   A_b = ∫∫_{ℝ²} (1 − range_{m<b}(u·m/b + v·(m/b)²))⁺ du dv.

The constants satisfy A_b ≥ A_b→∞ = A = 34/9. More precisely, A = ∫ a(v) dv, where a is even in v and, for v ≥ 0:
- a(v) = 1 − v²/6 for 0 ≤ v ≤ 1;
- a(v) = (8/3)√v − 2v + v²/6 for 1 ≤ v ≤ 4;
- a(v) = 0 beyond.

Numerically A_b = 5.20 at b = 10, 4.81 at 13 and 4.18 at 30.

*Proof.* On the two neighbourhoods given by the lemma, y_m = x₀ + p(m) mod 1, and D = 1 has x₀-probability (1 − b·range p)⁺. Substitute u = δb², v = εb³ (Jacobian b⁻⁵). ∎

- **Consequence for a slowly varying θ₂.** If θ₂ is uniform on [0, ρ) with ρ < ½, then P(D = 1) = (1/(ρb⁵))·∫₀^{ρb³} a_b(v) dv. This runs from 1/(b(b−1)) as ρb³ → 0 up to (A_b/2)/(ρb⁵).
- **D = 1 is impossible** whenever θ₂ is further than about 4/b³ from both 0 and ½.
- **Monte Carlo check** (`model_mc.jsonl`, 2×10⁸–10⁹ samples per base). P(D = 1) matches 2A_b/b⁵ at every base from 10 to 40; for example, 2.628×10⁻⁵ against 2.593×10⁻⁵ at b = 13, and 3.25×10⁻⁷ against 3.44×10⁻⁷ at b = 30. Adding θ₃ = b⁻⁴ changes nothing measurable.

**Theorem D3 (general s, rigorous but not sharp).** If (x₀, θ₁, θ₂) is uniform, any three distinct points (y_m, y_m′, y_m″) are Haar-uniform on T³, because the Vandermonde matrix has nonzero determinant. So the expected number of triples that share a cell is C(b,3)/b². If D ≤ s, at least s·C(b/s, 3) triples share a cell (convexity). Markov's inequality then gives

    P(D ≤ s) ≤ (b−1)(b−2)s² / (b²(b−s)(b−2s))   for s < b/2.

The true order is b⁻⁵. Measured b⁵·P(D ≤ s) is about 9, 100–140, 450–600 and 1500–2300 for s = 1–4, stable across b = 10–40 (roughly 7s⁴/b⁵). The heuristic behind it: D ≤ s puts (θ₁, θ₂) within (s/b², s/b³) of one of about s² rational points. **I proved the order b⁻⁵ only for s = 1.**

**Theorem D4 (cubic-zone exclusion).** Four points in one cell have third difference in (−4/b, 4/b), and that difference is congruent to 6r³θ₃. So D = 1 is impossible when some r ≤ (b−1)/3 has ‖6r³θ₃‖ ≥ 4/b. This holds:
- for θ₃ = b⁻¹ when b ≥ 10;
- for θ₃ = b⁻² when b ≥ 15 (and b = 10–12);
- for θ₃ = b⁻³ when b ≥ 25 (and b = 22).

These were checked exactly for b ≤ 2000 in `cubic_exclusion.py`, with an elementary argument beyond that. The Monte Carlo agrees: with θ₃ = b⁻³ there are 0 events at b ≥ 19.

**Proposition D5 (lattice θ₂).** Let θ₃ = 0, θ₂ fixed and (x₀, θ₁) uniform. Then:
- if θ₂ ∈ {0, ½}, the sequence is a rotation and P(D = 1) = 1/(b(b−1));
- if θ₂ is at least 1/(bR²) from both 0 and ½, then P(D = 1) = 0.

At P = 2k, θ₂ = (3R mod b)/b, so the rate is P(3R₀ ≡ 0 or b/2 mod b)/(b(b−1)). In base 30 that is (1/5)·(1/870) = 2.30×10⁻⁴; the structured model gives exactly 2.298×10⁻⁴ on nice-30 (2,3), P = 6. At P = 2k+1 only θ₂ ∈ {0, ½} exactly qualifies, giving order b⁻⁴. From e₂ = P+1−2k ≥ 3 on, the generic b⁻⁵ applies.

**Proposition A″ (batches; uses Theorem A, restricted as D7 found).** Assume:
- 3(k+f) + ηt ≤ P+1 ≤ min(2L, 2k+L−1);
- k ≥ ηt.

Then (x₀, θ₁, θ₂) is equidistributed in T³ as t → ∞.
- *Why.* Frequencies with h₀ ≠ 0 or h₁ ≠ 0 are handled as in Theorem A: the linear-in-Ptop part of θ₂ does not change the leading coefficient. For h₀ = h₁ = 0, the sum over Ptop is complete modulo b^(P+1−3k−f) and vanishes.
- *Consequences.* For fixed b, P(D ≤ s) tends to the model value, because the event is a finite union of polytopes. In particular P(D = 1) → 2A_b/b⁵, since θ₃ = b^(−(P+1−3k)) → 0. The bound of Theorem D3 also holds in the limit.

**The measured tail table, decomposed** (`tails.c h1`, `tail_summary.py`). The enumeration copies H1's population logic: surviving batches, uncertified middle positions, truncated batches included. It reproduces all five H1 rows exactly, e.g. twice-15: 5.1×10⁻⁷, 8.9×10⁻⁵, 4.4×10⁻⁴ over 1,979,316 positions.

| Case | D ≤ 3 events | Where they are | Generic positions: observed vs model |
|---|---:|---|---|
| thrice-13 (4,3) | 46,524 | P = 8, 11, 12, 13, 15; 0 at P = 9, 10 (θ₃ = b⁻¹, b⁻²) | D = 1 at P = 8: 189 vs 188.2; D ≤ 3 at P = 8 / 11 / 12: 11,205 / 5,437 / 10,938 vs 11,044 / 5,428 / 11,038 |
| twice-17 (3,3) | 3,413 | 43% at P = 7 (e₂ = 2, about twice the generic rate) | D ≤ 3 at P = 8 / 11 / 12: 808 / 227 / 775 vs 788 / 250 / 776 |
| twice-15 (3,2) | 881 | 17% in truncated batches (136 at P = 11) | D ≤ 3 at P = 9: 241 vs 265 |
| nice-30 (3,2) | 43 | all at P = 9 (θ₂ on a coarse grid) | 43 vs 94; 0 elsewhere (cubic zone, and θ₂ bounded away from {0, ½}) |
| nice-30 (2,3) | 33,385 | 99.9% at P = 2k = 6, the lattice position | D = 1: 1,152 vs 1,022 predicted by Proposition D5 |

At nice-30 (2,3), P = 6, two effects combine:
- **The end check hides a concentration of θ₁.**
  - Over the whole search interval, the prefix-free θ₁ = {3R²/b⁴} is 5.6 times too concentrated near 0 and ½ for R divisible by 5.
  - That raises D = 1 there to 1.9×10⁻³.
  - The end check removes those R, because their bottom digits repeat; that is why the survivors show the uniform-θ₁ rate.
- **x₀ is not quite uniform there.** A residual correlation involving x₀ adds 4% over the whole interval and 13% among survivors (`p6_x0_check.py`). This is the one place where the actual x₀ differs measurably from a uniform draw.

## 3. The general exponent pair (e₁, e₂)

**Lemma 1_e.** Along the batch n(m) = c + b^k·m, the digit at position P of n(m)^e is ⌊b·{Σ_{i≤e} θ_i m^i}⌋, where
- θ_i = (C(e,i)·c^(e−i) mod b^(P+1−ik))/b^(P+1−ik) when P+1 > ik, and 0 otherwise;
- θ_e = b^(−(P+1−ek)) exactly.

Position P lies in zone i (the sequence has degree i) for ik ≤ P < (i+1)k, and has degree e with a known leading coefficient for P ≥ ek. That makes e+1 zones.

**Theorem S_e.** In the range 1 ≤ j ≤ min(t−1, k+f):
- θ₁ = {e·R^(e−1)/b^J + e(e−1)·R^(e−2)·Ptop/b^j};
- given R, θ₁ is uniform on a coset of the subgroup with g = gcd(e(e−1)R^(e−2), b^j);
- its Fourier coefficients are incomplete Weyl sums of degree e−1 in R.

It was checked exactly for e = 2, 4, 5 in 12 cases (`theorem_s_general_e.py`). I did not write out the limit law for e ≠ 3.

**Theorem A_e.** Let e ≥ 3 and assume:
- L ≤ P and P+1 ≤ (e−1)L;
- P+1 ≥ e(k+f) + ηt;
- k ≥ ηt.

Then (x₀^(e), θ₁^(e)) is equidistributed with discrepancy ≪ N_P^(−η/2^e + ε).

*Proof.* Follow Theorem A with Weyl's inequality in degree e (when h₁ ≠ 0) and degree e−1 (when h₁ = 0). The two denominator exponents lie in:
- [ηt, et − L] ⊂ [ηt, (e−η)t], which uses P+1 ≤ (e−1)L and ηt ≤ L;
- [f + ηt, (e−1)t − k] ⊂ [ηt, (e−1−η)t], which uses k ≥ ηt.

For e = 3 this is D7's corrected Theorem A.

**The wall.** Digit p of n^e is reachable:
- from the bottom only with p+1 digits of n;
- from the top only with about eL − p digits of n.

So the positions reachable from neither end form [L, (e−1)L), of length (e−2)L. It is empty for e ≤ 2. For e = 3 it is the middle third.

**Consequences for a pair (e₁, e₂).** Let E = e₁ + e₂.
- Edges certify 2/E of the output digits. This is Haskin's Theorem 7: a deficiency of about b(1 − 2/E) ([nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean)). His articles, which were presumed to locate the wall, are still unpublished ([janzert.com/nicenumbers/wall/](https://janzert.com/nicenumbers/wall/) returns 404 on 2026-09-27).
- The overlap-join ceiling certifies (min(e₁,2) + min(e₂,2))/E.
- Cost per solution in the random model is about b^M/M! with M = ρb, i.e. ln(cost)/b → κ = ρ(1 − ln ρ).

| Pair | Uncertified by edges (κ) | Uncertified at the ceiling (κ) | Certified at the ceiling |
|---|---|---|---:|
| (1,2) | 0.333 (0.700) | 0 (0) | 100% (no wall) |
| (1,3) | 0.500 (0.847) | 0.250 (0.597) | 75% |
| (2,3) | 0.600 (0.906) | 0.200 (0.522) | 80% |
| (2,4) | 0.667 (0.937) | 0.333 (0.700) | 67% |
| (3,4) | 0.714 (0.955) | 0.429 (0.792) | 57% |
| (3,5) | 0.750 (0.966) | 0.500 (0.847) | 50% |

The (2,3) row reproduces both figures of the algorithm report (0.906 and 0.522). The (1,2)-nice numbers of D1 have no middle wall.

## 4. Formal lower bound: not written

A model does fit on a page:
- batches are a residue class intersected with a prefix interval;
- the algorithm sees the certified digits C(B) and may reject by any rule ρ(C(B));
- it pays |B| full checks for every batch it keeps.

But the model yields no real theorem:
- **Sound for every completion.** The optimal rule is "reject if C(B) repeats a value". The bound Σ_B |B|·1[C(B) distinct] is then an identity, and turning it into the 80% figure needs the random-digit model, which is heuristic.
- **Sound against the actual integers.** "No nice number in B" allows the trivial rule, so the class collapses.

What the theory does contribute rigorously is the "vanishing density" input the model would need, from §2: a middle digit is certified on a b-root batch with limiting frequency:
- 2A_b/b⁵ at generic positions (Proposition A″);
- 0 at cubic-zone positions (Theorem D4);
- order b⁻³ at the lattice position P = 2k (Proposition D5).

## 5. Corrections to middle-digits/REPORT.md

I did not edit that file.

1. **Theorem A** needs P+1 ≤ 2L (D7's finding).
2. **§2, "θ₁ is uniform to sampling accuracy only where Ptop² enters it".** The exact deviations in the Weyl regime reach 0.169 and 0.205 at (3,2), P = 10 and 11, and 0.104 at (4,1), P = 11. The report's figure of 0.03–0.09 understates this. These are finite-size effects of short Weyl sums, not structure.
3. **§5, Remark (ii).** The prefix sum is complete only for j ≤ t−1. The rows (3,2) P = 7 and (2,3) P = 8–10 involve incomplete Dirichlet kernels; the Fourier form in §1 handles them exactly.
4. **§4.**
   - 17% of twice-15's D ≤ 3 events are truncated batches at the ends of the search interval; the share is ≤ 5% in the other cases.
   - "θ₁ within about 1/b²" is made exact by Theorem D2, which also needs θ₂ within about 4/b³ of 0 or ½.
5. **§3.** The model that fits the domain-size law to sampling accuracy is x₀ uniform with the batch's exact θ₁, θ₂ and θ₃. It reaches total variation ≤ 0.002 at every position, where the report's model leaves 0.027 at (2,3), P = 6.

## 6. Unfinished

- The order b⁻⁵ for D ≤ s with s ≥ 2 is measured, not proved. The rigorous bound is s²/b².
- The limit law of Theorem S_e is not written for e ≠ 3.
- The lower bound of step 4 is not written (§4).
- Step 5 was left to D7, which confirmed the sensitivity probabilities.
- The mechanism of the 4–13% x₀ effect at nice-30 (2,3), P = 6 is not identified.

## Files

All in `attack/d6-wall-theory/`:
- `theta1.c`: the exact θ₁ law against the mixture and Fourier formulas.
- `limit_law.py`, `theorem_s_general_e.py`: the limit law ν, and Theorem S for other exponents.
- `tails.c`:
  - mode `h1` re-enumerates the H1 population and runs the structured model;
  - modes `model` and `model2` run the Monte Carlo.
- `tail_summary.py`, `p6_x0_check.py`: the tail decomposition and the P = 6 check.
- `quad_constant.py`: the constants A_b and A = 34/9.
- `three_gap_check.py`, `cubic_exclusion.py`, `exponent_pairs.py`: the checks for D1, D4 and §3.
- `results/`: the output of every script above.

Reproduce:

```sh
clang -O3 -o theta1 theta1.c -lm && clang -O3 -o tails tails.c -lm
for t in 3 2 4; do k=$((5-t)); for P in 6 7 8 9 10 11; do ./theta1 30 6 $t $k 1 $P; done; done > results/theta1_exact.jsonl
python3 limit_law.py; python3 theorem_s_general_e.py
./tails h1 15 2 4618673 11390624 12 18 6 3 2 1 > results/tails_twice15.json   # likewise twice-17, thrice-13, nice-30 (3,2) and (2,3); arguments as in h1-domains/run_cases.sh
python3 tail_summary.py
./tails model2 30 1000000000 12 0 1   # b, samples, seed, cubic exponent, rho; the grid is in results/model_mc.jsonl
python3 quad_constant.py; python3 three_gap_check.py; python3 cubic_exclusion.py; python3 exponent_pairs.py; python3 p6_x0_check.py
```

## Sources

- R. C. Vaughan, *The Hardy–Littlewood Method*, 2nd ed., Cambridge University Press 1997, Lemma 2.4 (Weyl's inequality): https://doi.org/10.1017/CBO9780511470929
- E. M. Stein, *Harmonic Analysis*, Princeton University Press 1993, Ch. VIII (van der Corput's lemma): https://press.princeton.edu/books/hardcover/9780691032160/harmonic-analysis-pms-43-volume-43
- NIST Digital Library of Mathematical Functions, Ch. 7 (Fresnel integrals): https://dlmf.nist.gov/7
- H. Iwaniec and E. Kowalski, *Analytic Number Theory*, AMS Colloquium Publications 53, 2004 (Gauss sums, completion): https://bookstore.ams.org/coll-53
- J. Marklof and A. Strömbergsson, "The three gap theorem and the space of lattices", *American Mathematical Monthly* 124 (2017): https://arxiv.org/abs/1612.04906. The multiplicity form used in Theorem D1 was verified in `three_gap_check.py`.
- M. Drmota and R. Tichy, *Sequences, Discrepancies and Applications*, Lecture Notes in Mathematics 1651 (Erdős–Turán–Koksma inequality): https://doi.org/10.1007/BFb0093404
- B. Haskin, nice-numbers-lean (Theorem 7): https://github.com/Janzert/nice-numbers-lean
- Internal: [middle-digits](../middle-digits/REPORT.md), [p1-algorithm](../p1-algorithm/REPORT.md), [h1-domains](../h1-domains/REPORT.md), D7 audit (`attack/d7-audit/theoremA_counterexample.py`).
