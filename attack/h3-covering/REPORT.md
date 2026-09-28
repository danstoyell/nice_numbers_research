# H3: pandigital splits cover every compatible residue pair

2026-09-28. Hypothesis H3 of [NEXT_HYPOTHESES.md](../NEXT_HYPOTHESES.md): for
lengths s + c = b with s, c ≥ b/3 and any modulus M ≤ b² coprime to b, the
residue pairs (X mod M, Y mod M) of pandigital splits (X the s-digit "square
word", Y the c-digit "cube word", both leading digits nonzero) are exactly the
pairs allowed by the digit-sum congruence,

    x + y ≡ T (mod gcd(M, b−1)),   T = b(b−1)/2.

## Verdict

**Confirmed wherever it could be computed, and proved for M = b+1 in every
base b ≥ 10.** No new necessary condition exists in this range: no congruence
modulo any M ≤ b² coprime to b (for b ≤ 18), modulo any divisor of b²−1 (for
b ≤ 24), or modulo b+1 (for every b ≥ 10) can exclude a candidate that the
digit-sum congruence admits.

- **Exhaustive check.** For every base 10 ≤ b ≤ 18 with the nice-number
  lengths (s, c), and every M coprime to b with 2 ≤ M ≤ b², the image equals
  the predicted set: <!-- EXH_SUMMARY -->0 failures in 1057 tested (b, M) pairs<!-- /EXH_SUMMARY -->.
  For 12 ≤ b ≤ 14 the equality persists up to the largest M tested
  (2–2.75 b²), and at b = 12 up to M = 1582 (11 b²). The only failures found
  anywhere are at b = 10 and b = 11, where the square word has just 4 digits,
  for some M > b² (first at M = b²+1), and at b = 12 for M = 1583 and 1717.
  Details in §2.
- **Theorem (M = b+1).** For all b ≥ 10 with the nice-number lengths, every
  pair (x, y) mod b+1 with x + y ≡ T (mod gcd(2, b−1)) is realized. Proof in
  §3: a direct construction, for b ≥ 17 (odd) and b ≥ 24 (even), plus the
  exhaustive computation below those bounds. The same construction gives the
  divisors of b²−1 with gcd(M, b−1) = 1.
- **Why it is true.** Once the digit *sets* of the two words are chosen, the
  two words are independent, and each word's residue is 2·(sum at even
  positions) − (sum of its digits) modulo b+1. Subset sums of prescribed size
  of an interval of integers fill an interval of e·o + 1 consecutive values,
  which exceeds b+1 as soon as the word has about 2√b digits. The critique's
  swap argument lacked exactly this covering step.
- **Prior work.** The general statement is Theorem 5 of Brian Haskin's
  machine-checked [nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean)
  (`sieve_complete`): for any modulus dividing b^j − 1 the sieve sees a digit
  list only through its j positional block totals, it is sound, and under an
  explicit no-gap hypothesis on the block sizes its image is the full coset,
  so no such modulus prunes more than casting out (b−1)s does. Since every M
  coprime to b divides some b^j − 1, that covers the hypothesis here; his
  witness `base_four_sieve_is_incomplete` is the same phenomenon as the
  short-word failures in §4. What this report adds is narrower: exhaustive
  tables for every M ≤ b² through base 18, and an elementary proof with an
  explicit threshold for M = b+1 (and the divisors of b²−1 with
  gcd(M, b−1) = 1) that does not go through the no-gap condition.
- **Bearing on the goal.** This closes the congruence route to a
  nonexistence proof more firmly than before, which was its stated purpose.
  It yields no search filter, no candidate, and nothing about existence.

## 1. Method

`cover.c` runs a dynamic programme over the s + c positions. Its state is the
set of digits used so far together with the set of reachable pairs
(X mod M, Y mod M), stored as an M×M bitset per used-set. Assigning digit d to
position i of X rotates the bitset along x by d·b^i mod M; a Y position rotates
along y. Leading positions skip d = 0. At the end the single full-set state is
compared with the predicted set. The image is always contained in the
predicted set (that is the digit-sum congruence); the program also counts any
pairs outside it as a sanity check (always 0).

For b = 10, (s, c) = (4, 6), the DP reproduces the earlier brute-force
enumeration in `critique/results/multiset-image-base10.json` exactly,
including the 202 missing pairs at M = 101.

`class_dp.py` handles moduli M | b²−1 for larger bases by a DP over the
digits 0..b−1 whose state is the four class counts (even and odd positions of
each word) and the reachable pairs; for M | b²−1 the weight of a position
depends only on its parity. For s, c ≥ 4 each class has at least two
positions, so digit 0 can always be placed at a non-leading position of its
class and the leading-digit condition needs no bookkeeping. It agrees with
`cover.c` on every common case.

Reproduce:

```sh
clang -O3 -march=native -o cover cover.c
./campaign.sh                       # about 45 minutes on one core
python3 class_dp.py --max-base 40 --max-base-sq 24
python3 summarize.py                # tables below
```

## 2. Results

<!-- TABLES -->
**Exhaustive DP (`cover.c`): all M coprime to b, nice-number lengths.** "Fail" means the image is a proper subset of the predicted set. Bases 11 and 16 have no nice-number interval; s = round(2b/5) is used there.

| b | (s, c) | M tested | Largest M | Failures with M < b² | Failures overall | Smallest failing M | Largest covering M |
|---:|---|---:|---:|---:|---:|---:|---:|
| 10 | (4, 6) | 399 | 999 | 0 of 39 | 200 | 101 | 927 |
| 11 | (4, 7) | 272 | 300 | 0 of 109 | 2 | 122 | 300 |
| 12 | (5, 7) | 132 | 397 | 0 of 47 | 0 | — | 397 |
| 13 | (5, 8) | 369 | 400 | 0 of 155 | 0 | — | 400 |
| 14 | (6, 8) | 170 | 397 | 0 of 83 | 0 | — | 397 |
| 15 | (6, 9) | 159 | 299 | 0 of 119 | 0 | — | 299 |
| 16 | (6, 10) | 127 | 255 | 0 of 127 | 0 | — | 255 |
| 17 | (7, 10) | 271 | 288 | 0 of 271 | 0 | — | 288 |
| 18 | (7, 11) | 107 | 323 | 0 of 107 | 0 | — | 323 |

Totals below b²: 0 failures in 1057 tested (b, M) pairs.

**Other word lengths and larger moduli** (b = 10 and 12; s from the hypothesis range and beyond):

| b | (s, c) | M tested | Largest M | Failures with M < b² | Failures overall | Smallest failing M | Largest covering M |
|---:|---|---:|---:|---:|---:|---:|---:|
| 10 | (2, 8) | 399 | 999 | 24 of 39 | 384 | 11 | 43 |
| 10 | (3, 7) | 399 | 999 | 2 of 39 | 319 | 89 | 281 |
| 10 | (5, 5) | 399 | 999 | 0 of 39 | 179 | 101 | 963 |
| 10 | (6, 4) | 399 | 999 | 0 of 39 | 200 | 101 | 927 |
| 10 | (7, 3) | 399 | 999 | 2 of 39 | 319 | 89 | 281 |
| 10 | (8, 2) | 399 | 999 | 24 of 39 | 384 | 11 | 43 |
| 12 | (3, 9) | 132 | 397 | 2 of 47 | 11 | 131 | 397 |
| 12 | (4, 8) | 132 | 397 | 0 of 47 | 1 | 145 | 397 |
| 12 | (5, 7) | 575 | 1727 | 0 of 47 | 2 | 1583 | 1727 |
| 12 | (6, 6) | 132 | 397 | 0 of 47 | 0 | — | 397 |
| 12 | (7, 5) | 132 | 397 | 0 of 47 | 0 | — | 397 |
| 12 | (8, 4) | 132 | 397 | 0 of 47 | 1 | 145 | 397 |
| 12 | (9, 3) | 132 | 397 | 2 of 47 | 11 | 131 | 397 |

**Class DP (`class_dp.py`)**: M = b+1 for b = 10–40 and M = b²−1 for b = 10–24: 0 failures. The sufficient condition of Theorem 1 holds for b in {17, 19, 21, 23, 24, 25, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40} (and, by the Corollary, for every larger b).
<!-- /TABLES -->

## 3. Theorem and proof

**Notation.** b ≥ 10; s + c = b with s, c ≥ 4; e = ⌈s/2⌉ and o = ⌊s/2⌋ are
the numbers of even and odd positions of X; e' = ⌈c/2⌉, o' = ⌊c/2⌋ likewise
for Y; T = b(b−1)/2. Since b ≡ −1 (mod b+1), a word with digit set S and
even-position digit set E satisfies

    X ≡ ΣE − Σ(S∖E) = 2ΣE − ΣS   (mod b+1).

**Lemma 1 (subset sums of an interval).** For 0 ≤ r ≤ m, the sums of the
r-element subsets of {u, u+1, …, u+m−1} are exactly the integers from
ru + r(r−1)/2 to ru + r(2m−r−1)/2, an interval of r(m−r) + 1 values.

*Proof.* The endpoints are the sums of the r smallest and the r largest
elements. Let R be an r-subset other than the top block. Let a be the largest
element of R with a + 1 ≤ u+m−1 and a + 1 ∉ R; it exists, since otherwise
every element of R below u+m−1 has its successor in R, which makes R the top
block. Replacing a by a+1 raises the sum by exactly 1. Iterating from the
bottom block reaches every value up to the top. ∎

**Lemma 2 (independence of the two words).** Fix disjoint digit sets S_X,
S_Y with |S_X| = s, |S_Y| = c and S_X ∪ S_Y = {0, …, b−1}. Every e-subset E of
S_X is the even-position digit set of some arrangement of X with nonzero
leading digit, and every e'-subset of S_Y likewise for Y, independently.

*Proof.* Place E at the even positions of X in any order and S_X∖E at the odd
positions. The leading position s−1 lies in one parity class, which has at
least ⌊s/2⌋ ≥ 2 positions; if 0 belongs to that class, put it at a
non-leading position. Same for Y. ∎

**Theorem 1.** Assume

- for even b: e·o ≥ b and e'·o' ≥ b;
- for odd b: e(o−1) ≥ (b−1)/2 and e'(o'−1) ≥ (b−1)/2.

Then for every pair (x, y) of residues modulo b+1 with
x + y ≡ T (mod gcd(b+1, b−1)) there is a pandigital split with X ≡ x and
Y ≡ y (mod b+1).

*Proof, even b.* Here gcd(b+1, b−1) = 1, so every pair must be realized, and
2 is invertible modulo b+1. Take S_X = {0, …, s−1} and S_Y = {s, …, b−1}. By
Lemma 1, as E runs over the e-subsets of S_X, ΣE runs over e·o + 1 ≥ b+1
consecutive integers, hence over a complete residue system modulo b+1, so
2ΣE − ΣS_X runs over every residue. The same holds for Y with e'·o' + 1 ≥ b+1.
By Lemma 2 the choices are independent. ∎

*Proof, odd b.* Now gcd(b+1, b−1) = 2, and X ≡ ΣS_X (mod 2) because X is
congruent to its digit sum modulo the even number b−1; likewise Y ≡ ΣS_Y, and
ΣS_X + ΣS_Y = T. So x + y ≡ T (mod 2) is necessary. For sufficiency, first
observe: if ΣE runs over an interval of at least (b+1)/2 consecutive
integers, then 2ΣE runs over every even residue modulo b+1 (2ΣE modulo b+1
depends only on ΣE modulo (b+1)/2), so X = 2ΣE − ΣS_X runs over every
residue of parity ΣS_X. Hence with S_X = {0, …, s−1}, S_Y = {s, …, b−1}
(Lemma 1 gives intervals of e·o + 1 and e'·o' + 1 values, both at least
(b+1)/2 under the hypothesis), every pair with x ≡ ΣS_X (mod 2) is realized.
For the pairs with x ≡ ΣS_X + 1 (mod 2) we change the parity of the digit
sums:

- *s odd.* S_X = {1, …, s} (the sum grows by s, which is odd) and
  S_Y = {0} ∪ {s+1, …, b−1}. For X, Lemma 1 applies to the interval {1, …, s}.
  For Y, restrict to e'-subsets that avoid 0: these are the e'-subsets of the
  interval {s+1, …, b−1} of c−1 elements, whose sums form an interval of
  e'(c−1−e') + 1 = e'(o'−1) + 1 ≥ (b+1)/2 values.
- *s even* (so c is odd). S_X = {0, …, s−2} ∪ {s} (the sum grows by 1) and
  S_Y = {s−1} ∪ {s+1, …, b−1}. For X, restrict to e-subsets avoiding s: the
  e-subsets of {0, …, s−2}, with e(s−1−e) + 1 = e(o−1) + 1 ≥ (b+1)/2 sums.
  For Y, restrict to e'-subsets avoiding s−1: e'(o'−1) + 1 ≥ (b+1)/2 sums.

In both cases X takes every residue of the required parity and Y likewise,
independently by Lemma 2. ∎

**Corollary (nice-number lengths).** Let (s, c) be the lengths of the
nice-number interval in base b, so that 3s ≥ 2c − 2, i.e. s ≥ (2b−2)/5, and
c ≥ s. Then the hypothesis of Theorem 1 holds for every even b ≥ 28 and every
odd b ≥ 21:

- even b: e·o ≥ (s²−1)/4 ≥ b follows from s ≥ √(4b+1), which (2b−2)/5 exceeds
  once 4b² − 108b − 21 ≥ 0, i.e. b ≥ 28;
- odd b: e(o−1) ≥ s(s−3)/4 ≥ (b−1)/2 follows from s² − 3s ≥ 2b − 2, which
  holds for s ≥ (2b−2)/5 once 2b − 2 ≥ 40, i.e. b ≥ 21;
- and e'·o' ≥ e·o, e'(o'−1) ≥ e(o−1) since c ≥ s.

The hypothesis also holds directly at b = 17, 19, 24, 25, 27 (checked in
`class_dp.py`, column `theorem_condition_holds`). Combined with the exhaustive
DP for 10 ≤ b ≤ 18 and the class DP for 10 ≤ b ≤ 40, **covering modulo b+1
holds for every base b ≥ 10.**

**Remark (divisors of b²−1).** For even b, b−1 and b+1 are coprime, and
X ≡ ΣE + b·Σ(S_X∖E) ≡ bΣS_X − (b−1)ΣE (mod b²−1). Modulo b−1 this is the
digit sum ΣS_X, and modulo b+1 it is 2ΣE − ΣS_X as before. So the
construction of Theorem 1 realizes every pair (x, y) modulo b²−1 with
x ≡ ΣS_X and y ≡ ΣS_Y (mod b−1); to reach *every* class x mod b−1 one must
also vary ΣS_X over all residues modulo b−1 while keeping the subset-sum
intervals long, which the interval sets above do not do (shifting an
interval of even length does not even change the parity of its sum). The
class DP settles M = b²−1 for b ≤ 24; a uniform proof would need digit sets
with prescribed sum and near-interval structure (for example an interval with
two displaced elements), which we did not pursue.

## 4. What the failures above b² look like

At b = 10, (s, c) = (4, 6), coverage fails first at M = 101 = b²+1, where
X ≡ (d₀ + 10d₁) − (d₂ + 10d₃) is an alternating sum of two 2-digit blocks of
a 4-digit word: 202 of the 10,201 pairs are unreachable. The failing moduli
below 3b² are only 101 and 297 = 3(b²−1) (one pair short). At b = 11,
(s, c) = (4, 7), the failures below 300 are M = 122 = b²+1 and 244. From
b = 12 on, no modulus up to the tested limit fails; in particular M = b²+1 is
covered for 12 ≤ b ≤ 15. So the b² threshold in the hypothesis is
conservative from b = 12 on, and the exceptions at b = 10, 11 come from the
4-digit square word, not from the modulus alone.

**Dependence on word length.** The hypothesis restricts to s, c ≥ b/3, and
the other-length runs show why. At b = 10 a 2-digit square word fails for 24
of the 39 moduli below b² (first at M = 11), a 3-digit word fails for two
(M = 89 and 91), and words of 4 digits or more fail for none. At b = 12 a
3-digit word fails at M = 131 and 133 (below b² = 144), a 4-digit word only
at M = 145 = b²+1, and the nice lengths (5, 7) fail for nothing below 1583,
more than 10 b². So the threshold s ≥ b/3 in the hypothesis is where the
short word stops being the bottleneck, and the b² bound on M is loose for the
actual nice-number lengths.

## 5. What this does and does not establish

- It **does** show that no congruence obstruction exists modulo b+1 in any
  base, modulo any divisor of b²−1 for b ≤ 24, and modulo any M ≤ b² coprime
  to b for b ≤ 18. Together with the edge theorems (moduli sharing factors
  with b see only trailing digits), a uniqueness proof cannot use residue
  information of this kind.
- It **does not** give a search filter: every candidate already passes.
- It **does not** say anything about whether the power curve (n², n³) meets
  a pandigital pair; that is the whole problem.
- The general statement (all M ≤ b², all b) remains a conjecture, now
  supported through b = 18 and with the mechanism identified.

## Files

- `cover.c`: exhaustive DP; `run_cover.sh`, `campaign.sh`: the runs;
  `results/cover_b*_s*.jsonl`: one JSON line per (b, s, M).
- `class_dp.py`: class-count DP for M | b²−1; `results/class_dp.json`.
- `summarize.py`: produces the tables in §2.
