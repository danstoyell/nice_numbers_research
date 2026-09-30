# Machine-checked core in Lean 4 (direction D4)

2026-09-28. Direction [D4](../../attack/directions/D4-lean-core.md).

`NiceCore.lean` is one self-contained file: 2,124 lines and 117 theorems, in Lean 4 core with no Mathlib, no `sorry` and no `native_decide`. It follows the style and digit definitions of Brian Haskin's [nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean).

Check it from this directory:

```sh
lean NiceCore.lean   # the lean-toolchain file pins v4.33.0, Haskin's version
```

It exits 0 in about 20–30 s on one core; `lake build` also succeeds. The `#print axioms` block at the end covers 44 headline results.
- 33 of them list only `propext`, `Classical.choice` and `Quot.sound`, or a subset.
- The other 11 (certificate checks and numeric witnesses) use no axioms at all.

## Status

Targets 1–3 of D4 are done. Target 4, the middle-third wall, was stopped under the D4 stop rule as unexpectedly heavy (see below). Formalization found no flaw in the informal proofs; it sharpened two statements.

## Statements proved

**1. Batch digit formula (Lemma 1 of [middle-digits](../../attack/middle-digits/REPORT.md)).**
- `batch_cube_digit` and `batch_square_digit`: for n = c + b^k·m, the digit of n³ at P is (A mod b^(P+1)) / b^P, where A = c³ mod b^(P+1) + (3c² mod b^(P+1−k))·m·b^k + (3c mod b^(P+1−2k))·m²·b^(2k) + (1 mod b^(P+1−3k))·m³·b^(3k).
- This holds for every P, k, m and b. Truncated subtraction gives the report's "else 0" automatically, so the hypothesis P ≥ k is not needed.
- Corollaries:
  - `batch_low_digit_const`: digits below k are constant along the batch, for every exponent.
  - `batch_cube_rotation_only`: for P+1 ≤ 2k, the digit depends on m only through (3c² mod b^(P+1−k))·m mod b^(P+1−k). The square version is the same with slope 2c.
  - `batch_cube_quadratic`: the cubic term drops for P+1 ≤ 3k.
- Witnesses:
  - The formula reads all six digits of 69³ correctly.
  - It holds on a base-30 batch where every residue is genuinely reduced.
  - The rotation zone really moves.
  - The tail modulus and the zone boundary are sharp.

**2. Subset sums of an interval (Lemma 1 of [h3-covering](../../attack/h3-covering/REPORT.md)).**
- `subset_sums_iff`: for r ≤ m, σ is an r-subset sum of {u, …, u+m−1} iff r·u + tri r ≤ σ ≤ r·u + tri r + r(m−r).
- The new half is `subset_bounds`, which Haskin's NOTES list as missing.
- `subset_sum_top` converts the upper end to the report's r(2m−r−1)/2 form.

**3. Covering modulo b+1 (Theorem 1 and Corollary of h3-covering).**
- `cover_b_plus_one_iff`: under the class-size hypothesis, a residue pair mod b+1 is realised by a pandigital split with nonzero leading digits iff x+y ≡ T (mod gcd(2, b−1)).
  - Sufficiency is the report's construction, including the parity swap.
  - Necessity (`realised_compatible`) is new.
- `cover_nice_lengths` extends this to every base b ≥ 10. `candidate_lengths` shows every candidate has 2b ≤ 5s+1 and 5s ≤ 2b+2.
- Headline, `cover_candidate`: for every b ≥ 10 and every n whose square and cube have b digits between them, the residue pairs mod b+1 of pandigital splits with those lengths are exactly the pairs the digit sum permits.
- Small bases:
  - Bases 10, 12, 13, 14, 15, 18, 20 and 22 are settled by certificates with one or two digit partitions each. A kernel-evaluated checker (`certOK`) is proved sound (`realised_of_cert`), so the certificates need not be trusted. They came from a greedy search script kept in scratch, not in the repo.
  - Base 24 is settled by `decide` on the Theorem 1 hypothesis.
- Witnesses:
  - 69's split realises its own residues (9, 5).
  - The hypothesis fails at base 10, which is why certificates are needed.
  - A 2-digit square word fails at base 10, so the length hypothesis is load-bearing.
  - The parity condition bites at base 13.

## What formalizing found

- **Corollary threshold.** The report's odd-base threshold of 21 can be lowered to **17**, and both thresholds are then sharp:
  - even b = 28 fails at (26, s = 10);
  - odd b = 17 fails at (15, s = 6).

  The Lean names are `cover_cond_large`, `cover_cond_twentysix_fails` and `cover_cond_fifteen_fails`. This agrees with the D7 audit's observation that the hypothesis holds at 17 and 19. Using the report's own weaker length hypothesis (5s ≥ 2b−2, s ≤ c), the Lean proof covers every such s.
- **Lemma 1** needs no P ≥ k hypothesis (see above).
- **No flaw found** in middle-digits Lemma 1, or in h3-covering Lemma 1, Theorem 1 or the Corollary.
- **The D7 audit's Theorem A issue** (it needs P+1 ≤ 2L) does not touch these targets. Lemma 1 is proved unconditionally.

## Mutation tests: 22 of 22 rejected

Each mutant was compiled on its own and failed. The mutants were:
- the Lemma 1 tail moduli, the linear coefficient, and dropping the cubic term;
- widening the zone hypotheses P < k and P+1 ≤ 2k;
- the subset-sum ends ±1, and dropping r ≤ m;
- dropping `Compatible` from Theorem 1, weakening e(o−1) to e·o, and weakening 4 ≤ s to 3 ≤ s;
- lowering the two Corollary thresholds, lowering the base bound to 9, and widening the band;
- one perturbed residue and one perturbed mask in two certificates;
- shifting the parity target to T+1;
- strengthening the candidate-length bound;
- a wrong residue in the 69 witness;
- a flipped sign in the word-residue lemma.

Most mutants are provably false statements, and a witness in the file pins them. Four failed only because the proof broke, so their truth is unknown: weakening e(o−1) to e·o, 4 ≤ s to 3 ≤ s, b ≥ 10 to b ≥ 9, and widening the band.

## Target 4 (the wall): stopped as heavy

No uniform witness construction emerged.
- The clean engine is simple: two cubes differ at P if digit_P(Δ) ∈ [1, b−2].
- The obvious base point b^(L−1) fails when the free window is a single low digit. For example, at L = 10, k = 0, t = 9, P = 14 no nonzero term lands at 14.
- Sparse roots b^(L−1) + b^i + b^j do give explicit digits (1, 3, 6). But they need:
  - a case split on where P sits relative to k and L, with parity sub-cases in the rotation zone;
  - collision-avoidance among about 10 term positions;
  - separate handling of b ≤ 6, where 3 and 6 carry.
- The estimate is several hundred lines. Per-(b, L) witnesses by finite search would be easy, but they are only instances, not the "every b ≥ 3, L" statement.

## Offering it upstream

§A copies 39 of Haskin's definitions and lemmas verbatim, extracted by script, so the file checks on its own. They include `slot`, `digits`, `occ`, `valOf`, `run`, `tri`, `pick`, `pick_sum`, `nth`, `dropZeros` and `bounds_of_numDigits`.

§B–§E, appended to Haskin's actual `NiceNumbers.lean` without the copies, compile with no name clashes. A pull request would just delete §A. No pull request or issue has been opened.

## Files

- `NiceCore.lean`, `lean-toolchain` (v4.33.0) and `lakefile.toml`.
- The certificate generator, the mutation script and its log stayed in scratch (`/private/tmp/nice-lean/work/`), and are not needed to check the result.
