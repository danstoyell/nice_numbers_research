# D7: adversarial audit of the September 28 proofs and code

**Nothing I found changes a conclusion.** No second nice number and no new obstruction came out of this audit. One theorem is false as stated, and one proof has a gap; both are fixable, and every application in the reports is unaffected. D3 and D6 must carry the corrected hypotheses.

- **Theorem A (middle-digits §5) is false as stated.** The proof uses P + 1 ≤ 2L twice, but the statement does not assume it. Counterexample: at P + 1 = 3L all stated hypotheses hold, but c³ < b^(P+1), so x₀ = c³/b^(P+1) is a smooth function of c. In base 30 the fraction of batches with x₀ < 1/2 is 0.7866 for every t (checked at t = 3, 4, 6), not 0.5. Adding P + 1 ≤ 2L fixes it. The middle third satisfies that condition, so no conclusion changes. D6 has already taken this in.
- **The proof of Proposition A′ has a gap; its conclusion stands.** The proof pushes Theorem A's equidistribution of (x₀, θ₁) forward under an affine map "plus a constant". But the constant θ₂m² + θ₃m³ depends on the batch, because θ₂ = (3c mod b^(P+1−2k))/b^(P+1−2k). Equidistribution does not survive a batch-dependent translation. The fix is to run Theorem A's Weyl argument directly on the pair; the exact replacement text is below.

Every item on the D7 list is below, marked **verified**, **corrected** (exact before/after given) or **open**. The line numbers refer to the files as they were on 2026-09-28. The corrections have not been applied yet.

## 1. The b+1 covering theorem (h3-covering §3)

| Item | Status | Evidence |
|---|---|---|
| Lemma 1 (subset sums of an interval), including the case u+m−1 ∈ R | **verified** | See note (a). Also run constructively in `h3_construction.py` for every chain used at b = 10–40: each step raises the sum by exactly 1, and the chain has r(m−r)+1 elements. |
| Lemma 2 (leading-digit placement) | **verified** | See note (b). Checked constructively: the builder asserts a nonzero leading digit for every word it builds. |
| Odd b: the three digit-set constructions | **verified** | The intervals have lengths e·o+1, e(o−1)+1 and e′(o′−1)+1 as stated. The digit-set sums change parity by s (s odd) and by 1 (s even), as stated. The step "2ΣE covers all even residues modulo b+1 when ΣE runs over (b+1)/2 consecutive integers" is right. |
| Theorem 1 | **verified** | `h3_construction.py` builds the actual words for b = 10–40 and reduces them modulo b+1. Wherever the hypothesis holds, every admissible pair is realized. It holds at b = 17, 19, 23, 24, 25, 27–30, 32–35 and 37–40, and also at 21, 31 and 36 with the fallback lengths. The construction alone also happens to cover b = 13. |
| Corollary inequalities | **verified** | 4b² − 108b − 21 ≥ 0 first holds at b = 28, and 2b − 2 ≥ 40 gives b ≥ 21. `corollary_check.py`: no violation for any b ≤ 200,000 and any s with 2b−2 < 5s < 2b+3. Below the thresholds the hypothesis holds only at 17, 19 and 24. Bases 25 and 27 are already covered by the odd case, so listing them is redundant but not wrong. |
| class_dp.py | **verified** | An independent numpy DP gives the same image as class_dp.json at M = b+1 for all 31 bases b = 10–40; every image is the full admissible set. class_dp's M = b²−1 rows also agree with cover.c on all 18 common (b, s, M) cases. |
| cover.c: words of length 1 or 2, and M a multiple of 64 | **verified** | Brute force over all permutations for b = 4–9, every s from 1 to b−1, and 18 moduli including 64, 128, 192, 256 and 320: 594 cases, 0 mismatches. `row_rot_or` against a naive rotation for M = 64k−1, 64k, 64k+1 up to 2048 (up to 32 words), every shift: 99,327 tests, 0 mismatches, clean under UBSan. With M a multiple of 64 the top-word mask is skipped correctly, because no bits lie above M. |
| Nit: h3 REPORT.md line 198 | **corrected** (optional) | The length condition is strict. Before: `nice-number interval in base b, so that 3s ≥ 2c − 2, i.e. s ≥ (2b−2)/5, and` After: `nice-number interval in base b, so that 3s > 2c − 2, i.e. s > (2b−2)/5, and` |
| Nit: h3 summarize.py line 56 (generates REPORT line 123) | **corrected** (optional) | Bases 21, 31 and 36 have no nice-number interval and use s = round(2b/5). Append to the f-string, after `for every larger b).`: ` Bases ≡ 1 (mod 5) have no nice-number interval; for them class_dp.py uses s = round(2b/5).` |

Notes to the table:

- (a) Lemma 1. If no element a of R has a+1 ≤ u+m−1 with a+1 ∉ R, then R is closed under successor below u+m−1. That forces u+m−1 ∈ R: otherwise max R would be such an a. So R is the top block. Each raise adds exactly 1 and the sum is bounded, so the chain reaches every value.
- (b) Lemma 2. For s, c ≥ 4 each parity class of either word has at least ⌊s/2⌋ ≥ 2 positions. Both odd-b constructions need this. When s is odd, 0 sits in Y's odd class, which holds the leading position c−1 and has c/2 ≥ 2 positions. When s is even, 0 may sit in either class of X, each with s/2 ≥ 2 positions.

## 2. The middle-digit theorems (middle-digits §5)

| Item | Status | Evidence |
|---|---|---|
| Lemma 1, cube and square coefficients | **verified** | Checked with the reduced residues x₀, θ₁, θ₂, θ₃ in exact arithmetic on 900,000 batches (27 million roots): 0 mismatches. The square's coefficients (2c mod b^(P+1−k), 1/b^(P+1−2k)) are right. |
| Lemma 1 check as described in the report | **corrected** | midpoly's "identity check" (midpoly.c line 67) re-expands (c + b^k m)³, which only tests the binomial theorem. The residue-based double it computes is thrown away (lines 71–72, `(void)y`). Fixes C1 and C2 below. |
| Theorem A: reduced denominator when b divides h₁ | **verified** | q = b^D/gcd(h₁, b^D) ≥ b^D/H. |
| Theorem A: summing over R | **verified** | The leading Ptop-coefficient does not depend on R, and Weyl's bound does not depend on lower-order coefficients. The triangle inequality over R therefore keeps the same normalised bound. |
| Theorem A: Erdős–Turán–Koksma with H = N_P^(η/8) | **verified** | The (log H)² factor goes into ε. η ≤ 1 follows from the hypotheses. |
| Theorem A: P + 1 ≤ 2L | **corrected** | See the top of this note. With k ≥ ηt, P + 1 ≤ 2L is sufficient. Roughly sharp limits: P + 1 ≤ 3L − ηt for x₀, and P + 1 ≤ 2L + k − ηt for θ₁ (above it, θ₁ = 3c²/b^(P+1−k) is smooth). Fixes A1 and A2. |
| Proposition A′: pushforward | **corrected** | Gap described at the top. Fix A3. |
| Proposition A′: is the o(1) uniform in the pair? | **verified** | Once the proof runs through Weyl directly, the frequencies are bounded by 2H and 2(b−1)H, and for fixed b there are only C(b,2) pairs. No transfer under the non-unimodular map is needed. |
| Proposition A′: convexity bound b(b−s)/(2s) when s does not divide b | **verified** | The real relaxation gives exactly b(b−s)/(2s). The integer minimum is at least that, and fewer than s values give more coinciding pairs. Markov's inequality gives s(b−1)/(b(b−s)), which is at most 2s/b when s ≤ b/2. Text nit: fix A4. |
| Theorem B | **verified** | The upper bound is q ≤ b^(2L) ≤ N^(3−η) because f ≥ (2+η)L/3. The lower bound is trivial. The proof actually gives exponent η/4. **But** the claim that "the theorem guarantees 0.03" is wrong: the measured t = 2, L = 6 rows need t ≤ 2(1−η), which fails for every η > 0. At P = 11, q = b^12 = N³, so Weyl gives nothing there. Fixes B1 and B2. |
| Theorem C, including frequencies with h₁ + h₂ = 0 | **verified** | When h₂ = −h₁ ≠ 0 the quadratic's leading coefficient is −3h₁δ/b^(p+1−i), which cannot vanish because 3\|h₁\|δ < 3Hb < b^(ηL). One wording error: the proof says "since L ≤ p + 1", but the hypothesis gives only p+1 ≥ ηL, which suffices. Fix C3. |
| Text after Theorem C: change probability at position i | **corrected** | For i ≥ 1 there is no carry: the change is ≡ 3n₀²δ·b^i (mod b^(i+1)) and the digits below i do not move. With δ ≠ 0, the exact gcd count is 219/290 = 0.7552 for the cube and 24/29 = 0.8276 for the square (`sens_gcd.py`). The measurements at i = 1–4 are 0.755 and 0.828. The report's 0.73 and 0.80 include δ = 0. Fix C4. |

## 3. Code and data

| Item | Status | Evidence |
|---|---|---|
| domains.c Hall matching | **verified** | `hall_ok`/`augment` copied verbatim and compared with exhaustive backtracking: 2,000,000 random instances (up to 8 values, capacities up to 3, up to 12 positions; 1,161,766 feasible), 0 mismatches. Kuhn's search, with each value visited once per augmentation, is complete for capacitated saturating matching. |
| domains.c top-edge certification under carries | **verified** | The scan descends from the top and stops at the first differing digit. Equal digits at every position ≥ p is equivalent to ⌊n²/b^p⌋ being constant over [n_min, n_max], so a carry that changes a higher digit stops the scan. Brute force over all n in 240,000 random windows (bases 3–12): 0 unsound certifications. All seven intervals in run_cases.sh give exactly S2 and S3 digits and are maximal, so the fixed-width digit extraction never truncates. |
| H1 edge batches | **checked** | Truncated batches at the interval ends all have 6–18 roots, never at most 3, so they cannot fake D ≤ 3 trivially. D6 reports that they are 17% of twice-15's D ≤ 3 events. I did not recheck that figure. It only makes "rare" rarer. |
| smc.c control accounting | **verified** | The control spends exactly the budget. The samplers overshoot by at most 1.15×10⁻⁵ of it. Out-of-range proposals cost no evaluation, which is fair. Witnesses are deduplicated by value and re-verified, so chain witnesses count once. The 8,000-entry cap is never approached: about 37 hits per run are expected even at thrice-10. **Latent bug:** the τ = 0 branch (line 118) writes without a bound check and can overflow `wit`. It never ran: τ = 0 was reached in 0 episodes over 150 sampler runs. Fix S1. |
| midpoly.c: double against exact rationals | **verified** | `midpoly_exact.py` replays midpoly's random stream draw for draw for rows (2,3) P = 6, (4,1) P = 10 and (3,2) P = 10, at 300,000 batches each. The measured, iid and model domain-size histograms equal coeff.jsonl exactly. Exact and double arithmetic disagree on 0 of 9 million model digits per row. The histogram maxima (including θ₁ = 0.1849 at (3,2) P = 10) reproduce exactly, so they are real and not a bug. **No bias.** Latent nit: `h0[(int)(x0*nb)]` could index 64 if a double rounds to 1.0 (possible once b^(P+1) > 2^53); this is about 10⁻¹⁵ per sample and never happened. |
| models.py / summarize.py: Stirling occupancy | **verified** | Brute force over all b^N sequences for seven small (b, N) pairs: exact agreement. For b = 13–30 the Stirling recurrence matches inclusion–exclusion. Every "iid exact" mean and every iid P(D ≤ 3) value in the report tables reproduces. The summarize.py slices (`h[1:4]`, the SENS means) are correct. |
| directions/quasi_nice.c | **verified** | Brute force for bases 6–15, enumerating every n with len(n) + len(n²) = b with no band formula and no filter. The band is contiguous and equals quasi_nice's [lo, hi] in every base. The hits agree (20, 174, 500; none at 11–15), and the fresh output is identical to results/quasi_nice_6_22.jsonl. |

## 4. Report text to correct (middle-digits/REPORT.md unless noted)

**A1. Theorem A statement (lines 215–216).**
- Before: `shape (t, k, f) and a position P with P + 1 ≥ 3(k+f) + ηt and k ≥ ηt for some`
- After: `shape (t, k, f) and a position P with 3(k+f) + ηt ≤ P + 1 ≤ 2L and k ≥ ηt for some`
- Add after the ∎ (line 235): `*Remark (D7 audit).* The upper bound P + 1 ≤ 2L is necessary: at P + 1 = 3L the other hypotheses hold, but x₀ = c³/b^(P+1) is smooth in c (P(x₀ < ½) = 0.787 in base 30 for every t).`

**A2. Theorem A proof (line 228).**
- Before: `q ≥ b^(ηt)/H ≥ N_P^(η/2) once H ≤ N_P^(η/4), and P + 1 ≤ 2L gives`
- After: `q ≥ b^(ηt)/H ≥ N_P^(η/2) once H ≤ N_P^(η/4), and the hypothesis P + 1 ≤ 2L gives`

**A3. Proposition A′ proof (lines 253–257).**
- Before: `*Proof.* For m ≠ m′ the map (x₀, θ₁) ↦ (x_m, x_m′) on T² is the affine map with` … through … `is equidistributed on T² and the two digits coincide with probability` (the first five lines of the proof).
- After: `*Proof.* Fix m ≠ m′ and write x_m = x₀ + θ₁m + θ₂m² + θ₃m³. For (g₁, g₂) ≠ 0 the phase g₁x_m + g₂x_m′ equals h₁x₀ + h₂θ₁ + h₃θ₂ + const, with h₁ = g₁+g₂, h₂ = g₁m+g₂m′, h₃ = g₁m²+g₂m′², and (h₁, h₂) ≠ 0 because m ≠ m′. The θ₂ term e(3h₃c/b^(P+1−2k)) is linear in Ptop and θ₃ is constant, so they change only lower-order coefficients in the proof of Theorem A, on which Weyl's bound does not depend. That proof therefore applies with |h₁| ≤ 2H and |h₂| ≤ 2(b−1)H, and (x_m, x_m′) is equidistributed on T², uniformly over the C(b, 2) pairs. (Pushing Theorem A forward does not suffice: the translation θ₂m² + θ₃m³ varies with the batch. D7 audit.) The two digits coincide with probability`

**A4. Line 262.**
- Before: `The bound s/b is far from the measured 10⁻⁶–10⁻³ (§4); the truth needs the`
- After: `The bound 2s/b is far from the measured 10⁻⁶–10⁻³ (§4); the truth needs the`

**B1. Summary (lines 38–39).**
- Before: `- **Over a large batch every middle digit is uniform** (Theorem B; measured` / `  deviations 0.001 where the theorem guarantees 0.03), and **changing any root`
- After: `- **Over a large batch every middle digit is uniform** (Theorem B; measured` / `  deviations 0.001 against the heuristic Weyl scale N^(−1/4) = 0.03; the t = 2 rows lie outside Theorem B's hypothesis t ≤ (1−η)L/3), and **changing any root`

**B2. Table header in summarize.py line 54 and REPORT.md line 305.** Replace `Weyl bound N^(−1/4)` with `Heuristic Weyl scale N^(−1/4)`.

**C1. Lines 78–79.**
- Before: `Checked exactly: \`midpoly coeff\` recomputes the digit from the four residues` / `for every root of every sampled batch; 0 mismatches in 5.4 million batches.`
- After: `Checked exactly: \`midpoly coeff\` recomputes the digit from the expanded terms c³ + 3c²b^k m + 3c b^(2k) m² + b^(3k) m³ for every root of every sampled batch (0 mismatches in 5.4 million batches). The reduced-residue form above was checked in exact arithmetic on 900,000 batches (27 million roots) by the D7 audit (attack/d7-audit/midpoly_exact.py): 0 mismatches.`

**C2. Optional, midpoly.c lines 70–72.** This makes the in-code check test Lemma 1 itself.
- Before:
  ```
              // polynomial model with these exact coefficients (double precision; th's are exact rationals rounded)
              double y = x0 + th1 * m + th2 * (double)m * m + th3 * (double)m * m * m; y -= floor(y);
              (void)y;
  ```
- After:
  ```
              // Lemma 1 as stated: the digit from the REDUCED residues over the common denominator b^(P+1)
              u128 lem = c3 % modP;
              if (e1 > 0) lem += ((3 * c2) % POW[e1]) * POW[k] * (u128)m;
              if (e2 > 0) lem += ((3 * c) % POW[e2]) * POW[2 * k] * (u128)(m * m);
              if (e3 > 0) lem += POW[3 * k] * (u128)(m * m * m);
              if ((int)(((lem % modP) / POW[P]) % b) != d) mismatches++;
  ```

**C3. Theorem C proof (line 287).**
- Before: `L ≤ p + 1 ≤ (3−η)L; a frequency with h₂ = −h₁ ≠ 0 gives the quadratic`
- After: `ηL ≤ p + 1 ≤ (3−η)L; a frequency with h₂ = −h₁ ≠ 0 gives the quadratic`

**C4. Lines 295–297.**
- Before: `digit), so it changes with probability P(b ∤ 3n₀²δ), which the gcd count puts` / `at 0.73 in base 30 (0.80 for the square's 2n₀δ); the measured 0.76 and 0.83` / `include the carry from below. At i = 0 the bottom digit is n₀³ modulo b,`
- After: `digit; the change is exactly 3n₀²δ·b^i modulo b^(i+1), with no carry), so it changes with probability P(b ∤ 3n₀²δ), which the gcd count with δ ≠ 0 puts` / `at 219/290 = 0.755 in base 30 (24/29 = 0.828 for the square's 2n₀δ), matching the measured 0.755 and 0.828` / `(D7 audit). At i = 0 the bottom digit is n₀³ modulo b,`

**D1. §2 reading, lines 135–137** (confirms D6 §5 item 2).
- Before: `- x₀ is close to uniform everywhere; θ₁ is uniform to sampling accuracy only` / `  where Ptop² enters it (P ≥ 3k + 2f: rows (3, 2) at P = 8–9, (4, 1) at` / `  P ≥ 7), as Theorem A predicts. Elsewhere its histogram shows the arithmetic`
- After: `- x₀ deviates from uniform by 0.03–0.09 except at (3, 2), P = 6 (0.18). θ₁ is not uniform to sampling accuracy (0.015) in any row: 0.04–0.19 where Ptop² enters it (P ≥ 3k + 2f), up to 0.75 elsewhere. At this size the threshold does not separate the rows ((2, 3) at P = 9–10, below it: 0.03–0.04; (3, 2) at P = 10–11, above it: 0.19, reproduced in exact arithmetic). Theorem A is asymptotic in t and says nothing quantitative at t ≤ 4. Where θ₁ is far from uniform below the threshold, its histogram shows the arithmetic`

**D2. Lines 148–150.**
- Before: `- The residual deviations of x₀ and θ₁ in the Weyl regime (0.03–0.09) are the`
- After: `- The residual deviations in the rows that meet Theorem A's hypothesis ((3, 2) at P ≥ 9 and (4, 1) at P ≥ 6), 0.03–0.08 for x₀ and 0.04–0.19 for θ₁, are the`

**D3. Lines 141–142.** Row (2,3) at P = 7 differs by 0.042 in the mean.
- Before: `- The polynomial model matches the measured domain sizes to within 0.03 in`
- After: `- The polynomial model matches the measured domain sizes to within 0.03 (0.04 at (2, 3), P = 7) in`

**D4. Summary, line 21.**
- Before: `  to total-variation distance 0.002–0.011** at every middle position and batch`
- After: `  to total-variation distance 0.002–0.011** at 17 of the 18 middle positions and batch shapes tested (0.027 at (2, 3), P = 6; see D6 for a model that closes it), at every other middle position and batch`
- (Or simply rephrase to drop "every".)

**D5. Summary, lines 36–37: open / overstated.** No code links H1's extra rejections to the D ≤ 3 domains; a Hall failure can also come from several mid-sized domains together.
- Before: `  b; here they are seen directly, and they are exactly the extra rejections` / `  H1 measured.`
- After: `  b; here they are seen directly, and they are the likely source of the extra rejections H1 measured (not checked batch by batch).`

**P1. PROGRESS.md line 98.**
- Before: `  with the block zeroed. This is exact and was checked on 5.4 million batches.`
- After: `  with the block zeroed. This is exact (a two-line proof) and was checked in exact arithmetic on 900,000 batches.`

**P2. PROGRESS.md lines 101–102.**
- Before: `  middle digit takes along a batch** to within 0.2–1% at every position and` / `  batch shape tested, where independent random digits are off by up to 68%.`
- After: `  middle digit takes along a batch** to within 0.2–1.1% at 17 of 18 positions and` / `  batch shapes tested (2.7% at the last), where independent random digits are off by up to 68%.`

**P3. PROGRESS.md lines 112–113.**
- Before: `  algorithm report costed at one digit per factor b, seen directly; they` / `  account exactly for H1's negligible extra rejections.`
- After: `  algorithm report costed at one digit per factor b, seen directly; they` / `  are the likely source of H1's negligible extra rejections.`

**PROGRESS.md flag.** Suggested line under "What the middle digits actually are": `D7 audit: Theorem A needs P + 1 ≤ 2L (false without it) and Proposition A′'s proof needed a direct Weyl argument; both fixed, no conclusion changes.`

**S1. smc.c line 118.**
- Before: `                for (int i = 0; i < nseed; ++i) wit[nwit++] = pop[i].n;`
- After: `                for (int i = 0; i < nseed && nwit < 4 * P; ++i) wit[nwit++] = pop[i].n;`

## 5. Open

- D5 above: the "exactly the extra rejections" claim is unverified.
- D6 §5 item 3 (Remark (ii): the Ptop-sum is complete only for j ≤ t−1) and D6's 17% truncated-batch share at twice-15 were not independently rechecked.
- The ASan build of the rotation test hangs on this machine (a toolchain issue); the UBSan and plain builds pass.

## Files

Everything is in `attack/d7-audit/`:
- `h3_construction.py` (writes results/h3_construction.json)
- `corollary_check.py`
- `cover_bruteforce.py`
- `rowrot_test.c`
- `hall_test.c`
- `stirling_check.py`
- `midpoly_exact.py` (writes results/midpoly_exact.jsonl)
- `sens_gcd.py`
- `theoremA_counterexample.py`
- `quasi_nice_bruteforce.py`
- binaries in `bin/`

No existing file was modified, and nothing was committed.
