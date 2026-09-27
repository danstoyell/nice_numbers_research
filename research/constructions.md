# Construction hypotheses, obstructions, and bounded experiments

Started 2026-09-23. This is original working mathematics, not a claim of
priority. All numbers and representations use positive integer `n`, integer
base `b >= 2`, and ordinary representations with no leading-zero padding.

**Outcome so far:** no second nice number. Two exact obstructions below rule
out natural construction strategies. Neither is a uniqueness proof.

## 1. A carry-free construction cannot work

Write the ordinary digits of `n` as

`P(X) = a_0 + a_1 X + ... + a_k X^k`, with `a_k > 0` and `n = P(b)`.

Call the raw cube **carry-free** if every coefficient of `P(X)^3`, including
zero coefficients at absent powers, lies in `0,...,b-1`. There are then no
carries when these coefficients are interpreted as the base-`b` cube.

**Proposition. No nice number has a carry-free raw cube.**

Proof:

1. If `a_0 = 0`, both the square and cube end in zero. Thus a nice number
   must have `a_0 >= 1`.
2. Coefficient by coefficient, `P^3 >= a_0 P^2 >= P^2`, since all
   coefficients are nonnegative. A carry-free cube therefore implies a
   carry-free square.
3. If `k = 0`, both powers have one digit, so niceness would require
   `b = 2`. Its only positive one-digit `n` is `1`, whose powers repeat
   `1`. This also disposes of `n = 1` explicitly.
4. Suppose `k >= 1`. The power lengths are exactly `2k+1` and `3k+1`,
   so `b = 5k+2`.
5. Over the field of three elements, `P(X)^3 = sum a_i^3 X^(3i)`.
   Consequently each of the `2k` positions with exponent not divisible
   by three in `0,...,3k` has a cube digit divisible by three.
   There are only `floor((b-1)/3)+1 = ceil(b/3)` such digits in the
   entire base alphabet, including zero. Distinctness requires
   `2k <= ceil((5k+2)/3)`, hence `k <= 4` and `b <= 22`.
6. The cube's endpoint digits are `a_0^3` and `a_k^3`, both below
   `b <= 22`. Thus `a_0,a_k <= 2`. Either endpoint equal to `1` would
   repeat the digit `1` between the square and cube at that endpoint.
   Both must therefore equal `2`. The square then has digit `4` at
   both distinct endpoint positions, another repetition. Contradiction.

This blocks sparse polynomial constructions with small enough coefficients
to avoid carries, including attempts to design two coefficient lists that
jointly permute the alphabet. Carries are essential, not merely a nuisance
to remove.

### A quantitative residue condition on carries

For an arbitrary nice `n` of degree `k`, let `C_j` be the raw cube
coefficients, let `c_0=0` and `c_{j+1}=floor((C_j+c_j)/b)`, and let
`d_j=C_j+c_j-b*c_{j+1}` be its ordinary cube digits. For the `2k`
indices `j` in `0,...,3k` that are not multiples of three,

`d_j mod 3 = (c_j-b*c_{j+1}) mod 3`.

At least

`max(0, 2k-ceil(b/3))`

of these positions must have `c_j-b*c_{j+1}` nonzero modulo three;
otherwise the cube alone consumes too many distinct multiples of three.
The ordinary digit lengths give `5k+2 <= b <= 5k+5`, so the lower bound
grows approximately as `b/15`. This is a necessary constraint for a
solver or a deliberately designed carry pattern. It does not establish
that a solution exists.

## 2. Near powers and fixed-denominator fractions eventually repeat

Consider an integer candidate represented as

`n = (a*b^m + r)/d`, with integers `d >= 1`, `m >= 1`.

Assume `r^2 < b^m` and that `n^2` has at least `m` ordinary digits.
Let `h` be the number of base-`b` digits in `r^2`, with `h=0` if `r=0`.

**Proposition. If the square has no repeated digit, `m-h <= d^2`.**

Proof: Let `D=d^2` and `x = n^2 mod b^m`, written using exactly `m`
positions. These positions all belong to the ordinary representation of
`n^2` by the stated length assumption, even when the top digits of `x`
are zero. Squaring `d*n = a*b^m+r` shows

`D*x = r^2 + t*b^m`

for some integer `t`. In standard multiplication of `x` by `D`, each
carry is in `0,...,D-1`: this follows inductively from
`D*(b-1)+(D-1)=D*b-1`. Denote the carry entering position `i` by `c_i`
and the digit of `x` there by `x_i`. At each position
`h <= i <= m-1`, the product digit is zero, so

`D*x_i+c_i = b*c_{i+1}`.

Reading downwards gives

`x_i = floor(b*c_{i+1}/D)`, and `c_i = (b*c_{i+1}) mod D`.

Thus these `m-h` digits are drawn from a set of at most `D` possible
outputs, one for each carry state. More than `D` positions repeat a
digit. This proves the claim.

If `gcd(b,d)=1` and `d>1`, the downward carry sequence is periodic with
period dividing the multiplicative order `ord_(d^2)(b)`. The stronger
necessary bound is then

`m-h <= ord_(d^2)(b)`.

This explains why formulas near rational multiples of powers often make
highly repetitive squares. In the bounded experiment below,
`floor(a*b^m/d)+offset = (a*b^m+r)/d` has
`|r| <= (|offset|+1)*d`. For a fixed denominator and fixed offset bound,
`h` stays small while `m` grows with the base. Such a family cannot
produce infinitely many nice numbers. Denominators growing sufficiently
quickly with the base remain open; this argument does not eliminate them.

## 3. Other attempted templates and what they teach

- **Rebase the digits `69`.** The integer `6b+9` has two input digits
  for `b>=10`, so its square and cube have at most ten total digits.
  Therefore the direct rebase cannot give a new base above ten.
- **Stretch `69` to `6b^k+9`.** This introduces long gaps between raw
  product blocks. The bounded experiment tested the length-compatible
  exponent `k=floor((b-2)/5)` for every admissible tested base. No new
  solution. The near-power obstruction explains the eventual repeated
  digits without needing an unbounded search.
- **Small two-block expressions `a*b^k +/- c`.** Positive versions
  eventually have no carries; negative versions introduce long borrow
  runs. The fixed-denominator proposition with `d=1` gives the more
  general reason that sufficiently long gaps repeat square digits.
- **Repdigits and arithmetic-progressing digit strings.** These have
  controlled but substantial carries. All arithmetic progressions of
  the requisite input length were tested in each admissible base in
  the experiment. Constant progressions include repdigits. No new
  solution. This finite test is not a theorem excluding the family.
- **Small-denominator fractions near a power.** These deliberately
  allow carries and provide a broader template than sparse digit
  strings. They were tested with small positive and negative offsets.
  The second proposition gives an independent theoretical obstruction
  for fixed denominator as the base tends to infinity.

## 4. Reproducible finite experiments

Code: [scripts/constructions.py](../scripts/constructions.py).
All arithmetic uses Python integers. The script checks the known
`(69,10)` solution and the published base-45 near miss as regressions.
No probabilistic primality, floating-point interval bounds, or truncated
power representations are used.

For base `b`, `k=floor((b-2)/5)` is the required top exponent in `n`.
The search skips the rigorously impossible residues `b=1 mod 5` and
`b=3 mod 4`. Candidates are filtered by the necessary digit-sum
congruence `n^2*(n+1) = b*(b-1)/2 (mod b-1)`, then both complete power
representations are checked for exact length and uniqueness.

First run:

```sh
python3 scripts/constructions.py --max-base 300 \
  --coefficient-max 24 --denominator-max 64
```

Output: [results/constructions.json](../results/constructions.json).
This generated **1,468,106 family instances**, with repetitions across
families allowed in this count. Of these, **21,696** passed both the
modular condition and the exact total-length condition. Only `(69,10)`
was nice. The fractions include every reduced `a/d` with
`1<=a<d<=64`, and offsets `-2,-1,0,1,2`.

Larger run:

```sh
python3 scripts/constructions.py --max-base 1000 \
  --coefficient-max 48 --denominator-max 128 \
  --output results/constructions-b1000.json
```

Output: [results/constructions-b1000.json](../results/constructions-b1000.json).
This generated **19,252,100 family instances** in about 127 seconds;
**133,350** passed both the modular and length conditions. Again the
only nice pair was `(69,10)`. This is a superset of the first run, so
the two generated counts should not be added as unique coverage.

The JSON stores generation and survivor counts by family, every solution,
and the best digit diversity within each family and base. These results
cover the listed templates only; they do not exhaust any large base.

## 5. What remains worth pursuing

The two propositions suggest looking for complicated, nonperiodic carry
patterns, or formulas whose effective denominator grows with the base.
A solver could impose the cube carry-residue condition from Section 1
before enforcing all-different digits. Carry-free polynomial constructions,
fixed sparse near-power templates covered by Section 2, and bounded
denominators with bounded offsets have exact obstructions. Growing-length
strings drawn from a fixed small digit alphabet can create complicated
carries and are not ruled out by these propositions.
