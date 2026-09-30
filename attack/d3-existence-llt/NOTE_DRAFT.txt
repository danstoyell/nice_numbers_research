# D3. Fixed base, multiplicity k → ∞: the (1,2) existence theorem, reduced to one uniformity lemma

2026-09-28. Task: [D3-existence-llt.md](../directions/D3-existence-llt.md). Code and data are in this folder.

## Verdict

**There is no unconditional existence theorem here, and nothing here is a solution in the owner's sense.** The regime studied is a fixed base b with multiplicity k → ∞. It says nothing about nice numbers proper (k = 1) or about b → ∞; §10 explains why the method cannot reach them.

**1. The (1,2) existence theorem reduces to one hypothesis, Lemma U (§5). U is stated precisely there, together with the three properties (P1)–(P3) of the 2018 proof it needs.** U is a uniform-in-the-weights version of a published bound: Mauduit–Rivat 2018, Theorem 1, for Σ g(n²) e(θn).

> **Theorem A (CONDITIONAL on Lemma U — not proved unconditionally).** Fix b ≥ 2. As k → ∞ through admissible k, the number of n whose base-b digits of n and n² together contain every digit exactly k times is
>
> A_b(k) = (1 + o(1)) · ρ_b(k) · √b · (2πk)^(−(b−1)/2) · |I_b(k)|.
>
> - I_b(k) is the band, with |I_b(k)| ≍ b^(kb/3).
> - ρ_b(k) = #{x mod (b−1) : x + x² ≡ k·b(b−1)/2}. It is at least 1 when k is admissible, and it equals 2^ω(b−1) when b is even or k is even.
>
> In particular A_b(k) > 0 for every admissible k ≥ k₀(b). Admissible means kb ≢ 1 (mod 3) and not (b ≡ 3 (mod 4) and k odd); both conditions are necessary.

**2. Everything except U is proved in this note,** at the level of a research note. The proofs of Lemmas 4–5 are compressed, and an independent check (for example by D7) would be worthwhile. The pieces are:
- the Fourier reduction, with the digit-sum spikes handled exactly (§3);
- a quantitative Fourier-decay bound for arbitrary digit weights (Lemma 1);
- a **twist lemma** (Lemma 2): the digital function of n is annihilated by the second van der Corput step of the Mauduit–Rivat method, so Σ f(n) g(n²) obeys the same bound as Σ g(n²);
- near-spike asymptotics by the method of moments, using (log k)² moments and quadratic Weyl sums only (Lemma 4).

**3. Two unconditional by-products (§7).** Both follow from Mauduit–Rivat 2009 together with Lemmas 2 and 4:
- a power-saving bound for Σ f(n) e(α s_b(n²)), for every strongly b-multiplicative f;
- a local limit theorem for s_b(n) + s_b(n²) on the band.

They concern the one-dimensional digit sum only and produce no k-nice numbers.

**4. The (2,3) case (§8).** It reduces the same way to a cube hypothesis U3. U3 implies DMR's Problem 2 for P = X³ in base b, which is open. In small bases even the non-uniform cube estimate is unknown. The twist lemma does not transfer, because the square's digits survive the differencing.

**5. Numerics (§9).** Exhaustive counts cover b = 6 (k = 2–6), 8 (k = 3, 4), 9 (k = 2, 3), and 4, 7, 10 as controls. Stratified samples cover b = 6 (k = 7–9) and b = 9 (k = 4).
- For b ≥ 6, observed/predicted against the plain multinomial-mode prediction is 0.66–0.95, rising toward 1 at a rate of about 0.6/k (base 6).
- With the exact law of the 2–3 lowest and highest digits (the O(1/k) edge correction), the ratio is 0.93–1.01 for every case with b ≥ 6 and k ≥ 3, and 0.97–1.01 for k ≥ 4.
- Base 4 (7 hits in a band of 128) is too small to mean anything.
- Every hit lies in the residue class the digit-sum congruence predicts.

This is what the local limit theorem predicts. It is a consistency check only.

**How far U is from proved.** I believe U is bookkeeping in a published proof, not a new estimate:
- **Linear weights (θ_d = αd).** U is proved in [MR09] (Théorème 1 with (66), (74), (77)–(79)). The constants depend on α only through ‖(b−1)α‖².
- **General weights.** [MR18, Theorem 1] proves the power saving for every function with the carry and Fourier properties. Every proper strongly b-multiplicative function has both ([DMRS22, Prop. 2] and §3 there use exactly this).
- **Where U is unverified.** §5 states exactly which three properties of the proof of [MR18, Thm 1] U needs:
  - (P1): the implied constant is uniform over the function class, or at most polynomial in 1/c(g);
  - (P2): the saving has the form q^(−a γ(a′ log_q x));
  - (P3): the proof uses the two-step van der Corput skeleton, with the second shift exponent ν₁ ≥ 2ϱ.
  
  [ADM22, Thm 8.5 and §8.2] confirms (P2) and the skeleton in (P3). The inequality in (P3) is inferred, and (P1) is unverified; ADM write that their constant "only depends on d, f and k".
- **Search record.** [MR18] has no open copy that I could find, after a second search (§5). Anyone with the PDF can check (P1) and (P3) in about one session.
- **D3 stop rule.** This is the "follows by a routine extension" branch, but the extension is not written out. **Theorem A is conditional** on U, equivalently on (P1)–(P3).

## 1. Setup, bands and admissibility (two corrections to the D3 file)

Fix a base b = q ≥ 2. Call n **k-(1,2)-nice** if the digits of n (s digits) and of n² (c digits) together contain every digit 0, …, b−1 exactly k times. Then s + c = kb with c ∈ {2s−1, 2s}.

**Bands.**
- If kb ≡ 0 (mod 3): s = kb/3, c = 2s, and I_b(k) = [⌈b^(s−1/2)⌉, b^s).
- If kb ≡ 2 (mod 3): s = (kb+1)/3, c = 2s−1, and I_b(k) = [b^(s−1), ⌈b^(s−1/2)⌉).
- If kb ≡ 1 (mod 3): there is no band.

*Correction:* the D3 file says "bases b ≡ 1 (mod 3) never have a band". That holds only for k = 1. At multiplicity k the condition is kb ≢ 1 (mod 3).

**Digit-sum congruence.** Since s_b(x) ≡ x (mod b−1), every k-nice n satisfies n + n² ≡ t_k := k·b(b−1)/2 (mod b−1).
- If b is even, or k is even, then t_k ≡ 0 and x = 0 is a solution.
- If b is odd and k is odd, then t_k ≡ (b−1)/2. Write v = v₂(b−1).
  - If v = 1, then t_k is odd while x(x+1) is even, so there is no solution.
  - If v ≥ 2, then x(x+1) = ((2x+1)² − 1)/4 runs over all even residues mod 2^v, because odd squares mod 2^(v+2) are exactly the residues ≡ 1 (mod 8). Also x ≡ 0 solves the equation modulo the odd part of b−1. By CRT a solution exists.

So the only congruence obstruction is b ≡ 3 (mod 4) with k odd. *Correction:* the D3 file's "b ≡ 3 (mod 4) fail the digit sum" holds only for odd k.

The last-digit clash only matters at k = 1. §3 shows that the only arithmetic spikes are the mod (b−1) characters, so in this regime there are no hidden congruences.

## 2. Survey: what is proved, with the exact uniformity

| Source | What it proves | Weights | Uniformity | Bearing on D3 |
|---|---|---|---|---|
| Mauduit–Rivat, *La somme des chiffres des carrés*, Acta Math. 203 (2009) [MR09] | Théorème 1: \|Σ_{n≤x} e(α s_q(n²))\| ≤ 4q^(7/2)(log q)^(5/2) τ(q)^(1/2) (1 + log x/log q)^(ω(q)/2+4) · x^(1−σ_q(α)) for every q ≥ 2 and (q−1)α ∉ Z. Théorème 3: s_q(n²) is equidistributed in residue classes, with main term (x/m)·Q(a, (q−1, m)). | Linear only: e(α s_q) | Explicit. σ_q(α) = (99/200)ξ_q(α) (79). ξ_q is linear in c′_q(α) = min{2c_q‖(q−1)α‖², log 2/(2 log q)} ((66), (74)). The threshold ν₁ = max{10, ν₂, 1/(6ξ)} ((75)–(78)) can be dropped at the cost of a constant, because x₀^σ = q^O(1). So the bound is uniform in α. | Minor arcs for linear weights. §5 extracts the method's skeleton: van der Corput with shift r < q^ϱ (Lemme 15), the carry lemma (Lemme 16), van der Corput with shifts s·q^µ (Lemme 17, with µ in the range (73), so µ ≥ 8ν/9), the double truncation f_{µ,λ} (43), and Gauss sums (Prop. 2). The L1 averages (Φ, Lemme 2) are specific to the sum of digits. |
| Drmota–Mauduit–Rivat, JLMS 84 (2011) [DMR11] | Theorem 1: Σ_{n<x} e(α s_q(P(n))) ≪ x^(1−σ) for deg P = d ≥ 2, q ≥ q₀(d) prime, (a_d, q) = 1. Remark 1: σ = c‖(q−1)α‖² and q₀(d) ≤ e^(67d³(log d)²). Problem 2: the local law #{n ≤ x : s_q(P(n)) = k}. | Linear only | The constant depends on α. The method needs 2(d−1)η_q < 1/(11d² log d) (Lemma 5 and §4), where η_q is the L1 exponent (η₂ = 0.5, η₃ ≈ 0.4649), so it needs large q. | Page 4: "For P(X) = X² the estimates obtained in [MR09] are uniform in α so that the methods we used in [DMR09] permit to answer Problem 2 when d = 2. But, as the estimate (2.1) is not uniform in α Problem 2 remains open for d ≥ 3." I found no paper that writes out the d = 2 local theorem. |
| Mauduit–Rivat, *Rudin–Shapiro sequences along squares*, Trans. AMS 370 (2018) [MR18] (not read; see ADM22 and DMRS22) | Theorem 1: a bound for Σ_{n≤x} f(n²) e(nθ), uniform in θ, for every f with the carry property [MR18, Def. 3] and the Fourier property f ∈ F_{γ,c} [MR18, Def. 4]. | **General**: only the L∞ bound sup_t \|q^(−λ) Σ_{u<q^λ} f(u q^α) e(−ut)\| ≤ q^(−γ(λ)) is needed | Exponent through γ. The dependence of the constant is unverified. | This is the tool for general digit weights, i.e. Lemma U. |
| Adamczewski–Drmota–Müllner, Trans. AMS 375 (2022), [arXiv:2009.14773](https://arxiv.org/abs/2009.14773) [ADM22] | Thm 8.5 (matrix-valued MR18): ‖Σ_{0<n≤x} f(n²) e(nθ)‖² ≪_{d,f,k} (log x)^(ω(q)+2) (x k^(−ηγ(2⌊3 log x/(100 log k)⌋)/56)), as printed; for a squared norm the factor must be x². Defs 7.1 (carry) and 7.2 (Fourier). §8.2 sketches MR18's proof: van der Corput in r, carry, then van der Corput with shifts s·k^(ν₁), then the double truncation f_{ν₁,ν₂}. | General (matrix) | "implied constant only depends on d, f and k" | Evidence for U, and confirmation that MR18 has the same two-step skeleton as MR09. |
| Drmota–Mauduit–Rivat–Spiegelhofer, J. Anal. Math. 146 (2022), [arXiv:2001.07898](https://arxiv.org/abs/2001.07898) [DMRS22] | Thm 2: Σ_{n<N} μ(n) g(n²) = o(N) for every strongly b-multiplicative g with \|g\| = 1. Prop. 1: g is periodic iff g(ℓ) = g(1)^ℓ and g(b−1) = 1. Prop. 2: if g is non-periodic then sup_t \|F_λ(t)\| ≤ C e^(−ηλ). §3 applies [MR18, Thm 1] to g(p²n)·conj g(q²n). | **General** | Qualitative | MR18 applies to every proper strongly b-multiplicative function, in every base b ≥ 2. |
| Drmota–Mauduit–Rivat, *Normality along squares*, JEMS 21 (2019) [preprint](https://www.dmg.tuwien.ac.at/drmota/alongsquares.pdf) | Thm 1: t(n²) is normal. Thm 2: Σ_{n<N} e(½ Σ_ℓ α_ℓ s₂((n+ℓ)²)) ≪ N^(1−η). | Base 2, Thue–Morse | η not uniform | Block statistics in *n*, not digit-weight vectors; not the needed object. |
| Müllner, Canad. J. Math. 70 (2018), [arXiv:1704.06472](https://arxiv.org/abs/1704.06472) | Thm 1.4: b(n²) mod m′ is normal for digital (block-additive) b. Thm 1.6: the exponential sum with rational α_ℓ ∈ (1/m′)Z is ≪ N^(1−η). | Rational weights | Non-uniform | Not needed. |
| Drmota–Rivat, [arXiv:2509.17474](https://arxiv.org/abs/2509.17474) (2025) [DR25] | Thm 2: Σ_{n≤x} Λ(n) f(n²) e(θn) ≪ (log x)^(5/2) x^(1−(c(f)/40 − 16η(f)²/5)) for q prime, f proper, η(f) ≤ 1/2000. Defines c(f) and η(f) (2.2); (3.35): sup_t\|F_λ(t)\| ≤ q^(c(f)) q^(−c(f)λ). Prop. 2 is a fully explicit Type I bound. | General, but η(f) ≤ 1/2000 | Fully explicit and uniform | Needs η(f) tiny, i.e. huge bases and near-linear weights. Useless for fixed small b; used here only for c(f) and (3.35). |
| Bassily–Kátai, Acta Math. Hungar. 68 (1995), [doi](https://doi.org/10.1007/BF01874349) (not read) | CLT for q-additive functions along polynomial values ([DMR11, Thm B] for s_q) | By title, general q-additive | Convergence in distribution only | A multivariate CLT follows by Cramér–Wold; no local statement. Lemma 4 replaces it here with a quantitative version. |
| Drmota–Morgenbesser, Israel J. Math. 190 (2012), [doi](https://doi.org/10.1007/s11856-011-0186-2) (not read, paywalled) | Generalized Thue–Morse along squares | — | — | Not needed given MR18. |
| Spiegelhofer, [arXiv:2308.09498](https://arxiv.org/abs/2308.09498) | Parity of s₂(n³) | Base 2, mod 2 | — | No local statement for cubes (§8). |

**Answers to the survey questions in the D3 plan.**
- (a) **Local limit theorem for s_q(n²).** Asserted in [DMR11, p. 4] to follow from [MR09] and the method of [DMR09]. I did not find it written out; §7 proves it (Corollary C covers s_b(n²) alone with f ≡ 1).
- (b) **Joint local limit theorem for the digit-count vector of n².** Not found anywhere.
- (c) **Intervals [x, x+y] with y ≍ x.** Covered: all the bounds hold for every x, so differences give such intervals.
- (d) **Weights of the Fourier property.** The Fourier property is stated for general weights e(θ_d) in [MR18] and [DMRS22]. It is stated only for linear weights e(αd) in [MR09] and [DMR11].

## 3. Fourier reduction with exact spikes

**Count vector and generating sum.** Let X(n) ∈ Z^(b−1) be the vector of counts of the digits 1, …, b−1 in n and n² together. The count of zeros is kb − Σ X_d, which is fixed on the band. For θ ∈ T^(b−1) put θ₀ = 0. Let f_θ be the strongly b-multiplicative function with f_θ(d·b^j) = e(θ_d). Then

  A_b(k) = ∫_{T^(b−1)} S(θ) e(−k Σ_d θ_d) dθ,  where S(θ) = Σ_{n∈I} f_θ(n) f_θ(n²).

One torus T^(b−1) suffices, because only the sum X matters. The D3 plan's T^(b−1) × T^(b−1) would describe the joint law of the two count vectors separately; Lemma 2 handles that too, but it is not needed.

**Spikes.** f_θ is not proper (it equals a character e(jn/(b−1))) exactly at the points θ*_j = (jd/(b−1))_d, j = 0, …, b−2 [DMRS22, Prop. 1], [DR25, Def. 3]. The exact identity is

  Σ_j e(θ*_j · (X(n) − k1)) = Σ_j e(j(s_b(n) + s_b(n²) − t_k)/(b−1)) = (b−1) · 1[n + n² ≡ t_k (mod b−1)].

So the spike neighbourhoods together contribute exactly (b−1) times the integral over the residue class I_t = {n ∈ I : n + n² ≡ t_k}. The congruence enters as a factor ρ_b(k), not as an error term.

**Decomposition.** Let D(θ) = min_j max_d ‖θ_d − jd/(b−1)‖ and r_k = (A log k/k)^(1/2), with A = A(b) large. Split the torus into the spike neighbourhoods B_j = {|θ − θ*_j|_∞ ≤ r_k} and the minor arc 𝔪 = {D ≥ r_k}. These pieces are disjoint once r_k < 1/(2(b−1)).

**Lemma 1 (Fourier decay for arbitrary digit weights).** Let F₁(t) = b^(−1) Σ_{d<b} e(θ_d − dt/b). Then

  max_t |F₁(t) F₁(bt)| ≤ 1 − 8D(θ)²/(9b²).

Hence c(f_θ) := −log max_t|F₁(t)F₁(bt)| / (2 log b) ≥ 4D(θ)²/(9b² log b), and by [DR25, (3.35)], sup_t |F_λ(t)| ≤ b^(c(f_θ)) b^(−c(f_θ)λ).

*Proof.*
1. For any reals w_d with w₀ = 0, |b^(−1) Σ_d e(w_d)|² = 1 − (4/b²) Σ_{d<d′} sin² π(w_d − w_{d′}). Keeping only the pairs (0, d) and using sin²(πx) ≥ 4‖x‖² gives
   |F₁(t)|² ≤ 1 − (16/b²) A,  A = Σ_{d≥1} ‖θ_d − du‖²,
   |F₁(bt)|² ≤ 1 − (16/b²) B,  B = Σ_{d≥1} ‖θ_d − dbu‖²,
   where u = t/b.
2. By AM–GM, |F₁(t)F₁(bt)| ≤ 1 − 8(A+B)/b².
3. Put ε² = A + B. Taking d = 1 in both sums gives ‖(b−1)u‖ ≤ 2ε. So u = j/(b−1) + η with |η| ≤ 2ε/(b−1) for some integer j.
4. Then ‖θ_d − jd/(b−1)‖ ≤ ε + d|η| ≤ 3ε for every d, so D ≤ 3ε. ∎

`check_decay.py` confirms the inequality on 300 random and near-spike θ in each of bases 2, 3, 6, 8, 9, 10. The slack factor ranges from 4 to 300, so the constant 8/9 is conservative.

## 4. The twist lemma: the digits of n cost nothing

**Lemma 2.** Let f be any strongly b-multiplicative function with |f| = 1, and let g : N → U. Run the proof of [MR09, §5] on the twisted sum

  S₁ = Σ_{b^(ν−1) < n ≤ x} f(n) g(n²) e(θn),

with the same parameters ϱ, λ = ν + 2ϱ + 1, and µ ≥ 2ϱ. The result is the chain of inequalities (32) → (37) → (42) for S₁, where:
- S₃(r, s, ν, ϱ, µ) is exactly the same fourfold correlation of the doubly truncated g as for the untwisted sum;
- the only change is an extra error term of at most b^(ν−ϱ) + b^(2ϱ) inside the square root of (37).

Consequently, any bound on Σ g(n²) e(θn) obtained by bounding S₃ uniformly over 1 ≤ |r| < b^ϱ, 1 ≤ |s| < b^(2ϱ) and some µ ∈ [2ϱ, ν − 2ϱ − 1] also holds for Σ f(n) g(n²) e(θn), with the same exponent.

*Proof.*
1. **First van der Corput step** ([MR09, Lemme 15], shift |r| < b^ϱ). The shifted product is
   z_{n+r} conj(z_n) = e(θr) · [f(n+r) conj f(n)] · [g((n+r)²) conj g(n²)].
2. **Carry for f.** Take 0 < r < b^ϱ and write n = H·b^(2ϱ) + L with 0 ≤ L < b^(2ϱ). If L + r < b^(2ϱ), strong multiplicativity gives
   f(n+r) conj f(n) = f(L+r) conj f(L) =: a_r(n),
   which is b^(2ϱ)-periodic in n with |a_r| = 1. The exceptions are the n whose digits at positions ϱ, …, 2ϱ−1 all equal b−1; there are at most (count)·b^(−ϱ) + b^(2ϱ) of them. For r < 0 the exceptional digits are all 0 instead.
3. **Carry for g.** [MR09, Lemme 16] replaces g by g_λ, unchanged.
4. **Second van der Corput step** ([MR09, Lemme 17], with k = b^µ and R = b^(2ϱ)). This multiplies the summand by a_r(n + s·b^µ) conj a_r(n), which equals |a_r(n)|² = 1 because µ ≥ 2ϱ. So f has disappeared, and what remains is [MR09, (41)/(43)] verbatim.
5. **Parameter range.** [MR09] chooses µ ≥ ν(1 + 25ξ/8)/(1 + log 2/(8 log q)) (73) and ϱ ≤ ξν (71), with ξ < 1/25. So µ ≫ 2ϱ automatically. ∎

**Same skeleton in MR18.** [ADM22, §8.2] describes the proof of [MR18, Thm 1]. The second step uses shifts s·k^(ν₁) and cuts the square's digits below ν₁. So Lemma 2 transfers verbatim provided ν₁ ≥ 2ϱ. This is property (P3) of §5; I could not check it in [MR18] itself.

## 5. Lemma U and the minor arcs

**Lemma U (hypothesis; precise form).** Fix a base b ≥ 2. There are constants C, B, κ > 0, depending only on b, such that for all strongly b-multiplicative f, g : N → U, all x ≥ 2 and all θ ∈ R:

  |Σ_{n≤x} f(n) g(n²) e(θn)| ≤ C (log x)^B · x · exp(−κ c(g) log x).   (U)

Here c(g) = −log max_t |F₁(t)F₁(bt)| / (2 log b) is the Fourier-decay constant of [DR25, (2.2)]. It is positive iff g is proper ([DR25, §3.5], citing Martin–Mauduit–Rivat 2014, §5.2), and for g = f_θ it is ≥ 4D(θ)²/(9b² log b) by Lemma 1.

**Only a weak form of U is used.** Theorem A needs (U) only for c(g) ≥ c_k := 4A log k/(9b² k log b) and x ≍ b^(kb/3), i.e. where κ c(g) log x ≍ log k. The following weakenings are harmless:
- an extra term C x^(1−δ) with δ = δ(b) > 0;
- a constant C_ξ ≤ C_b ξ^(−E) (E = E(b)) that grows polynomially as ξ = c(g) → 0, since ξ^(−E) ≤ k^E is absorbed by taking A larger;
- a threshold x ≥ x₀(g) with log x₀(g) ≤ C′ c(g)^(−1) log(2/c(g)), which at c(g) = c_k is ≤ (kb/3 − 1) log b once A ≥ 27C′b/4.

**What U needs from Mauduit–Rivat 2018.** Write 𝓕(γ, c, C_carry) for the class of functions in [MR18, Thm 1]: carry property with constant C_carry [MR18, Def. 3; ADM22, Def. 7.1 with η = 1], and f ∈ F_{γ,c} [MR18, Def. 4; ADM22, Def. 7.2]. Lemma U follows from Lemmas 1 and 2 together with these three properties of [MR18, Thm 1] and its proof:

- **(P1) Uniformity.** The implied constant in [MR18, Thm 1] depends only on the base q, on c and on C_carry. It is not otherwise dependent on f or on γ, beyond the displayed exponent. The weak form suffices: for γ_ξ(λ) = ξ(λ − 1), the constant is ≤ C_q ξ^(−E), and any threshold x₀ satisfies log x₀ ≤ C′ξ^(−1) log(2/ξ).
- **(P2) Shape of the saving.** The bound has the form C (log x)^B · x · q^(−a·γ(⌊a′ log_q x⌋)) with absolute a, a′ > 0.
- **(P3) Skeleton.**
  - The proof bounds the sum through the doubly differenced sums S′₂(r, s), taken uniformly over 1 ≤ |r| < q^ϱ and 1 ≤ |s| < q^(ϱ₂).
  - The first van der Corput step uses shifts r with R = q^ϱ; the second uses shifts s·q^(ν₁).
  - The second shift exponent satisfies ν₁ ≥ 2ϱ + O(1).

*Derivation of U from (P1)–(P3).*
1. **Carry property.** Every strongly b-multiplicative g has it with C_carry = 1. For n₁, n₂ < b^α, the digits of ℓ·b^α + n₁ + n₂ at positions ≥ α + ρ differ from those of ℓ·b^α + n₁ only if ℓ ≡ −1 (mod b^ρ), which happens for ≤ b^(λ−ρ) values ℓ < b^λ. This is the argument of [DMRS22, Lemma 4].
2. **Fourier property.** g ∈ F_{γ,c} for every c, with γ(λ) = c(g)(λ − 1). This follows from [DR25, (3.35)], sup_t |F_λ(t)| ≤ b^(c(g)) b^(−c(g)λ), and from g(u·b^α) = g(u).
3. **The case f ≡ 1.** (P1) and (P2) give |Σ_{n≤x} g(n²) e(θn)| ≤ C (log x)^B x · b^(−a c(g)(a′ log_b x − 2)), which is (U) with κ = a·a′.
4. **Arbitrary f.** (P3) lets the argument of Lemma 2 run inside the proof of [MR18]:
   - the carry exceptions for f add O(x² b^(−ϱ)) to |S|², the same order as the term x²/R already there;
   - a_r(n + s·b^(ν₁)) = a_r(n) because ν₁ ≥ 2ϱ, so f disappears from S′₂(r, s). ∎

**Why (P3) cannot be avoided.** I see no way to get the twisted sum from Theorem 1 of [MR18] used as a black box. After one differencing the summand is a_r(n)·g((n+r)²)·conj g(n²), a correlation along squares that is not of the form F(n²). Either (P3), or a twisted restatement of [MR18, Thm 1], is needed.

**What is verified and what is not.**
- *Linear weights: all three properties hold.*
  - For g = e(α s_b), [MR09] gives (P1)–(P3) explicitly: see (29)–(31), (66), (71), (73)–(79), and Lemmes 15–17.
  - The dependence on α is only through σ_b(α) ≍ ‖(b−1)α‖² ≍ c(g).
  - The threshold ν₁(q, α) ≍ 1/ξ costs only a factor b^O(1).
  - The second shift exponent is µ ≥ 8ν/9 ≫ 2ϱ.
  - So U holds unconditionally for linear weights; this is Corollary B in §7.
- *General weights: partially confirmed.*
  - (P2): the restatement [ADM22, Thm 8.5] displays this shape. For |S| it is a = 1/112, a′ = 0.06, taken from the exponent γ(2⌊3 log x/(100 log k)⌋)/56 for |S|². So κ ≈ 5·10⁻⁴.
  - (P3): [ADM22, §8.2] confirms the two-step skeleton and S′₂(r, s) built from the doubly truncated f_{ν₁,ν₂}. The inequality ν₁ ≥ 2ϱ is inferred, not read: the final saving is γ(2ϱ) with ϱ ≈ 0.03 log_q x, and a saving of that size requires the window [ν₁, ν₂) to have length O(ϱ) and to sit above position ≈ log_q x − O(ϱ).
  - (P1) is unverified. [ADM22] states that its implied constant "only depends on d, f and k". Its prime-number analogue, [ADM22, Thm 7.3], has constants c₁(k), c₂(k) depending only on the base, "with the same constants as in" Mauduit–Rivat's JEMS 2015 paper. That suggests base-only constants in Mauduit–Rivat's general theorems, but it does not prove it for [MR18].

**Search record for [MR18].** Nothing turned up:
- no arXiv version;
- the HAL record [hal-02075857](https://hal.science/hal-02075857v1) has no file;
- Unpaywall and Semantic Scholar list it as closed;
- ams.org and doi.org serve a Cloudflare challenge to scripted access;
- the authors' publication pages give only the DOI;
- I did not locate a thesis reproducing the proof.

Anyone with the PDF can settle (P1) and (P3) directly.

**Lemma 3 (minor arcs, assuming U).** Take A ≥ 27b(B + (b+1)/2)/(4κ). Then

  ∫_𝔪 |S(θ)| dθ ≪ |I| · k^(−(b+1)/2).

*Proof.*
1. On 𝔪, Lemma 1 gives c(f_θ) ≥ 4A log k/(9b² k log b).
2. U applied at the two ends of the band, together with s ≥ kb/3 − 1, gives |S(θ)| ≪ s^B b^s · exp(−4κA log k/(27b)).
3. Since |I| ≍ b^s, this is |I| · O(k^(B − 4κA/(27b))) ≤ |I| · O(k^(−(b+1)/2)). ∎

## 6. Near the spikes: a quantitative CLT without any Mauduit–Rivat input

**Setup.** Let L = ⌈(log k)⁴⌉. Call the digit positions [L, s−L) of n and [L, c−L) of n² the middle, and let m = kb − 4L be their number. Split X = X_mid + X_edge. Put φ₁(ψ) = b^(−1) Σ_{d=0}^{b−1} e(ψ_d) with ψ₀ = 0, and φ_t(ψ) = |I_t|^(−1) Σ_{n∈I_t} e(ψ·X(n)).

**Lemma 4.** For fixed A, uniformly for |ψ|_∞ ≤ r_k:

  |φ_t(ψ) − φ₁(ψ)^m| ≪_{b,A} k^(−1/2) (log k)^(9/2).

*Proof.*
1. **Edges.** |e(ψ·X) − e(ψ·X_mid)| ≤ 2π|ψ|_∞ · 4L ≤ 8π r_k L.
2. **Centring.** Write e(ψ·X_mid) = e(mψ̄) e(Z), where ψ̄ = b^(−1) Σ_d ψ_d and Z = Σ_{p∈mid} h(digit_p) with h(d) = ψ_d − ψ̄. Under the iid-uniform model, E e(ψ·X_mid) = φ₁^m exactly.
3. **Moment comparison.** For m′ ≤ M = 2⌈(log k)²⌉,
   |E_true Z^(m′) − E_model Z^(m′)| ≤ Σ_{tuples ∈ mid^(m′)} (2|ψ|)^(m′) · 2·TV(P),
   where P is the set of positions in the tuple and TV(P) is the total-variation distance between the true law of the digits at P and the uniform law.
4. **Lemma 5.** TV(P) ≤ (C_b k)^(|P|+1) · b^(−L/2) for P in the middle. *Proof:*
   - (i) Expand the pattern indicators exactly in Fourier on Z/b^(e₁) × Z/b^(e₂). The L1 norm, summed over all patterns, is ≤ Π_{p∈P} b(1 + C(p+1) log b), using the Dirichlet-kernel L1 bound for each digit-interval indicator.
   - (ii) Every nonzero frequency with a nonzero coefficient has reduced denominator b^j with j > L. The digits below L are independent of the digits at P under the uniform measure, so smaller denominators give zero coefficients.
   - (iii) For n in a residue class mod b−1 inside the band, sums of e(H₂n²/b^(e₂) + H₁n/b^(e₁)) are bounded as follows. With a quadratic part, use Weyl's bound ≪ N/√(b^j) + √(N log b^j) + √(b^j log b^j) ([DR25, Lemma 17] = Montgomery, *Ten Lectures*, Ch. 3, Thm 1). A linear part alone gives a geometric series ≤ b^j. Since L < j ≤ c − L and c ≤ 2s, both are ≪ k·|I_t|·b^(−L/2). ∎
5. **Summing the moments.** The differences are |Δ_{m′}| ≤ (Ck²)^(m′) · b^(−L/2). The Taylor remainder is bounded by (2π)^M E|Z|^M/M!, and the model is sub-Gaussian with E Z^M ≤ (C M m |ψ|²)^(M/2), where m|ψ|² ≤ Ab log k. Therefore
   |E_true e(Z) − E_model e(Z)| ≤ (M+1)(Ck²)^M b^(−L/2) + (C′A b log k/M)^(M/2) = exp(−(1 + o(1))(log k)² log log k). ∎

## 7. Assembly, and the unconditional corollaries

**Proof of Theorem A (given U).**
1. **Spike region.** By the exact identity of §3, Σ_j ∫_{B_j} = (b−1)|I_t| ∫_{|ψ|≤r_k} φ_t(ψ) e(−kψ·1) dψ.
2. **Lemma 4** replaces φ_t by φ₁^m at total cost (b−1)|I_t| (2r_k)^(b−1) k^(−1/2) (log k)^(9/2) = o(|I| k^(−(b−1)/2)).
3. **Completing the integral.** ∫_{T^(b−1)} φ₁^m e(−kψ·1) dψ is the probability that a Multinomial(m; uniform) vector has counts (k − 4L, k, …, k). The part |ψ| > r_k is negligible because |φ₁|^m ≤ exp(−8m|ψ|²/b²), which follows from Lemma 1's first display.
4. **Stirling.** That probability is √b (2πk)^(−(b−1)/2) (1 + O(L²/k)), since the target is O(L) ≪ √k from the mean.
5. **Congruence.** |I_t| = ρ_b(k)|I|/(b−1) + O(b).
6. **Minor arcs** are handled by Lemma 3. ∎

**Corollary B (unconditional).** For every b ≥ 2, every strongly b-multiplicative f with |f| = 1, and every α with (b−1)α ∉ Z:

  |Σ_{n≤x} f(n) e(α s_b(n²))| ≤ C_b (1 + log_b x)^(ω(b)/2+4) x^(1 − σ_b(α)),

with σ_b(α) as in [MR09, (79)]. *Proof:* [MR09, §5] together with Lemma 2. For x < x₀(b, α) the bound is trivial.

Example: Σ_{n<N} (−1)^(s₂(n) + s₂(n²)) ≪ N^(1−δ). I did not search specifically for prior statements of Corollary B.

**Corollary C (unconditional local limit theorem).** For b ≥ 2 on the band I = I_b(k), uniformly in m:

  #{n ∈ I : s_b(n) + s_b(n²) = m} = |I| · ρ(m) · (2πσ²kb)^(−1/2) · exp(−(m − μkb)²/(2σ²kb)) + o(|I| k^(−1/2)),

where μ = (b−1)/2, σ² = (b²−1)/12 and ρ(m) = #{x mod (b−1) : x + x² ≡ m}.

*Proof:* the proof of Theorem A in dimension 1, with weights θ_d = αd. The minor arcs use Corollary B with f = g = e(α s_b). Lemma 4 applies with ψ_d = ψd.

The same argument with f ≡ 1 gives the local limit theorem for s_b(n²), i.e. DMR's Problem 2 for d = 2, in every base.

These are genuine but small theorems about the one-dimensional shadow of the problem.

## 8. The (2,3) analogue and DMR's Problem 2

**Bands and congruence.** With s′ = len(n²) and c′ = len(n³), s′ + c′ ∈ {5L−3, …, 5L}, so a band exists iff kb ≢ 1 (mod 5). For k = 1 this recovers Haskin's Theorem 1. The congruence n² + n³ ≡ k·b(b−1)/2 (mod b−1) fails only when v₂(b−1) = 1 and k is odd; for v₂ ≥ 2 take x = 2^(v−1) − 1.

**Theorem A3 (conditional).** Assume U3 and the cube analogue of Lemma 4. Then A_b^(2,3)(k) = (1 + o(1)) · ρ₃ · √b · (2πk)^(−(b−1)/2) · |I|, with |I| ≍ b^(kb/5).

**U3.** |Σ_{n≤x} g(n²) h(n³) e(θn)| ≤ C (log x)^B x^(1 − κ c(h)), uniformly over strongly b-multiplicative g, h.

**The cube analogue of Lemma 4** should follow the same way, but it needs cubic Weyl sums with power-of-b denominators and only polylogarithmic loss. Plain Weyl's inequality loses N^ε, which is fatal here. I did not check this.

**Relation to Problem 2.**
- U3 with g ≡ 1 and h = e(α s_b), plus the cube analogue of Lemma 4, is exactly an α-uniform power saving, and it yields the local law for s_b(n³). That is DMR Problem 2 for P = X³ in base b, which [DMR11] states is open because (2.1) is not uniform in α.
- U3 is strictly stronger: it needs all weights, not just linear ones, and a square-digit twist.
- For b below q₀(3) ≤ e^2183, even the non-uniform Gelfond property of s_b(n³) mod m is unknown. The only exception is base 2 mod 2 (Spiegelhofer).
- **The twist lemma fails for (2,3).** After n → n + r, the factor g((n+r)²) conj g(n²) depends on a window of about ν digits of n², not on a short window of n. The second differencing moves n² in all positions ≥ µ, so a quadratic digit factor survives into the cubic correlation.

(2,3) therefore needs genuinely new estimates. By the D3 stop rule I stop at this reduction.

## 9. Numerical check

The code is `count_knice.c`: exhaustive or stratified-sample counts, with packed digit-count tables and 128-bit squares. It was cross-checked against an independent Python brute force on six cases. The prediction script is `predict.py`.

- **"basic"** = |I| · ρ · (kb)!/((k!)^b b^(kb)), the multinomial mode.
- **"refined"** gives the lowest and highest e digits of n and n² their exact joint law (lowest from n mod b^e; highest from n uniform on the band), treats the rest as iid uniform, and conditions the congruence exactly.

Sampled rows used stratified contiguous blocks of 10⁶ roots. Their standard errors are 0.13–0.41%.

| b | k | band | tested | hits | est. count | ρ | basic | obs/basic | refined (e = 2) | obs/ref | refined (e = 3) | obs/ref₃ |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 2 | 766 | all | 5 | 5 | 2 | 5.3 | 0.95 | 3.7 (e=1) | 1.35 | — | — |
| 6 | 3 | 27,608 | all | 55 | 55 | 2 | 74.6 | 0.74 | 58.1 | 0.95 | — | — |
| 6 | 4 | 993,915 | all | 1,158 | 1,158 | 2 | 1,362 | 0.85 | 1,139 | 1.02 | 1,168 | 0.99 |
| 6 | 5 | 3.58e7 | all | 24,587 | 24,587 | 2 | 28,755 | 0.86 | 25,022 | 0.98 | 25,349 | 0.97 |
| 6 | 6 | 1.29e9 | all | 582,862 | 582,862 | 2 | 666,929 | 0.87 | 595,184 | 0.98 | 599,416 | 0.97 |
| 6 | 7 | 4.64e10 | 2e9 | 630,111 | 1.461e7 | 2 | 1.652e7 | 0.88 | 1.500e7 | 0.97 | 1.506e7 | 0.97 |
| 6 | 8 | 1.67e12 | 2e9 | 469,807 | 3.921e8 | 2 | 4.297e8 | 0.91 | 3.952e8 | 0.99 | 3.961e8 | 0.99 |
| 6 | 9 | 6.01e13 | 2e9 | 357,262 | 1.074e10 | 2 | 1.160e10 | 0.93 | 1.078e10 | 1.00 | 1.079e10 | 1.00 |
| 8 | 2 | — | — | — | no band (kb ≡ 1 mod 3) | | | | | | | |
| 8 | 3 | 1.08e7 | all | 1,381 | 1,381 | 2 | 1,697 | 0.81 | 1,483 | 0.93 | 1,437 | 0.96 |
| 8 | 4 | 1.96e9 | all | 100,778 | 100,778 | 2 | 118,470 | 0.85 | 102,467 | 0.98 | 100,139 | 1.01 |
| 9 | 2 | 354,294 | all | 51 | 51 | 2 | 59.0 | 0.86 | 54.6 | 0.93 | — | — |
| 9 | 3 | 2.58e8 | all | 9,031 | 9,031 | 2 | 9,598 | 0.94 | 9,051 | 1.00 | 8,982 | 1.01 |
| 9 | 4 | 1.88e11 | 5e9 | 59,021 | 2.223e6 | 2 | 2.354e6 | 0.94 | 2.248e6 | 0.99 | 2.225e6 | 1.00 |
| 4 | 3 | 128 | all | 7 | 7 | 2 | 5.6 | 1.24 | 5.3 (e=1) | 1.31 | — | — |
| 7 | 2 | 3,952 | all | 12 | 12 | 4 | 15.9 | 0.76 | 12.6 (e=1) | 0.95 | — | — |
| 10 | 2 | 2.16e6 | all | 68 | 68 | 2 | 102.7 | 0.66 | 75.4 | 0.90 | — | — |
| 10 | 3 | 6.84e9 | all | 52,063 | 52,063 | 2 | 59,991 | 0.87 | 52,652 | 0.99 | 52,015 | 1.00 |

**Reading.**
- **The counts are positive at every admissible (b, k) tested**, from k = 2 up. The theorem does not need this; it only shows that k₀(b) is small in practice.
- **The counts grow as |I| · k^(−(b−1)/2)**, i.e. the multinomial-mode prediction, to within a factor 0.66–0.95.
- **The gap closes like c/k** (b ≥ 6; the b = 4 row has only 7 hits). In base 6, (1 − obs/basic)·k = 0.60, 0.73, 0.76, 0.81, 0.70, 0.68 for k = 4, …, 9. This is the O(1/k) correction Theorem A's error term allows.
- **Edge digits explain the gap.** Giving 2–3 digits at each end their exact law brings every k ≥ 3 case with b ≥ 6 to 0.93–1.01. The residual of about 3% in base 6 at k = 5–7 falls to 0.5% by k = 9.
- **Every hit sits in a predicted residue class.** For example, all 9,031 hits for b = 9, k = 3 have n + n² ≡ 4 (mod 8) (`hits_by_n_plus_n2_mod_bm1` in the JSON). This is the exact spike of §3, seen directly.
- **This is only a consistency check.** It confirms the leading term and the edge mechanism. It is not evidence for U, and not evidence about k = 1.

## 10. What this does and does not say

**Nothing about k = 1 or b → ∞.** Every step uses fixed b and k → ∞ essentially:
- The target probability is polynomial, k^(−(b−1)/2).
- U's saving b^(−κ c(g) s) is superpolynomial in k, since s ≍ k, as soon as D(θ) ≫ √(log k/k).
- The spike region is handled by a CLT at scale k^(−1/2) in fixed dimension b−1.

For k = 1 the dimension is b and the target is e^(−b). The minor-arc exponent κ c(g) s ≈ 5·10⁻⁴ · D² · b/5 would have to beat e^(−b) on a set where [p2 §3](../p2-existence/REPORT.md) shows that upper bounds cannot even recover the model's own mass. The p2 barrier is untouched.

**Even conditionally, k₀(b) is enormous.** κ is about 10⁻⁴ and C, B depend on b badly. So Theorem A says nothing about any specific (b, k). The numerics show positivity from k = 2 anyway.

**What would make Theorem A unconditional.** Check (P1) and (P3) of §5 in the proof of [MR18, Thm 1]:
- the implied constant is uniform over the class, or polynomial in 1/c(g), with any threshold satisfying log x₀ ≪ c(g)^(−1) log(2/c(g));
- the second van der Corput shift exponent satisfies ν₁ ≥ 2ϱ.

If both hold, Lemmas 1–4 and §§3–7 complete the proof for every base b ≥ 2. If either fails, the fix is still local: re-run MR18's parameter choices with γ_ξ(λ) = ξ(λ − 1), as [MR09, §5.8] does for linear weights.

This takes about one session for someone with the paper, or 1–2 sessions if parameter choices need redoing. It is the natural next step if the owner wants a rigorous theorem in the family. By the owner's criterion it still would not count as progress on nice numbers.

## Files

- `count_knice.c`: counts k-(1,2)-nice n in base b ≤ 10, exhaustive or stratified sample. It prints JSON with the band, the hits, and the hits by n + n² mod (b−1).
- `predict.py`: the basic and edge-refined predictions. It writes `results/comparison.json` and `results/comparison_table.txt`.
- `check_decay.py`: the numerical check of Lemma 1, written to `results/check_decay.json`.
- `results/counts_{small,mid,large,xl}.jsonl`: the raw counts.

Reproduce (1 core; a few CPU-minutes in total, the largest single runs about 1.5 minutes each):
```sh
clang -O3 -march=native -o count_knice count_knice.c -lm
for b k in 6 2 6 3 6 4 8 2 8 3 9 2; do ./count_knice $b $k; done > results/counts_small.jsonl
(./count_knice 8 4; ./count_knice 9 3; ./count_knice 7 2; ./count_knice 10 2; ./count_knice 4 3) > results/counts_mid.jsonl
(./count_knice 6 5; ./count_knice 6 6; ./count_knice 10 3; ./count_knice 6 7 2000 1000000 11; ./count_knice 9 4 5000 1000000 2026) > results/counts_large.jsonl
(./count_knice 6 8 2000 1000000 88; ./count_knice 6 9 2000 1000000 99) > results/counts_xl.jsonl
python3 predict.py > results/comparison_table.txt; python3 check_decay.py
```

## Sources

- [MR09] C. Mauduit, J. Rivat, *La somme des chiffres des carrés*, Acta Math. 203 (2009) 107–148. Used: Théorèmes 1–3; Lemmes 15–17; (39)–(45), (66), (71)–(79). [Project Euclid](https://projecteuclid.org/journals/acta-mathematica/volume-203/issue-1/La-somme-des-chiffres-des-carr%c3%a9s/10.1007/s11511-009-0040-0.full) ([PDF download](https://projecteuclid.org/journalArticle/Download?urlId=10.1007%2Fs11511-009-0040-0))
- [DMR11] M. Drmota, C. Mauduit, J. Rivat, *The sum-of-digits function of polynomial sequences*, J. London Math. Soc. 84 (2011) 81–102. Used: Theorems 1–3; Remarks 1, 2, 4; Problem 2 and the sentence after it; Lemmas 2, 5. [preprint](https://www.dmg.tuwien.ac.at/drmota/dmr6.pdf), [doi](https://doi.org/10.1112/jlms/jdr003)
- [MR18] C. Mauduit, J. Rivat, *Rudin–Shapiro sequences along squares*, Trans. Amer. Math. Soc. 370 (2018) 7899–7921, Theorem 1 and Definitions 3–4. Not read directly; known through ADM22 and DMRS22. [doi](https://doi.org/10.1090/tran/7210), [HAL record](https://hal.science/hal-02075857v1)
- [ADM22] B. Adamczewski, M. Drmota, C. Müllner, *(Logarithmic) densities for automatic sequences along primes and squares*, Trans. Amer. Math. Soc. 375 (2022) 455–499. Used: Definitions 7.1–7.2, Theorems 7.3 and 8.5, §8.2. [arXiv:2009.14773](https://arxiv.org/abs/2009.14773)
- [DMRS22] M. Drmota, C. Mauduit, J. Rivat, L. Spiegelhofer, *Möbius orthogonality of sequences with maximal entropy*, J. Anal. Math. 146 (2022) 531–548. Used: Theorem 2, Propositions 1–2, Lemma 4, §3. [arXiv:2001.07898](https://arxiv.org/abs/2001.07898), [doi](https://doi.org/10.1007/s11854-022-0201-z)
- [DMR19] M. Drmota, C. Mauduit, J. Rivat, *Normality along squares*, J. Eur. Math. Soc. 21 (2019) 507–548. Used: Theorems 1–2. [preprint](https://www.dmg.tuwien.ac.at/drmota/alongsquares.pdf), [doi](https://doi.org/10.4171/JEMS/843)
- [DR25] M. Drmota, J. Rivat, *Digital functions along squares of prime numbers*. Used: Definition 3, (2.2), Theorem 2, (3.33)–(3.35), Lemmas 9, 12, 17, Proposition 2. [arXiv:2509.17474](https://arxiv.org/abs/2509.17474)
- C. Müllner, *The Rudin–Shapiro sequence and similar sequences are normal along squares*, Canad. J. Math. 70 (2018). Used: Theorems 1.4 and 1.6. [arXiv:1704.06472](https://arxiv.org/abs/1704.06472)
- N. L. Bassily, I. Kátai, *Distribution of the values of q-additive functions on polynomial sequences*, Acta Math. Hungar. 68 (1995) 353–361. Not read; cited as Theorem B in DMR11. [doi](https://doi.org/10.1007/BF01874349)
- M. Drmota, J. F. Morgenbesser, *Generalized Thue–Morse sequences of squares*, Israel J. Math. 190 (2012) 157–193. Not read. [doi](https://doi.org/10.1007/s11856-011-0186-2)
- L. Spiegelhofer, *Thue–Morse along the sequence of cubes*. [arXiv:2308.09498](https://arxiv.org/abs/2308.09498)
- B. Martin, C. Mauduit, J. Rivat, *Théorème des nombres premiers pour les fonctions digitales*, Acta Arith. 165 (2014), §5.2, for c(f) > 0 as cited in DR25. [doi](https://doi.org/10.4064/aa165-1-2)
- Project context: [p2-existence](../p2-existence/REPORT.md) (why k = 1, b → ∞ is blocked), [literature](../literature/REPORT.md), Haskin's [nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean) (Theorems 1–4 for band and congruence at k = 1).
