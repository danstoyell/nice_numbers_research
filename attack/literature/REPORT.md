# Literature survey: nice numbers (square–cube pandigitals)

2026-09-27. Scope: prior work that could plausibly lead to a second nice number or to a proof that 69 is the only one. Topics the project has already covered are not repeated here (the public search, the random model, the p2 existence bookkeeping, family kills, congruences, SAT). Scratch code is in `attack/literature/wu_squares_model.py`.

## Verdict

**I found nothing in the literature that plausibly leads to either outcome.** There is no published or informal claim of a second nice number or of a uniqueness proof. Every closely related "each digit exactly once" problem is in the same state: the only obstruction ever proved is the digit-sum congruence, and no existence result reaches past finite computation. Four findings are new to the project:

1. **Independent work, first commit today: Brian Haskin (Janzert).** He has two Lean 4 repositories and an announced article series, *Nice Numbers and the Middle Digit Wall*.
   - He independently reaches the project's diagnosis (the middle digits are where everything stops).
   - He machine-checks the obstruction theory, and that no nice number exists in bases 2–18 other than 69.
   - He makes one unverified statistical claim about clustering (item 1.4).
2. **The existence half of Wu's Conjecture 1 (strictly pandigital squares) is a strictly easier gate for Path 2, and is blocked by the same obstruction.**
   - I checked the random model against the exact counts: it matches to 0.94 pooled over bases 9–19, and the largest count is 187,562 at base 19.
   - So the conjecture is almost surely true, with astronomically many solutions at large bases, and it is still unproven.
3. **The prefix/suffix overlap join in `p1-algorithm` has prior art.** Geißer–Körner–Kurz–Zahn (2021) used it for squares with three distinct digits.
4. **The twice- and thrice-nice analogues were already known in base 10**, in OEIS A364024 and A174823 (the latter citing De Koninck–Mercier 2004). The multi-base counts in the critique appear to be new.

---

## 1. History and prior art on this exact problem

### 1.1 Origin and popular coverage

**The base-10 property is classical.**
- ProofWiki gives the statement ("the only integer whose square and cube use each of the digits 0–9 exactly once is 69") and cites David Wells, *Curious and Interesting Numbers* (1986, 2nd ed. 1997). [ProofWiki](https://proofwiki.org/wiki/Number_whose_Square_and_Cube_use_all_Digits_Once)
- The base-10 proof is a check of the 53 candidates from 47 to 99.
- Doesn't help: it is a finite check.

**The (n, n²) analogue is older still.**
- 567² = 321489 and 854² = 729316 are credited to Kraitchik's *Mathematical Recreations*. [OEIS A059930](https://oeis.org/A059930)

**3Blue1Brown popularized it.**
- Per Conflux's post, Grant Sanderson mentioned the property during the first *Lockdown Math* livestream (2020). I did not verify this against the video.

**Conflux (Jacob Cohen) posed the multi-base question.**
- [Is 69 unique?](https://beautifulthorns.wixsite.com/home/post/is-69-unique), 2022-12-17. He searched to base 30 and used Stirling to predict that solutions "skyrocket" around base 120–130.
- [Progress update](https://beautifulthorns.wixsite.com/home/post/progress-update-on-the-search-for-nice-numbers), January 2023:
  - the residue filter mod b−1 and the death of b ≡ 3 (mod 4);
  - quasi-nice counts matching the heuristic;
  - Joshua Brower's residue counts;
  - Robin Houston's "multiply-nice" numbers.
- Doesn't help: this is the model the project already uses.

**Other coverage.**
- [Mind Your Decisions (2023-06-09)](https://mindyourdecisions.com/blog/2023/06/09/69-is-the-only-number-with-this-property/) and [Wikipedia: 69](https://en.wikipedia.org/wiki/69_(number)) cover base 10 only.
- I found no Numberphile or Stand-up Maths video, and no Math StackExchange or MathOverflow thread on the multi-base problem.

### 1.2 Prediction markets and forum technical remarks

**Markets.**
- [Manifold: "Is 69 the only nice number?"](https://manifold.markets/PlasmaBallin/is-69-the-only-nice-number) stood at **9% YES** when fetched today.
- Conflux's earlier market was re-issued after the −69 loophole. [Revised market](https://manifold.markets/Conflux/will-i-learn-of-a-nice-number-besid-c68dd57dfc1)

**Thomas Kwa's lattice pointer** (a comment on that market).
- He pointed to [MathOverflow 224013](https://mathoverflow.net/questions/224013/minimal-solution-of-simultaneous-congruences). The answer there encodes set-valued CRT constraints as f(x) = Σ (M/pᵢ)·Π_{a∈Aᵢ}(x−a), then applies Coppersmith.
- Kwa himself noted it does not transfer.
- Doesn't help: the polynomial's degree is |Aᵢ|, and Coppersmith needs roots below M^{1/deg}. For distinct-digit residue sets of size about b^k·p_k, that bound is trivially small.

### 1.3 The search project's own claims

**Claims.**
- [wasabipesto.com/nice](https://wasabipesto.com/nice/): "a very high chance of a nice number past base 120, and maybe even infinitely many out past base 140". Its time table puts bases 10–120 at 2.5×10³⁵ years.
- [nicenumbers.net](https://nicenumbers.net/) makes only qualitative claims.
- [README](https://github.com/wasabipesto/nice): nice numbers "seem to be distributed pseudo-randomly".

**No mathematical roadmap.** The [CHANGELOG](https://github.com/wasabipesto/nice/blob/main/CHANGELOG.md) is engineering only: GPU backends, the Hall-condition MSD filter, and the cross-end residue filter.

**Coverage today (verified via the [bases API](https://data.nicenumbers.net/bases)):**

| Base | Nice-only | Detailed |
|---|---|---|
| 49 | 100% | 53.46% |
| 50 | 100% | 6.94% |
| 52, 53, 54 | 100% | — |
| 57 | 12.68% | — |

### 1.4 Janzert / Brian Haskin: new work (verified by reading the repositories)

**[Janzert/nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean).**
- Repository created 2026-09-27; commits go back to 2026-08-12.
- Lean 4 core, no Mathlib, no `sorry`. The README credits Claude with writing much of the formalization.
- The article site [janzert.com/nicenumbers/wall/](https://janzert.com/nicenumbers/wall/) returns 404 today, so the articles themselves are unpublished.
- Everything is stated for general exponent pairs (e1, e2).

**What it proves:**
- **Thm 1:** the length obstruction, as a biconditional above an explicit threshold (b ≡ 1 mod 5 is dead for (2,3)).
- **Thm 2:** universal last-digit clash.
- **Thm 3:** b ≡ 3 (mod 4) is dead for every exponent pair.
- **Thm 4:** the residue set is empty exactly when v₂(b−1) = 1, or when v₂(b−1) ≥ 3, e2−e1 is even and e1 ∤ v₂(b−1)−1.
- **Thm 5:** congruence sieves.
  - Modulo b^j − 1, a digit pair is worth only its j block totals.
  - The "naive" completeness claim is **false** at base 4 with lengths (2,2).
  - Completeness holds under an explicit block-size hypothesis.
- **Thm 6:** a rigorous upper bound on #nice(b); in base 10 it gives exactly {69}.
- **Thm 7:** the "2/E" construction: deficiency at most b(1 − 2/E), which is the 40% edge.
- **Thms 8–10:** infinitude is equivalent to infinitely many bases containing one; the heuristic count diverges; and a single named hypothesis, `ModelPositive`, implies infinitude.
  - `divergence_is_not_existence` shows that a large heuristic alone is not enough: the (2,3) bases 20s+7 have a divergent heuristic count and are provably empty by Thm 3.

**[Janzert/nice-numbers-certified](https://github.com/Janzert/nice-numbers-certified).**
- Machine-checks that for 2 ≤ b ≤ 18, n is nice in base b iff (n, b) = (69, 10).
- Kernel cost is about 2.3 ms per scanned candidate; bases much past 20 need a different design.

**One unverified claim, in `NOTES.md`:**
> "in exhaustive counts, close pairs of solutions run 1.6× over Poisson at +46σ"

It does not say which exponent pair or which bases.

**Bearing on the goals:**
- Thm 5 is a machine-checked form of the critique's "no hidden congruences" claim, for moduli b^j − 1 (the step to general moduli is one CRT argument the file notes as not done). It is consistent with the critique, which already required long words; base 4 fails only because its words are short.
- Otherwise this is verification. It does not move either goal.
- The clustering claim, even if real, is a constant factor.

### 1.5 OEIS

I searched OEIS for a multi-base nice-number sequence and found none. The base-10 relatives:

| Entry | Content |
|---|---|
| [A085453](https://oeis.org/A085453) | n² and n³ together use distinct digits: 2, 3, 8, 9, 24, 69 |
| [A363905](https://oeis.org/A363905) | n² and n³ together contain every decimal digit (at least once) |
| [A363927](https://oeis.org/A363927) | Every digit occurs equally often; Branicky's b-file has 10,000 terms |
| [A364024](https://oeis.org/A364024) | Least base-10 k-nice number: 69, 6534, 497375, 46839081, …, through k = 9. Terms converge to the digits of 100^{1/3} |
| [A174823](https://oeis.org/A174823) | Thrice-nice in base 10: exactly 10 terms (De Koninck–Mercier 2004, exercise 255) |

Doesn't help. These are fixed-base analogues with polynomially small probabilities; they are not the (2,3) growing-base problem.

---

## 2. Related problems, solved and unsolved

### 2.1 Strictly pandigital squares: Wu, Partridge, OEIS A258103 and A370950

**Statements.** [Wu, arXiv:2403.20304](https://arxiv.org/abs/2403.20304) (v3, 2025-03-13):
- **Thm 1–2 and Cor 1:** if b is odd and v₂(b−1) is even, there is no strictly pandigital square. The only mechanism is the digit sum mod b−1, via the root set A_b.
- **Conjecture 1 (open):** for b > 4, a strictly pandigital square exists **iff** b is even or v₂(b−1) is odd.
- The nonexistence half is Partridge's argument. [Chalkdust, 2015](https://chalkdustmagazine.com/blog/pandigital-square-numbers/)

**Data.** [A258103](https://oeis.org/A258103) gives exact counts only through base 19 (base 18: 24,192; base 19: 187,562). [A370950](https://oeis.org/A370950) gives the zeroless version.

**My check (`wu_squares_model.py`).** Model: E = #{n : n² has b digits, n mod (b−1) ∈ A_b} × (b−1)·(b−1)!/b^{b−1}.

| Bases | Observed | Model | Ratio |
|---|---:|---:|---:|
| 18 | 24,192 | 24,669 | 0.98 |
| 19 | 187,562 | 199,930 | 0.94 |
| 9–19 pooled | 217,253 | 230,589 | 0.94 |

**Bearing on Path 2.** This is the key calibration.
- The expected count is about b^{b/2}·e^{−b}, astronomically large, and the model fits. Yet existence in all large admissible bases is open.
- The p2 absolute-mass obstruction still applies: the model's integrand has absolute mass A_b = e^{−0.91b} against a target of e^{−b}. That comparison depends only on the b-digit output string, not on N or on the polynomial, so it blocks any upper-bound method for squares too.
- **Any nice-number existence proof would have to prove at least Wu's Conjecture 1 first.**
- I found no construction for strictly pandigital squares in infinitely many bases.
- A single rational n = N/d cannot give one. The square's periodic digits follow the orbit ρ → bρ mod d², which stays in the unit group mod d². It therefore visits at most about d² − d values, and injectivity of the digit map needs d² ≤ b. So at most about b − √b digits come from the orbit, and the rest would have to come from O(1) block junctions. This is my inference, in line with the p1-structure kills.

### 2.2 Pandigital oblong numbers

- **Statement:** [A381266](https://oeis.org/A381266) lists the least m with m(m+1) strictly pandigital, found through base 29 by search. Wu proves that b ≡ 3 (mod 4) is empty; the converse is conjectured.
- Doesn't help: the pattern is the same (congruence obstruction only; existence by computation).

### 2.3 Nonexistence mechanisms across all "each digit once" problems

- In squares (Partridge, Wu), oblongs (Wu) and (e1,e2)-powers (Janzert Thms 1–4), the **only** proved obstructions are lengths, last digits and the digit sum mod b−1.
- No non-congruence obstruction exists anywhere in this literature.
- Doesn't help: this confirms Path 3 has no tools.

### 2.4 Digit-condition problems where the heuristic favours finiteness: still open

**[Erdős #406](https://www.erdosproblems.com/406)** (only finitely many powers of 2 have ternary digits in {0,1}).
- Open, and listed in [FrontierMath Erdős (arXiv:2609.25050)](https://arxiv.org/abs/2609.25050) as open in August 2026.
- Saye verified it for n ≤ 2·3⁴⁵ ≈ 5.9×10²¹ using a trailing-digit recursion, which is a bottom-edge method. [arXiv:2202.13256](https://arxiv.org/abs/2202.13256)
- Doesn't help. It calibrates Path 3: even where the heuristic *supports* finiteness, no proof exists, and for nice numbers the heuristic says the opposite.

### 2.5 Digit-permutation problems solved by construction or by exhaustive search

**Self-descriptive numbers.** One exists in every base b ≥ 7: (b−4)b^{b−1} + 2b^{b−2} + b^{b−3} + b³. [Wikipedia](https://en.wikipedia.org/wiki/Self-descriptive_number)
- Doesn't help: no arithmetic map is involved.

**Pandigital polydivisible numbers.** Solutions exist in bases 2, 4, 6, 8, 10 and 14, and exhaustive search is complete to base 72 (except the semiprime bases 62 and 74). [Skirtle's Den](https://skirtlesden.com/articles/pandigital-polydivisible-numbers)
- Search is complete because every constraint is decidable on prefixes.
- Doesn't help. It is the textbook case of what nice numbers lack: the middle digits are not prefix- or suffix-local.

**Squares with three distinct digits** (Geißer, Körner, Kurz, Zahn). [arXiv:2112.00444](https://arxiv.org/abs/2112.00444), §6.
- Lists of root prefixes and suffixes whose square digits lie in D, overlapping in q digits and hash-joined.
- Cost is O(n·3^{0.657n}) instead of 3^n.
- **This is prior art for `p1-algorithm`'s JOIN mode.**
- Doesn't help. It gains a lot when |D| ≪ b, because the lists shrink like |D|^k. Under distinctness the lists shrink only by the distinctness probability. The project's own [cost model](../p1-algorithm/cost_model.txt) at b = 120: edge 10^44.3, overlap join 10^41.9, join plus cross-check 10^40.1, against a ceiling of 10^25.4.

### 2.6 Digits of polynomial values with restricted or prescribed digits

**Maynard, [arXiv:1510.07711](https://arxiv.org/abs/1510.07711).**
- For a sufficiently large base q, there are infinitely many primes missing a digit a₀, and similarly for polynomial values meeting the local conditions.
- These are the only theorems about polynomial values that hold uniformly in large bases.
- Doesn't help: they control one or a few digits; nice numbers need all b.

**Swaenepoel, [squares with preassigned digits](https://webusers.imj-prg.fr/~cathy.swaenepoel/article_squares_AM.pdf).**
- Asymptotics when a proportion c₀ of the digits is preassigned; c₀ is tiny (p2 has the numbers).
- Doesn't help: p2 row E.

---

## 3. Recent work on digits of polynomial values, 2023–2026

None of these is uniform in the base, none is a local limit theorem with exponentially small error, and none controls all digits jointly.

| Paper | Statement | Why it doesn't help |
|---|---|---|
| Spiegelhofer, [arXiv:2308.09498](https://arxiv.org/abs/2308.09498) (2023) | t(n³) = 0 has density ½ | Base 2, one bit of digit sum |
| Drmota–Rivat, [arXiv:2509.17474](https://arxiv.org/abs/2509.17474) (2025) | Prime number theorem for q-multiplicative functions along squares of primes | Fixed base, distributional |
| Drmota–Spiegelhofer, [arXiv:2501.00850](https://arxiv.org/abs/2501.00850) (2025) | Joint distribution of s₂ and s₃ | Linear, not polynomial |
| Leng–Sawhney, [arXiv:2409.06894](https://arxiv.org/abs/2409.06894) (2024) | Vinogradov's theorem with restricted-digit primes (large base, one missing digit) | One digit |
| Green, [arXiv:2309.09383](https://arxiv.org/abs/2309.09383) (2023) | Waring with two-digit sets, b^{160k²} summands | Additive |
| Manai, [arXiv:2606.08325](https://arxiv.org/abs/2606.08325) (2026) | P(X) absolutely normal for random real X with biased Bernoulli digits; sharp exponent n^{−(d−1)/d} | Random reals, not integers |
| Sabuncu 2026; Bazlov 2026; Arévalo–Lalín 2026 | Missing-digit variants (sums of prime squares, function fields) | One digit |

**DMR Problem 2** (local distribution of s_q(P(n)) for deg P ≥ 3) remains open; I found no resolution (p2 had the same result).

---

## 4. Algorithms for middle-digit conditions

**Points near curves: the only algorithms that beat brute force on middle digits.**
- **Elkies, [arXiv:math/0005139](https://arxiv.org/abs/math/0005139)** (ANTS 2000): all solutions of |x³+y³−z³| < M in time L(N)·M (output-sensitive), and 0 < |x³−y²| ≪ x^{1/2} in rigorous O(X^{1/2}L(X)).
- **Stehlé–Lefèvre–Zimmermann, [IEEE TC 54 (2005)](https://ieeexplore.ieee.org/document/1388198/)** (per abstract and summary; I did not read the paper): worst cases of the Table Maker's Dilemma in time N^{4/7} for d = 2 (Lefèvre's method was N^{2/3}), and N^{1/2+ε} for deeper runs.
- **Brisebarre–Hanrot, [arXiv:2606.04858](https://arxiv.org/abs/2606.04858)** (June 2026): Bombieri–Pila/Coppersmith-style algorithms with practical speedups.
- These find n where a run of middle digits of f(n) hits **one** target interval, in time close to the output size.
- Why it doesn't help: the set of acceptable windows (all k-digit windows with distinct digits) is a union of about b^k·p_k intervals with no lattice structure. The per-interval overhead brings back the critique's rate-1 lattice certificates. **I found no mechanism in this literature that shares work across patterns.**

**Truncated nonlinear generators.**
- Blackburn–Gomez-Perez–Gutierrez–Shparlinski, [Math. Comp. 74 (2005)](https://www.ams.org/journals/mcom/2005-74-251/S0025-5718-04-01698-9/S0025-5718-04-01698-9.pdf).
- Bauer–Vergnaud–Zapalowicz, [PKC 2012](https://www.iacr.org/archive/pkc2012/72930609/72930609.pdf).
- They recover the seed of the quadratic or Pollard generator from a *known* proportion of the most significant bits: 2/3 → 1/2 asymptotically for the quadratic generator with known parameters, 3/5 → 1/2 for Pollard.
- Why it doesn't help: they need specific known bits; nice numbers constrain a set of b! targets.

**Meet-in-the-middle and representation techniques** (Howgrave-Graham–Joux 2010; Becker–Coron–Joux 2011).
- Why they don't help: they need an additive or equality decomposition. The middle digits of n² and n³ with n = H·b^m + L depend on H²L and HL² plus carries, with no split. The one additive invariant (the digit sum) is already used.

**Record digit searches.** Saye (trailing-digit recursion), polydivisible (prefix gcd filter), three-digit squares (overlap join), and the public client's Hall-condition MSD filter are all edge methods. None certifies middle digits.

**Grover search.** About √10⁴³ ≈ 10^21.5 sequential iterations of a reversible ~500-bit cube at b ≈ 120. Not feasible, and no gain over the p1 target.

---

## 5. AI-era results, 2025–2026

- **[Wikipedia list of AI discoveries](https://en.wikipedia.org/wiki/List_of_mathematical_discoveries_by_artificial_intelligence):** no entry on digits or pandigital numbers.
- **AlphaProof Nexus** (Tsoukalas et al., [arXiv:2605.22763](https://arxiv.org/abs/2605.22763), May 2026):
  - 44 of 492 OEIS conjectures.
  - It resolved **[Erdős #125](https://www.erdosproblems.com/125)** negatively: A+B has lower density 0, where A and B are the integers with digits {0,1} in bases 3 and 4. The argument is an inductive thinning using 3^m ≈ 4^k.
  - Doesn't help: it is a density statement about digit sets, not polynomial values.
- **Epoch OEIS Open** ([arXiv:2608.11941](https://arxiv.org/abs/2608.11941), Aug 2026):
  - 147 of 492 resolved; the digit items are carry-analysis proofs such as A326746.
  - I checked the benchmark's 444 source sequence IDs ([repo](https://github.com/epoch-research/LeanOpenProblems)). A258103, A370950, A381266, A036745 and the other pandigital sequences are **not** in it, so Wu's conjectures have not been attempted there.
- **Janzert** (§1.4) is Claude-assisted formalization, not new mathematics toward either goal.
- **No claim of a second nice number or a uniqueness proof exists anywhere I searched:** web, arXiv, OEIS, GitHub, Manifold.

---

## 6. Other items

- **Pandigital cubes by base.** No OEIS sequence exists. The model gives about 7 at base 20, about 3×10⁸ candidates, so a search is cheap. It is irrelevant to the goals.
- **Janzert's clustering claim** is the only reported deviation from Poisson-like behaviour, and it is unverified. If it holds for (2,3) near misses beyond edge-sharing, it is a constant-factor effect. It cannot close a 10²³ gap, and it makes naive second-moment arguments harder, not easier.

---

## Top candidates, ranked (none is promising)

1. **Wu's Conjecture 1 as a gate for Path 2.**
   - *Next step:* write one paragraph in `p2-existence` noting that the §3 absolute-mass obstruction applies verbatim to strictly pandigital squares, which are the easier problem. Set arXiv alerts for "pandigital square", "sum of digits" + "local" + "polynomial", and DMR Problem 2.
   - Reopen Path 2 only if Wu's Conjecture 1 is proved for infinitely many bases.
   - *Odds of producing either outcome:* essentially 0 this decade.
2. **Pattern-sharing lattice certification** (Elkies, SLZ, Brisebarre–Hanrot).
   - *Next step:* on the thrice-nice base-16 testbed, test whether one lattice reduction per sub-interval can certify a k-digit window against *all* distinct-digit patterns at once, with cost independent of the number of patterns.
   - Kill it if the rate is at least ½ log b per certified digit (the critique's stopping rule).
   - *Odds:* under 1%. No sharing mechanism is known, and the pattern set is not a lattice neighbourhood.
3. **Janzert's +46σ clustering.**
   - *Next step:* ask for the exponent pair and bases, or wait for the article. Test it on the public near-miss lists for bases 22–50 against an edge-sharing null.
   - *Odds:* 0 for either goal (constant factor). Useful only for correcting heuristics.
4. **Adopt Janzert's Theorems 5 and 6 as the rigorous base.**
   - No bearing on the goals. Cite them instead of re-deriving.

**Assessment.** The literature strengthens the project's conclusions rather than opening a route. Janzert names the same barrier independently (the "middle digit wall"). The strictly-pandigital-squares problem shows that even the easier existence question is out of reach of current analytic tools. The only algorithms known to beat brute force on middle digits need a small number of target intervals, which distinctness does not provide.

## Sources

- [ProofWiki: Number whose square and cube use all digits once](https://proofwiki.org/wiki/Number_whose_Square_and_Cube_use_all_Digits_Once); [Wikipedia: 69](https://en.wikipedia.org/wiki/69_(number)); [Mind Your Decisions](https://mindyourdecisions.com/blog/2023/06/09/69-is-the-only-number-with-this-property/)
- [Conflux, Is 69 unique?](https://beautifulthorns.wixsite.com/home/post/is-69-unique); [Progress update](https://beautifulthorns.wixsite.com/home/post/progress-update-on-the-search-for-nice-numbers); [Manifold (PlasmaBallin)](https://manifold.markets/PlasmaBallin/is-69-the-only-nice-number); [Manifold (Conflux, revised)](https://manifold.markets/Conflux/will-i-learn-of-a-nice-number-besid-c68dd57dfc1); [MathOverflow 224013](https://mathoverflow.net/questions/224013/minimal-solution-of-simultaneous-congruences)
- [wasabipesto.com/nice](https://wasabipesto.com/nice/); [nicenumbers.net](https://nicenumbers.net/); [repo](https://github.com/wasabipesto/nice); [CHANGELOG](https://github.com/wasabipesto/nice/blob/main/CHANGELOG.md); [bases API](https://data.nicenumbers.net/bases)
- [Janzert/nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean); [Janzert/nice-numbers-certified](https://github.com/Janzert/nice-numbers-certified)
- OEIS: [A258103](https://oeis.org/A258103), [A370950](https://oeis.org/A370950), [A381266](https://oeis.org/A381266), [A085453](https://oeis.org/A085453), [A363905](https://oeis.org/A363905), [A363927](https://oeis.org/A363927), [A364024](https://oeis.org/A364024), [A174823](https://oeis.org/A174823), [A059930](https://oeis.org/A059930)
- C. W. Wu, [arXiv:2403.20304](https://arxiv.org/abs/2403.20304); A. Partridge, [Chalkdust](https://chalkdustmagazine.com/blog/pandigital-square-numbers/); [Wu blog](https://accidentaldesultorycogitations.blogspot.com/2024/02/square-pandigital-numbers.html)
- Geißer–Körner–Kurz–Zahn, [arXiv:2112.00444](https://arxiv.org/abs/2112.00444); [Skirtle's Den, polydivisible](https://skirtlesden.com/articles/pandigital-polydivisible-numbers); [Wikipedia: self-descriptive number](https://en.wikipedia.org/wiki/Self-descriptive_number)
- Saye, [arXiv:2202.13256](https://arxiv.org/abs/2202.13256); [Erdős #406](https://www.erdosproblems.com/406); [Erdős #125](https://www.erdosproblems.com/125)
- Maynard, [arXiv:1510.07711](https://arxiv.org/abs/1510.07711); Swaenepoel, [squares with preassigned digits](https://webusers.imj-prg.fr/~cathy.swaenepoel/article_squares_AM.pdf); Spiegelhofer, [arXiv:2308.09498](https://arxiv.org/abs/2308.09498); Müllner, [arXiv:1704.06472](https://arxiv.org/abs/1704.06472); Drmota–Rivat, [arXiv:2509.17474](https://arxiv.org/abs/2509.17474); Drmota–Spiegelhofer, [arXiv:2501.00850](https://arxiv.org/abs/2501.00850); Leng–Sawhney, [arXiv:2409.06894](https://arxiv.org/abs/2409.06894); Green, [arXiv:2309.09383](https://arxiv.org/abs/2309.09383); Manai, [arXiv:2606.08325](https://arxiv.org/abs/2606.08325); Sabuncu, [arXiv:2601.20897](https://arxiv.org/abs/2601.20897)
- Elkies, [arXiv:math/0005139](https://arxiv.org/abs/math/0005139); Stehlé–Lefèvre–Zimmermann, [IEEE TC 2005](https://ieeexplore.ieee.org/document/1388198/); Brisebarre–Hanrot, [arXiv:2606.04858](https://arxiv.org/abs/2606.04858); Blackburn et al., [Math. Comp. 2005](https://www.ams.org/journals/mcom/2005-74-251/S0025-5718-04-01698-9/S0025-5718-04-01698-9.pdf); Bauer–Vergnaud–Zapalowicz, [PKC 2012](https://www.iacr.org/archive/pkc2012/72930609/72930609.pdf)
- [Wikipedia: AI discoveries](https://en.wikipedia.org/wiki/List_of_mathematical_discoveries_by_artificial_intelligence); Tsoukalas et al., [arXiv:2605.22763](https://arxiv.org/abs/2605.22763); Adamczewski, [arXiv:2608.11941](https://arxiv.org/abs/2608.11941); [LeanOpenProblems](https://github.com/epoch-research/LeanOpenProblems); FrontierMath Erdős, [arXiv:2609.25050](https://arxiv.org/abs/2609.25050)
- Scratch code: `attack/literature/wu_squares_model.py`
