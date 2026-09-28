# D7. Adversarial audit of the September 28 proofs and code

## Goal

Try to break the proofs and the measurement code produced on September 28,
before other agents build on them.

## Why it matters

The critique of the first phase found that the strongest habit of this
project is independent auditing of proofs; several later results (D3, D4,
D6) rest on today's theorems, and the reports state numerical agreements
that depend on the code being right. An audit is one session and protects
several.

## What to audit

1. **The b+1 covering theorem** ([h3-covering §3](../h3-covering/REPORT.md)).
   - Lemma 1 (subset sums of an interval): is the "largest raisable
     element" argument complete when the subset contains u+m−1?
   - Lemma 2: the leading-digit placement needs the parity class of the
     leading position to have at least two positions; check s, c ≥ 4 suffices
     for both words and both parities.
   - Odd b: verify the three digit-set constructions (interval; {1..s} with
     {0} ∪ [s+1, b−1]; {0..s−2} ∪ {s} with {s−1} ∪ [s+1, b−1]) give the
     stated interval lengths e(o−1)+1 and e′(o′−1)+1, and that "2ΣE covers all
     even residues modulo b+1 when ΣE ranges over (b+1)/2 consecutive
     integers" is right.
   - The Corollary's inequalities (even b ≥ 28 from 4b² − 108b − 21 ≥ 0; odd
     b ≥ 21 from 2b − 2 ≥ 40) and the individual bases 17, 19, 24, 25, 27.
     Reproduce the construction in code for b = 10..40 and check every
     residue pair is hit (this also validates `class_dp.py`).
   - Does `cover.c` handle the leading-digit constraint correctly when the
     word has length 1 or 2 (irrelevant for b ≥ 10, but the program allows
     it)? Does its row-rotation code work when M is a multiple of 64?
2. **The middle-digit theorems** ([middle-digits §5](../middle-digits/REPORT.md)).
   - Lemma 1: trivial, but check the square version's coefficients.
   - Theorem A: the reduced denominator of the leading coefficient when h₁ is
     divisible by powers of b; the range conditions for Weyl's inequality
     with the stated exponents; the claim that summing over R loses nothing;
     the use of Erdős–Turán–Koksma with H = N_P^(η/8). Does the theorem need
     P + 1 ≤ 2L anywhere it is not assumed?
   - Proposition A′: the pushforward argument gives uniformity of each pair
     (x_m, x_m′) but the discrepancy transfer under a non-unimodular affine
     map depends on |m − m′| ≤ b; is the o(1) uniform in the pair? Is the
     convexity bound b(b−s)/(2s) correct for non-divisible b/s?
   - Theorems B and C: the position ranges and the handling of the
     frequencies with h₁ + h₂ = 0.
3. **Code and data.**
   - `domains.c`: the Hall matching with capacities (recursive augment): is
     it a correct maximum matching? Test against brute force on random small
     instances. Is the top-edge certification (`p2`, `p3` scans) sound when a
     carry changes a higher digit between n_min and n_max?
   - `smc.c`: is the control (mode 9) charged the same evaluations as the
     sampler? Are witnesses found in chains counted for the sampler but not
     double-counted?
   - `midpoly.c`: the `coeff` mode converts exact rationals to doubles for
     the polynomial model; check this does not bias the domain-size
     comparison (recompute a row with exact rational arithmetic in Python).
   - `models.py` / `summarize.py`: the exact iid occupancy distribution via
     Stirling numbers; check one value by brute force.
   - `quasi_nice.c` (directions/D1): the band computation with integer
     square roots at the boundaries; check bases 6–12 by brute force in
     Python.

## Deliverables

An audit note listing each item as verified, corrected (with the fix
committed), or open, in the repository's usual style. Corrections to report
text should be made in place with a dated remark.

## Stop rules

Bounded: one pass over the list. Anything found wrong that changes a
conclusion must be flagged in PROGRESS.md.
