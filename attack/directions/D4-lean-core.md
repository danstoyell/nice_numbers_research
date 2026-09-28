# D4. Machine-checked core: the digit formula, the b+1 covering theorem, the wall

## Goal

Turn the three elementary results of September 28 into Lean 4 theorems in
the style of Haskin's [nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean)
(Lean core only, no Mathlib, no `sorry`), and offer them there or keep them
in this repository.

## Why it matters

The proofs in this repository are informal. Haskin's repository shows that
the elementary parts of the subject formalize quickly and that formalization
finds errors (his notes record several places where the informal argument
needed a different route). The two results below are the load-bearing ones
for the middle-digit theory and for the congruence question; a kernel-checked
version makes them safe to build on and easy to hand to others.

## Targets, in order of ease

1. **The batch digit formula (Lemma 1 of [middle-digits](../middle-digits/REPORT.md)).**
   For n = c + b^k·m, every position P ≥ k, and any exponent e ∈ {2, 3}:
   digit_P(n^e) is determined by the residues c^e mod b^(P+1),
   e·c^(e−1) mod b^(P+1−k), … as stated; concretely, the statement that
   (c + b^k m)³ ≡ c³ + 3c²b^k m + 3c b^(2k) m² + b^(3k) m³ and that the digit
   at P depends only on these terms modulo b^(P+1). Pure `Nat` algebra with
   `Nat.digits`-style definitions as in Haskin's file. Include the corollary
   that digits below k are constant along the batch and that positions in
   [k, 2k) depend on m only through (3c² mod b^(P+1−k))·m.
2. **Subset sums of an interval** (Lemma 1 of [h3-covering](../h3-covering/REPORT.md)):
   the sums of r-element subsets of {u, …, u+m−1} are exactly the integers
   from ru + r(r−1)/2 to ru + r(2m−r−1)/2. Induction on the "raise the
   largest raisable element" step.
3. **The b+1 covering theorem** (Theorem 1 and Corollary there): for the
   nice-number lengths and every b ≥ 10, every pair (x, y) mod b+1 with
   x + y ≡ b(b−1)/2 (mod gcd(2, b−1)) is realized by a pandigital split with
   nonzero leading digits. The construction is explicit (interval digit sets,
   a parity swap for odd b); the small bases 10–23 that the inequality does
   not cover need either `decide`-style finite checks with witnesses or the
   class-count DP transcribed as a certificate. Haskin's Theorem 5 gives the
   general statement under a no-gap hypothesis; this would be the
   unconditional b+1 instance.
4. **The middle-third wall as a theorem with witnesses** (optional, harder):
   for every b ≥ 3, L, position P with L ≤ P < 2L, and prefix/suffix lengths
   t + k ≤ L − 1, there exist two roots with the same top t and bottom k
   digits whose cubes differ at position P. A constructive proof needs an
   explicit choice; the batch formula gives the digit at P as a polynomial
   sequence in the free block, so it suffices to exhibit m₁, m₂ with different
   digits for a suitable c. Expect this to need a small case analysis or a
   finite search for the witness c per (b, L); decide whether a uniform
   construction exists before committing.

## Plan

- Read `NiceNumbers.lean` and `NOTES.md` in Haskin's repository first and
  reuse his digit definitions and conventions, so that a pull request is
  possible.
- Formalize 1 and 2 (an afternoon each by his experience with comparable
  statements), then 3.
- Mutation-test as he does: perturb a hypothesis and confirm the proof
  breaks.
- Coordinate through issue #1 of his repository before opening a pull
  request; otherwise keep the file under `research/lean/` here.

## Deliverables

A Lean file that compiles under his toolchain (v4.33.0 at the time of
writing), a short note listing the statements, and either a pull request or
a link in PROGRESS.md.

## Stop rules

Bounded work; stop only when the file compiles or when a target proves
unexpectedly heavy (report which and why). Do not attempt the Weyl-sum
theorems in Lean core; they need analytic machinery Mathlib does not have in
usable form.
