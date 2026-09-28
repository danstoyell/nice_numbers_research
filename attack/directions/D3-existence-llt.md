# D3. A first existence theorem in the family: fixed base, multiplicity k → ∞

## Goal

Prove a rigorous existence theorem for the nice-number family in the one
regime where the existence question reduces to a classical local limit
theorem: **fixed base b, multiplicity k → ∞**, for the exponent pair (1, 2)
first, and for (2, 3) conditionally on the open cube case.

Target statement (for (1, 2)): *for every admissible base b ≥ b₀ and every
sufficiently large k for which the band is non-empty, there is an n such that
n and n² together contain every base-b digit exactly k times.*

## Why it matters

No existence result of any kind is known in this family; Haskin's Theorem 10
makes infinitude conditional on `ModelPositive`, and the
[existence report](../p2-existence/REPORT.md) shows why `ModelPositive` for
nice numbers proper (b → ∞, k = 1) needs asymptotics with exponentially
small error that no known method gives. The obstruction there is the
precision: the event has probability e^(−b) in a b-dimensional problem.

In the fixed-base, growing-k regime the dimension is fixed (b − 1) and the
target event, "the digit-count vector equals (k, …, k)", is the *mode* of a
multinomial with probability about (2πk)^(−(b−1)/2) · b^((b−1)/2), which is
polynomial in k. The count of candidates is b^(kb/3) up to the band. So a
local limit theorem with any power saving in k suffices, and the
exponentially-small-error obstacle disappears. What remains is a
b-dimensional local limit theorem for the joint digit-count vector of
(n, n²) over n in an interval, which is the kind of statement the
Mauduit–Rivat method was built for.

## What is known

- Mauduit–Rivat, *La somme des chiffres des carrés* (Acta Math. 2009):
  the sum of digits of n² is equidistributed in residue classes; the method
  (Fourier analysis of strongly q-multiplicative functions, van der Corput,
  carry-propagation lemmas) is the template.
- Drmota–Mauduit–Rivat, *The sum-of-digits function of polynomial sequences*
  (JLMS 2011): equidistribution and a central limit theorem for s_q(P(n)) for
  q ≥ q₀(d); their Problem 2 states that the **local** distribution for
  degree ≥ 3 is open because the estimates are not uniform in the frequency.
  The agent must determine exactly what local statement is proved for
  degree 2 and for which q.
- Drmota–Mauduit–Rivat, *Normality along squares* (JEMS 2019): the
  Thue–Morse sequence along squares is normal, i.e. **block** statistics of a
  digital function along squares are controlled. This is the closest result
  to what is needed: a digit-count vector is a vector of b digital functions
  with arbitrary unit-modulus weights per digit value.
- Bassily–Kátai (1995): central limit theorem for digit sums of polynomial
  values; Drmota–Morgenbesser (2012) for generalized Thue–Morse sequences of
  squares; Spiegelhofer (2023) for Thue–Morse along cubes mod 2, which does
  not give the local statement.
- The digit-sum congruence and the last-digit clash also apply at
  multiplicity k (Haskin's theorems are for general pairs; the target
  residue becomes k·b(b−1)/2). The band for (1, 2) at multiplicity k is
  s + c = kb with c ∈ {2s−1, 2s}; bases b ≡ 1 (mod 3) never have a band and
  bases b ≡ 3 (mod 4) fail the digit sum, so "admissible" means neither.

## Plan

1. **Survey precisely** (one session): for squares, which of these are
   proved and with what uniformity: the local limit theorem for s_q(n²); a
   joint local limit theorem for the vector of digit counts of n²; the
   corresponding statements over an interval [x, x + y] with y ≍ x. Quote
   theorem numbers. Identify the "Fourier property" input and whether it is
   stated for general weights e(θ_d) or only linear ones e(αd).
2. **Reduction.** Write the count of k-(1,2)-nice n in the band as the
   Fourier integral over T^(b−1) × T^(b−1) of
   Σ_n f_θ(n) · g_φ(n²), where f_θ, g_φ are strongly b-multiplicative with
   weights e(θ_d), e(φ_d). The factor in n is elementary (its Fourier
   coefficients are explicit products); the factor in n² is the
   Mauduit–Rivat object. State the needed estimate: |Σ_n f_θ(n) g_φ(n²)| ≪
   N^(1−η) uniformly for (θ, φ) outside a neighbourhood of the trivial
   characters (the digit-sum spikes at θ, φ linear in d, which are handled
   exactly by the congruence), with η fixed as k → ∞ in a fixed base.
3. **Prove or reduce.** Either carry out the estimate by adapting the
   Mauduit–Rivat proof (the digit weights enter only through the "Fourier
   property" of the digital function, which for fixed b and weights bounded
   away from the trivial characters should give a uniform power saving), or
   isolate the exact lemma that is missing and state it as a conjecture with
   evidence.
4. **State the (2, 3) analogue** as conditional on the cube version of the
   same estimate, and explain the relation to DMR's Problem 2.
5. **Check numerically** that the count grows as predicted: k-(1,2)-nice
   counts for b = 6, 8, 9 at k = 2, 3, 4 (bands of 10²–10⁷ roots) against
   the multinomial-mode prediction.

## Deliverables

A note in `research/` (or a paper draft) with the theorem and proof, or a
precise reduction to a stated lemma with the literature that supports it and
the numerical check.

## Stop rules

- If the survey shows a joint local limit theorem for squares' digit counts
  is available (or follows by a routine extension), continue to the theorem.
- If the extension needs a genuinely new estimate beyond the Fourier
  property (for example uniformity the method cannot give), stop after
  writing the reduction; that is still a useful map of the gap.

## Pitfalls

- Do not confuse this regime with the real problem: it says nothing about
  k = 1 or about b → ∞. Say so plainly in the note.
- Bands: at multiplicity k the length condition changes; make sure the
  interval is [b^(s−1), b^s) intersected with the square-length condition.
- The digit-sum congruence is an *exact* constraint that concentrates all
  the mass on a fraction 1/(b−1) of residues; the Fourier integral must
  treat those characters exactly, not as error terms.
