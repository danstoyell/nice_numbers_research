# Path 2: can we prove that some base has a nice number?

2026-09-27. Hypothesis: some base b, possibly astronomically large and possibly restricted to a structured family of n, provably contains a nice number.

## Verdict

**No approach closes. There is no existence proof here, and nothing in this folder counts as a solution.**

Every approach fails its exponent bookkeeping, most by a factor exponential in b. One new obstruction explains why a whole class of methods fails.

- **Upper bounds alone cannot close, whatever their quality.** The natural circle method writes the count as an integral over a b-dimensional torus. Even the model's own integrand has absolute mass e^(−0.910b), which exceeds the target e^(−b). The main term comes from oscillation, not size.
- **So an asymptotic formula is unavoidable.** It is needed on the region 0.461 ≤ |φ(θ)| ≤ 0.773, where φ(θ) is the model value defined in §1 (Haar measure about e^(−0.225b)), with exponentially small error.
- **This rules out every known tool used on its own:** Mauduit–Rivat and Drmota–Mauduit–Rivat Fourier-property methods, van der Corput, Type II (bilinear) sums, the large sieve, and Maynard-type L1 bounds. All of them produce upper bounds.

The **sharpest missing estimate** (§6) is a b-dimensional local limit theorem, with exponentially small error, for the digit composition of n² and n³. It is not formally reducible to any named problem; no Σ₁ statement is. In the only sense available (any method for it would also settle these), it is at least as hard as two open problems:

- Drmota–Mauduit–Rivat's **Problem 2**, the local distribution of s_q(P(n)) for deg P ≥ 3. DMR state it is open because their bounds are not uniform in α.
- The existence half of **Wu's Conjecture 1**, that a strictly pandigital square exists in every even base b > 4.

All three rough calculations in the brief are confirmed; the second is corrected slightly (§2).

## 1. Setup and exact identities

- **The count.** Fix an admissible base b with candidate interval I_b, N = |I_b| ≈ b^(b/5), square length s and cube length c, where s + c = b. Let F(n) = n² + b^s·n³. For n ∈ I_b, the b digits of F(n) are exactly the digits of n² and n³. Let P be the set of b-digit permutation strings. The count is C_b = Σ_{n∈I_b} 1_P(F(n)).
- **Torus identity (exact; the brief's version is correct).**

  `C_b = ∫_{T^b} e(−Σ_a θ_a) S_b(θ) dθ`, where `S_b(θ) = Σ_{n∈I_b} Π_{positions} e(θ_{digit})`.

  For each θ the summand is a strongly b-multiplicative digital function of F(n). The same digit weight g(a) = e(θ_a) applies at every position.
- **Where the arithmetic main terms sit.**
  - A digital function with one weight for all positions is a character of x mod m only when m | b−1. So the only *arithmetic* spikes are θ_a = t + j·a/(b−1). These are the digit-sum congruence. This matches the fact that the only congruence obstruction is mod b−1.
  - For other linear weights θ_a = u·a, S_b is a Gelfond-type sum. It cancels, but only non-uniformly as u approaches j/(b−1) (DMR Theorem 1 and Remark 1).
  - *Correction to the brief:* the main term does not come from a thin neighbourhood of these points. It comes from a fat region around the diagonal (§3).
- **Model.** Φ_b(θ) = (exact law of the first and last few digits) × φ(θ)^(middle positions) × (singular series mod b−1), where φ(θ) = (1/b)·Σ_a e(θ_a). The random-digit model says S_b ≈ N·Φ_b.
- **Required saving.** Suppose sup_θ |S_b − NΦ_b| ≤ N^(1−η). This proves C_b > 0 iff η > η\*(b) = (ln 2 − ln p_b)/ln N_b ≈ 5/ln b, where p_b = b!/b^b (uncorrected). Values from results/bookkeeping.json:

| b | log₁₀ N | log₁₀ expected count (uncorrected model) | η\*(b) |
|---:|---:|---:|---:|
| 150 | 65.2 | 1.54 | 0.981 |
| 10³ | 600 | 167.6 | 0.721 |
| 10⁴ | 8,000 | 3,659 | 0.543 |
| 10⁶ | 1.2×10⁶ | 7.66×10⁵ | 0.362 |
| 10¹² | 2.4×10¹² | 1.97×10¹² | 0.181 |
| e^2183 (DMR's q₀(3) bound) | — | — | 0.0023 |

The required saving tends to 0. Any fixed power saving would suffice for large enough b, provided it is **uniform in θ and includes the main term**. The rest of the report shows where that fails.

## 2. The brief's three rough calculations, checked

1. **Square-root cancellation.**
   - *Claim:* √N < N·e^(−b) needs b > e¹⁰ ≈ 22,026.
   - *Result: confirmed.* With the exact N_b and p_b, sup-norm square-root cancellation suffices from b = 21,977. Allowing the √(b ln b) loss from taking a supremum over a b-dimensional family, it suffices from b = 22,037. Neither is proved for any b.
2. **Generic Parseval.**
   - *Claim:* ∫|S_b|² counts the pairs (n, n′) whose digit compositions coincide, about N + N²ρ_b, with ρ_b ≈ e^(−1.3b).
   - *Result: corrected.* The exact collision probability of multinomial compositions is ρ_b = (b!)²·b^(−2b)·[x^b] (Σ_k x^k/k!²)^b. Its limiting rate is **e^(−1.2569b)**; at b = 100 it is e^(−1.22b), at b = 1600 e^(−1.254b).
   - Cauchy–Schwarz then gives an error of N·e^(−0.628b) against the needed N·e^(−b). The gap is **e^(0.372b)**. No-go, as the brief said.
3. **Fourier L1 with Type II sums.**
   - *Claim:* this needs η > 1.5.
   - *Result: confirmed as the b → ∞ limit.* By exact FFT for b = 3–7, the Fourier L1 norm of 1_P over Z/b^b, relative to its main term, is 0.85 down to 0.70 × M/√|P| (M = b^b).
   - The saving needed from the exponential sums is therefore η ≥ (ln M − ½ ln b!)/ln N. That is **3.03 at b = 100** and 2.64 at b = 10⁸, tending to **2.5**.
   - If the bottom 40% of digits is handled exactly (n = H·b^j + L), only 60% of digits need Fourier expansion. Then η ≥ **1.98 at b = 100** and 1.62 at b = 10⁸, tending to **1.5**.
   - Both are impossible: η ≤ 1 trivially, and Parseval forces |S(a)|² to average N.

## 3. The new obstruction: the main term is produced by cancellation

- **Absolute mass.** Let A_b = ∫_{T^b} |φ(θ)|^b dθ. For even b this is exactly (m!)²·[x^m](Σ_k x^k/k!²)^b / b^b with m = b/2. It was checked against Monte Carlo (b = 10) and direct enumeration (b = 4).
  - Its rate is **A_b = e^(−0.9104b)**, while the target is p_b = e^(−b+o(b)).
  - At finite b the excess over the target is e^(0.085b) at b = 50 and e^(0.089b) at b = 800.
- **Why this dooms upper bounds.** Any argument that bounds |S_b(θ)| on a set E, rather than S_b − NΦ_b, needs ∫_E N|Φ_b| ≪ N·p_b. Otherwise it cannot even recover the model's own count. Since ∫|Φ_b| ≥ A_b ≫ p_b, E must exclude the region where the model's mass lives.
- **Where asymptotics are unavoidable.** The Cramér rate for |φ| = κ is I(κ) = sup_λ (λκ − ln I₀(λ)). The model's mass exceeds e^(−b) exactly when ln κ − I(κ) > −1. That is the annulus **0.461 ≤ |φ(θ)| ≤ 0.773**, with Haar measure e^(−0.225b).
  - There one needs S_b = NΦ_b + O(N·e^(−0.775b)), averaged over the annulus.
  - Meanwhile |NΦ_b| ranges from N·e^(−0.77b) to N·e^(−0.26b).
  - Typical points of the annulus are θ = t·1 + ψ with random ψ_a of size about 0.3. So the object to compute is the characteristic function of the (b−1)-dimensional digit-composition vector of n²‖n³ at generic points, to precision about e^(−0.78b).
- **The permutation is the mode.** The all-ones composition is the single most likely composition of the multinomial. The problem is therefore a local limit theorem at the mode in b − 1 dimensions.
- **Handling the edges exactly does not help.** Suppose the bottom and top edges (40% of positions) are computed exactly and only the middle m = 0.6b digits are modelled. The excess becomes worse: e^(−0.684b) mass against the target e^(−0.9065b), a gap of **e^(0.222b)**. The annulus becomes 0.245 ≤ |φ| ≤ 0.778.
- **Consequence.** Mauduit–Rivat, Drmota–Mauduit–Rivat, Maynard, Type II and large-sieve estimates are all upper bounds. They can only serve on the complement of the annulus. Even there they are far from sharp:
  - The Fourier-property input for digit-sum phases (DMR Lemma 5(i): |F_λ(h,α)| ≤ e^(π²/48)·q^(−c_q‖(q−1)α‖²λ) with c_q = π²/(12 log q)·(1 − 2/(q+1))) gives at most π²/48 ≈ 0.206 nats of decay per digit.
  - The model's decay is ln(1/|φ_b(u)|), for example 1.55 nats per digit at u = 1.5/(b−1).

## 4. Approach-by-approach bookkeeping

"Gap" means the factor by which the best-case version of the method misses the target.

| # | Approach | Needs | Best available or possible | Gap | Verdict |
|---|---|---|---|---|---|
| A | Circle method on T^b, assuming square-root cancellation | η > η\*(b) ≈ 5/ln b, uniform in θ, with main term | Unproven for every b | — | Go only if the estimate of §6 is proved (b ≥ 21,977) |
| B | Generic Parseval / L2 on T^b | collision rate below e^(−2b) | e^(−1.257b) | e^(0.372b) | No-go |
| C | Any upper-bound method on T^b (MR/DMR Fourier property, van der Corput, Type II, large sieve) | ∫ bound ≤ e^(−b) | ≥ A_b = e^(−0.910b) even with zero loss | e^(0.090b); e^(0.222b) with exact edges | No-go (§3) |
| D | Fourier L1 of 1_P on Z/b^b plus exponential sums (Maynard / Bourgain / Swaenepoel style) | η ≥ 2.5 (≥ 1.5 with bilinear edges) | η ≤ 1 | infinite | No-go |
| E | Preassigned-digit (cylinder) theorems | P contains no cylinder except single strings (all b positions fixed) | Counting caps any cylinder theorem at L = b/5 fixed positions; proven for squares: c₀ ≤ 0.0163 (base 10), 0.040 (base 2⁶⁴); conjectured 1/2 | ≥ 5× even at the counting cap | No-go |
| F | Missing-digit inclusion–exclusion (Maynard) | All digit sets J with \|J\| ≤ 0.78b, relative error 10^(−34.2) (b = 64) to 10^(−282) (b = 512) | Maynard's L1 bound needs structured digit sets (L1 exponent → 0); arbitrary J have per-digit Fourier L1 ≍ √b (exponent ½) | exponent ½ vs ≈ 0 | No-go |
| G | Sieve / Bonferroni over collision pairs | Joint control of depth ≥ ~b collision events | Beyond depth L = b/5 events are rarer than 1/N, so no term-by-term asymptotic exists; at depth L the next term is still ≥ e^(0.29b) (rigorous count of disjoint pairs) against a target of e^(−b) | ≥ e^(1.29b) | No-go |
| H | Lovász Local Lemma / Moser–Tardos | e·p·(d+1) ≤ 1 | 2e ≈ 5.4 even for i.i.d. uniform strings; the arithmetic dependency graph is complete | — | No-go; LLL cannot even prove b! > 0 |
| I | Second moment, Paley–Zygmund, variance over short intervals | A probability space with a computable first moment | C_b is deterministic and its first moment is the problem; the variance form needs pair correlations of an e^(−b) event at precision e^(−2b) | harder than the original | No-go (structural) |
| J | Averaging over bases | Shared cancellation across b | The I_b are disjoint and live on different tori | — | No-go |
| K | Exact-decoupling families (§5) | Independent blocks, reducing to a combinatorial transversal problem | ≤ 40% of output digits can be exactly controlled; the other 60% carry 0.9065 of the exponent | e^(−0.9065b) must come from pseudo-randomness | No-go |
| L | Polynomial method mod p (Chevalley–Warning, Nullstellensatz) | Digits of low degree in the parameters | Carries give digit maps of full degree; Vandermonde^(p−1) has degree ≈ p³/2 | — | No-go |
| M | Special bases (b prime, b−1 prime, powers) | Tractable sums | Changes only the singular series mod b−1; the annulus of §3 is untouched | — | No-go |

Notes on the rows:

- **E.** A cylinder with even one free position contains strings with a repeated digit. The cap follows because a cylinder with r fixed positions has model count N·b^(−r), which falls below 1 once r > L.
- **F.** The Bonferroni depths and required accuracies come from research/existence-counting.md.
- **G.** The mean number of collisions is μ = (b−1)/2. The count of r-matchings times b^(−r) gives E[C(Z, L)] ≥ e^(0.29b).
- **K.** Specific families:
  - *Carry-free patterns:* impossible. The digit sums force S² + S³ = b(b−1)/2, while b distinct digit values need S² ≥ 2L² (the project already proves carrying is essential).
  - *Small-digit roots:* their output digits concentrate unless the digits are ≳ b^(1/4), and then carries are generic.
  - *Progressions n = r + b^m·t:* the block [m, 2m) of n² and n³ becomes affine in t, with slope λ = 3r/2. A "simple" λ (a b-adic rational with small denominator) forces r², r³ to have eventually periodic low digits that repeat. A generic λ is pseudo-random again.
- **Weyl + Erdős–Turán–Koksma (supports A and §6).** A product test on T positions has Fourier L1 cost b^(|T|/2+o(|T|)). The exponential-sum saving is at most N^σ. So this route controls at most |T| ≤ (2σ/5)·b positions:
  - b/15 with the Vinogradov-mean-value Weyl exponent σ = 1/6;
  - 0.4% of positions with DMR's Lemma 3 exponent;
  - b/5 even with square-root cancellation (σ = ½);
  - the middle alone has 3b/5 positions.

## 5. What can be proved: the 40/60 split

**Lemma (bottom-up line structure).** Let gcd(b, 6) = 1. Write n = n′ + t·b^i with i ≥ 1, n′ < b^i and 0 ≤ t < b. Then

`digit_i(n²) = A(n′) + 2n₀t (mod b)` and `digit_i(n³) = B(n′) + 3n₀²t (mod b)`, with n₀ = n mod b.

*Proof.* Modulo b^(i+1), (n′ + t·b^i)² ≡ n′² + 2n′t·b^i and (n′ + t·b^i)³ ≡ n′³ + 3n′²t·b^i. The terms with b^(2i) vanish because 2i ≥ i+1. Also n′·t·b^i ≡ n₀·t·b^i (mod b^(i+1)). ∎

**Consequence.** Suppose n₀ and 2 − 3n₀ are units. Then each new input digit t moves the new output pair along a line whose two coordinates are bijections of t. If the 2i digits below are distinct, at least b − 4i − 1 choices of t keep all 2(i+1) digits distinct. So

`#{n mod b^k : lowest k digits of n² and n³ pairwise distinct} ≥ G_b · Π_{i=1}^{k−1} (b − 4i − 1)`.

Here G_b counts the admissible n₀. edge_lemma_check.py verifies the identity exhaustively and the bound in every case tested:

| b, k | exact count | lower bound |
|---|---:|---:|
| 13, 3 | 469 | 320 |
| 29, 3 | 13,028 | 12,480 |
| 41, 3 | 44,669 | 43,776 |
| 29, 4 | 227,393 | 199,680 |

For k = L this is a rigorous count of n ∈ I_b whose bottom 40% of output digits are distinct.

**The exponent splits exactly.**

`b!/b^b = Π_{j<b} (1 − j/b) = e^(−0.0935b) · e^(−0.9065b)`

- The first factor is the bottom 40% (2L digits) being distinct. The lemma proves it rigorously up to a loss: e^(−0.1195b) instead of e^(−0.0935b).
- The second factor is the remaining 60% (3L digits) completing the permutation. These digits depend on all of n.
- The same holds from the top. Each input digit exactly controls at most 2 output digits from one end, so no family can control more than 40% exactly.

**So 90.65% of the exponent must come from pseudo-randomness of digits that depend on the whole of n.** This is where every approach stops.

## 6. The sharpest missing estimate

**(ME) L1 form.** For some admissible b,

`∫_{T^b} |S_b(θ) − N·Φ_b(θ)| dθ ≤ ½·N·p_b`.

This implies C_b > 0. By §3 it cannot come from upper bounds. It requires an asymptotic formula on the annulus 0.461 ≤ |φ(θ)| ≤ 0.773, together with its b − 2 translates to the arithmetic spikes. The error must be ≲ N·e^(−0.775b), while the main term there is N·e^(−0.26b) to N·e^(−0.77b).

**Pointwise form (the natural target for exponential-sum methods).** sup_θ |S_b(θ) − NΦ_b(θ)| ≤ N^(1−η) with η > 5/ln b. Any fixed uniform η > 0 suffices once b > e^(5/η).

- *Equivalent "mean-zero test" form.* Write each digit weight as mean + h. The requirement becomes power saving for Σ_n w(edges)·Π_{p∈T} h(digit_p(F(n))), uniform over position sets T and mean-zero-type h. The needed saving is η ≥ 5(1 + ln 3)/ln b ≈ 10.5/ln b; the extra 3^b comes from the union bound over T.
- *Framing as pseudorandomness:* the map n ↦ digits(n²‖n³) would have to fool all Fourier shapes (Gopalan–Kane–Meka) with error N^(−5/ln b).

**Status.**

- **Nothing gives asymptotics with exponentially small error** for any digital characteristic function along polynomial values. The best results are:
  - Bassily–Kátai's central limit theorem;
  - Mauduit–Rivat's and DMR's error terms, which are powers of N whose exponent σ = c‖(q−1)α‖² degenerates at the major arcs, in a fixed base q (DMR need q ≥ q₀(3), with q₀(3) ≤ e^2183, and q prime);
  - Swaenepoel's preassigned-digit asymptotics, with relative error n^(−δ).
- **Standard Weyl + Erdős–Turán–Koksma reach at most 1/9 of the middle positions** (§4). The large, spread-out position sets T are uncovered.

**Is it at least as hard as a known open problem?** Not formally: "some base has a nice number" is a Σ₁ statement, so no reduction is possible. In the only available sense (any method for (ME) would also settle these):

1. **Drmota–Mauduit–Rivat, Problem 2 (open for deg P ≥ 3).** Restricted to linear digit weights θ_a = u·a, the pointwise form is an α-uniform, power-saving Gelfond estimate for the cubic F_b, including u → j/(b−1). DMR write that because their estimate is not uniform in α, the local distribution #{n ≤ x : s_q(P(n)) = k} "remains open for d ≥ 3". Spiegelhofer's 2023 result on binary cubes mod 2 does not address this local question. A brief search found no later resolution.
2. **Wu's Conjecture 1 (existence half).** The same estimate for the square alone (F = n², N = b^(b/2), needed saving about 2/ln b) is weaker in every exponent. It would prove that strictly pandigital squares exist in every large even base. Wu conjectures exactly this, and it is open. OEIS A258103 lists counts only up to base 19.

(ME) is harder than both: it demands exponential precision across a b-dimensional family of weights, not one parameter.

## 7. What would change the verdict

- **Asymptotics with exponentially small relative error** for multiplicative digital sums along a polynomial, uniformly over a positive-measure family of digit weights. No such result is known even for the sum of digits.
- **An algebraic mechanism that exactly controls more than 40% of the output digits.** This would break the two-outputs-per-input-digit rate of §5. It is Path 1 (structure) territory, and nothing of the kind is known.

## Files

- bookkeeping.py produces results/bookkeeping.json: η\*(b), the square-root threshold, collision rates, absolute masses, Cramér thresholds, the FFT of 1_P for b ≤ 7, and the derived thresholds. Runs in about 1 s on one core.
- edge_lemma_check.py produces results/edge_lemma_check.json: the exhaustive check of the §5 lemma.

## Sources

- M. Drmota, C. Mauduit, J. Rivat, "The sum-of-digits function of polynomial sequences", J. London Math. Soc. 84 (2011). Used: Theorem 1, Remark 1 (σ = c‖(q−1)α‖², q₀(d) ≤ e^(67d³(log d)²)), Problem 2 (open for d ≥ 3), and Lemma 5(i). [preprint](https://www.dmg.tuwien.ac.at/drmota/dmr6.pdf), [journal](https://academic.oup.com/jlms/article-abstract/84/1/81/882084)
- C. Mauduit, J. Rivat, "La somme des chiffres des carrés", Acta Math. 203 (2009). [link](https://projecteuclid.org/journals/acta-mathematica/volume-203/issue-1/La-somme-des-chiffres-des-carr%c3%a9s/10.1007/s11511-009-0040-0.full)
- C. Mauduit, J. Rivat, "Sur un problème de Gelfond : la somme des chiffres des nombres premiers", Ann. of Math. 171 (2010). [link](https://annals.math.princeton.edu/2010/171-3/p04)
- C. Swaenepoel, "Squares with a positive proportion of preassigned digits". Used: Theorems 1–2, Table 1 (c₀), and Remark 2.8 (conjectured c₀ = 1/2). [pdf](https://webusers.imj-prg.fr/~cathy.swaenepoel/article_squares_AM.pdf)
- J. Maynard, "Primes and polynomials with restricted digits". [arXiv:1510.07711](https://arxiv.org/abs/1510.07711)
- C. W. Wu, "Pandigital and penholodigital numbers", Conjecture 1. [arXiv:2403.20304](https://arxiv.org/abs/2403.20304); counts: [OEIS A258103](https://oeis.org/A258103)
- L. Spiegelhofer, "Thue–Morse along the sequence of cubes". [arXiv:2308.09498](https://arxiv.org/abs/2308.09498)
- P. Gopalan, D. Kane, R. Meka, "Pseudorandomness via the discrete Fourier transform" (Fourier shapes). [arXiv:1506.04350](https://arxiv.org/abs/1506.04350)
- Weyl exponent 1/(k(k−1)) from the Vinogradov mean value theorem: T. D. Wooley, cubic case, [arXiv:1401.3150](https://arxiv.org/abs/1401.3150); J. Bourgain, C. Demeter, L. Guth, [arXiv:1512.01565](https://arxiv.org/abs/1512.01565)
- Project context: critique/research-directions.md, research/existence-counting.md, research/analytic-existence.md
