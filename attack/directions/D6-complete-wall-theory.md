# D6. Complete the middle-digit theory

## Goal

Turn the description in [middle-digits/REPORT.md](../middle-digits/REPORT.md)
into a complete theory: exact distributions in the regime the Weyl bound does
not reach, sharp bounds on degenerate batches, the general exponent pair, and
a lower bound in a formal computational model.

## Why it matters

Low bearing on the two outcomes: the theory already says what the middle
digits are and why no certificate helps. The value is completeness and
durability: a clean theorem that any future "middle-digit trick" would have to
contradict, and a formal lower bound that turns the informal ceiling of the
algorithm report into a statement about a class of algorithms.

## What is known

- Lemma 1 (exact): along a batch with free block at position k, the digit at
  P of n³ is ⌊b·{x₀ + θ₁m + θ₂m² + θ₃m³}⌋ with x₀, θ₁, θ₂ digit-tails of c³,
  3c², 3c and θ₃ = b^(−(P+1−3k)).
- Theorem A: (x₀, θ₁) equidistributed over batches when P + 1 ≥ 3(k+f) + ηt
  and k ≥ ηt (cubic and quadratic Weyl sums over the prefix variable).
- Below that threshold θ₁ is the digit-tail of 6·Ptop·R + 3R² modulo
  b^(P+1−k); the prefix enters linearly or not at all, the sums over the
  prefix are complete geometric or Gauss sums, and the distribution is a
  mixture over the classes of gcd(6R, b^(P+1−2k−f)). Measured, not proved.
- Proposition A′: P(a digit takes ≤ s values along a batch of b roots) ≤ 2s/b
  + o(1), by pair coincidences and Markov. Measured: 10⁻⁶–10⁻³ for s = 3.
- Theorems B (large batches) and C (sensitivity), with explicit ranges of
  positions.

## Plan

1. **Structured regime.** For positions 2(k+f) ≤ P < 3(k+f), compute the
   distribution of θ₁ over batches exactly as a mixture: for each divisor
   class of gcd(6R, b^j), the prefix sum is a complete sum, and the R-sum is an
   incomplete quadratic Gauss sum whose size is controlled by classical
   bounds. State and prove the resulting theorem, and confirm against the
   measured histograms in `results/coeff.jsonl` (rows with large deviations).
2. **Sharp degenerate bounds.** Replace Markov by an argument using the
   quadratic term: when θ₂ is uniform on [0,1), near-periodicity of the
   sequence needs both θ₁ and θ₂ close to rationals with small denominators,
   which has measure O(s²/b² · s²/b²). When θ₂ is small (upper positions) the
   sequence is a rotation and the bound is O(s²/b²) from the three-gap
   theorem. Compare with the measured tail table.
3. **General exponent pair (e₁, e₂).** Lemma 1 for n^e with the binomial
   expansion; the number of "zones" is e; the analogue of the middle third
   for (e₁, e₂) is the set of positions of n^(e₂) reachable from neither end,
   which Haskin's articles presumably also locate. State it.
4. **Formal lower bound.** Define a model of "local certificate algorithms":
   the algorithm may query, for a batch defined by a residue class modulo b^k
   and a prefix interval (or an arithmetic progression), any function of the
   certified digits, and must be sound. Prove that in this model the number of
   full checks per expected solution is at least the 80%-ceiling figure of the
   algorithm report, using Theorem A to show certificates on middle positions
   have vanishing density. Be explicit that the model excludes algorithms that
   compute the digits (which is what the enumerator does), so the bound is
   about pruning, not computation.
5. **Optional.** Prove the exact digit-change probabilities at the two
   positions above a changed digit (Theorem C's excluded range) from the gcd
   structure; they are measured to two decimals.

## Deliverables

An extended version of the middle-digits report or a separate note with the
new theorems, their proofs, and the numerical confirmations.

## Stop rules

Bounded by interest: stop after step 2 if step 1's mixture theorem becomes a
case-analysis swamp; step 4 only if a clean model can be stated in a page.
