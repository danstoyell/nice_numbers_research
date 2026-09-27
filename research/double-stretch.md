# Double stretching: boundary obstructions and a surviving asymmetric family

Working branch continued after the September 25 transformations work.
The family is

`n=P(B^2)`, `P(X)=a_0+a_1 X+...+a_k X^k`,

where `B>=2`, `0<=a_i<B`, and `a_k>0`. Thus the ordinary base-`B`
input has zeros in every odd-indexed position. Powers are always
evaluated as integers, with no leading-zero padding.

**Results:** no nice number can have the mirrored boundary coefficients
`a_0=a_k` and `a_1=a_(k-1)` when `k>=2`. In particular, palindromic
coefficient polynomials are impossible. Equal endpoints alone impose
strong necessary conditions, but do not force the square to repeat a
digit: an explicit asymmetric counterexample to that stronger claim is
given below. Neither all double stretching nor the overall problem is
settled.

## 1. Exact length compatibility

The input's top exponent is `2k`, so

`B^(2k) <= n < B^(2k+1)`.

The square has `4k+1` or `4k+2` digits; the cube has `6k+1`, `6k+2`,
or `6k+3`. Consequently a nice candidate must have

`B in {10k+2, 10k+3, 10k+4, 10k+5}`.

This is necessary, not sufficient. It is important not to test arbitrary
bases while keeping `k` fixed. For example base 128 is incompatible with
double stretching, whereas base 512 is compatible with `k=51`.
The familiar exclusion `B=3 mod 4` still applies independently.

If `a_0=0`, both powers end in zero, immediately excluding the candidate.
The rest of the argument assumes `a_0>0`.

## 2. Square block carries, with explicit indices

Put `D=B^2` and write

`P(X)^2 = sum_(j=0)^(2k) Q_j X^j`.

Let `r_j` be the carry **entering** base-`D` block `j`, so `r_0=0`.
Define

`r_(j+1) = floor((Q_j+r_j)/D)`,

`R_j = Q_j+r_j-D*r_(j+1)`.

The block `R_j` comprises the two base-`B` digits at positions `2j`
and `2j+1`, except that the last block may have only one ordinary digit.

There are at most `k+1` summands in any `Q_j`. Inductively,

`0<=r_j<=k`,

because `(k+1)*(B-1)^2+k < (k+1)*B^2`. The end carries satisfy the
much stronger bounds

`r_1=0`, `r_(2k-1)<=2`, `r_(2k)<=1`, `r_(2k+1)=0`.

Here are the details, which avoid confusing an entering carry with an
outgoing one:

- `Q_0=a_0^2<B^2`, giving `r_1=0`.
- `Q_(2k-2)` has at most three summands, so
  `Q_(2k-2)+r_(2k-2)<=3*(B-1)^2+k<3B^2`, using `B>=10k+2`.
  This gives `r_(2k-1)<=2`.
- `Q_(2k-1)=2*a_(k-1)*a_k`, so its value plus the incoming carry
  is at most `2*(B-1)^2+2<2B^2`. Thus `r_(2k)<=1`.
- Finally `Q_(2k)=a_k^2`; adding at most one still gives a number
  below `B^2`, so `r_(2k+1)=0`.

The bounds remain valid for `k=1`; the third-from-last coefficient then
has fewer than three summands.

## 3. Equal endpoints already impose strong restrictions

Suppose `k>=1` and `a_0=a_k=a`. The last square block is
`a^2+r_(2k)`, whereas its first block is `a^2`.

If `r_(2k)=0`, at least one ordinary leading digit of the square repeats
at the units end. Thus niceness requires `r_(2k)=1`.

This in turn forces `a>B/2`. Otherwise

`2*a*a_(k-1)+r_(2k-1) <= B*(B-1)+2 < B^2`,

contradicting the carry being one. Here `B>=12`, from `k>=1` and
length compatibility. In particular `a^2>B`, so both endpoint square
blocks genuinely have two ordinary digits.

Increasing a two-digit number by one changes its higher digit only when
its lower digit is `B-1`. To avoid repeating that higher endpoint digit,
we therefore need

`a^2 = -1 (mod B)`.

The units digits of the two endpoint blocks are now exactly `B-1` and
`0`, respectively. Both are already consumed by the square.

There is a further length consequence. Since
`B^(2k+1)/2 < n < B^(2k+1)` and `B>=12`, the square and cube have
exactly `4k+2` and `6k+3` digits. Hence

`B=10k+5`.

The exclusion of bases `3 mod 4` then forces `k` to be even. Equivalently
`B=5 mod 20`. Since `B` is odd and `-1` must be a square modulo `B`,
every prime divisor of `B` must be `1 mod 4`. A prime `3 mod 4` is
forbidden regardless of its exponent in `B`.

These conditions are necessary only. In particular they leave bases
65, 85, 125, 145, and 185 available for an asymmetric experiment.

## 4. Mirrored neighboring coefficients force a repetition

**Proposition.** If `k>=2`, a double-stretched number with
`a_0=a_k` and `a_1=a_(k-1)` cannot be nice.

Proof: retain the necessary endpoint conclusions from Section 3,
especially that square digits `0` and `B-1` have already appeared.
The two next-inward raw coefficients are equal:

`Q_1=Q_(2k-1)=2*a_0*a_1`.

Their incoming carries are `r_1=0` and
`epsilon=r_(2k-1) in {0,1,2}`. Thus their two-digit blocks are the
last two base-`B` digits of `Q_1` and `Q_1+epsilon`.

If `epsilon=0`, the blocks repeat. If `epsilon` is one or two and
adding it does not carry out of the units digit, the blocks' higher
digits repeat. If it does carry, at least one of the units digits is
`0` or `B-1`:

- adding one crosses the boundary only from `B-1` to `0`;
- adding two crosses only from `B-2` to `0` or from `B-1` to `1`.

Each case repeats a digit already at an endpoint. Reduction modulo
`B^2` does not change this argument: it only makes the higher digit
cyclic, while the units carry criterion stays the same.

The blocks are at distinct positions because `k>=2`. Both are below
the leading block, so their two digits are ordinary digits even if
one of them is zero. This proves the proposition.

The middle coefficients are completely unrestricted. Full
palindromicity is stronger than necessary. For a palindromic degree-one
polynomial, Section 3 would force odd `k=1`, already excluded by the
base parity condition. Degree zero reduces to the ten one-digit
candidates in bases 2 through 5 checked in
[transformations-stretch-exceptions.json](../results/transformations-stretch-exceptions.json).
Thus every palindromic `P` is ruled out, but only within this
double-stretched family; this is not a theorem about arbitrary
palindromic integers in arbitrary bases.

## 5. Validation of the argument

Code: [scripts/double_stretch.py](../scripts/double_stretch.py).

```sh
python3 scripts/double_stretch.py --mode validate \
  --output results/double-stretch-validation.json
```

The run exhaustively checked all 328,810 mirrored-boundary coefficient
tuples of degrees 2, 3, and 4 in their four length-compatible bases.
Every square repeated a digit, including candidates whose complete
power length did not happen to equal the base. It also checked the
50 degree-one palindromic tuples in bases 12 through 15.

For 2,000 deterministic random cases with degrees from 2 through 100,
it separately formed the raw convolution, propagated the base-`B^2`
carries, checked all the bounds with the stated indices, and
reconstructed the exact integer square from its blocks. Every check
passed. These experiments validate the implementation and proof
indices; the argument in Section 4 supplies the unrestricted result.

Data: [results/double-stretch-validation.json](../results/double-stretch-validation.json).

## 6. An asymmetric escape: the square can have all distinct digits

To test whether the mirrored-neighbor assumption could be removed, the
next experiment deliberately chose equal endpoints satisfying all of
Section 3's conditions, but different neighbors. It sampled only the
five admissible bases above and forced the final square carry to one
by choosing

`a_(k-1) >= ceil(B^2/(2*a_0))`.

One interior coefficient was then chosen to enforce the exact
digit-sum congruence. Every evaluated candidate had total power length
equal to its base. This is an informed finite probe, not an exhaustive
search of the remaining family.

```sh
python3 scripts/double_stretch.py --mode probe --samples 20000 \
  --output results/double-stretch-asymmetric-probe.json
```

The deterministic seed is 20260925. Each base stops after finding five
distinct-square examples or reaching 20,000 attempted constructions.
Attempts with equal neighbors are discarded before evaluation.

| Base | Evaluated candidates | Distinct-square examples |
|---:|---:|---:|
| 65 | 1,426 | 5 |
| 85 | 4,666 | 5 |
| 125 | 19,864 | 0 |
| 145 | 19,869 | 0 |
| 185 | 19,886 | 0 |
| Total | 65,711 | 10 |

No candidate was nice. The absence of a distinct-square sample in the
last three rows is not an impossibility result.

A concrete counterexample to the stronger square-repetition claim is

`B=65`, `P` coefficients from units upward:
`[47,8,62,49,22,52,47]`,

`n=267406439245243092178847`.

Its square has 26 distinct digits, its cube has 39 digits, and the
digit-sum congruence holds. The endpoints agree, but the neighbors are
8 and 52. Its square digits from units upward are

`[64,33,37,11,42,25,9,21,2,38,7,44,46,29,63,13,35,45,6,41,28,8,14,10,0,34]`.

There are only 41 distinct digits across both powers, so this is not
a nice number. The independently maintained verifier confirms all
these claims:

```sh
python3 scripts/verify.py 267406439245243092178847 65
```

Full probe data:
[results/double-stretch-asymmetric-probe.json](../results/double-stretch-asymmetric-probe.json).
Independent verification:
[results/double-stretch-counterexample-verified.json](../results/double-stretch-counterexample-verified.json).

## 7. What remains open

An unrestricted double-stretched candidate still has `k+1` coefficient
digits, where `k` is about `B/10`. The exact digit-sum congruence removes
some combinations. The square's overlapping blocks retain carry
variables up to `k`; they are not in the carry-free class already
excluded elsewhere. The mirrored two-pair boundary obstruction removes
a specific symmetry, not arbitrary supports or arbitrary asymmetric
coefficients.

Even the equal-endpoint case survives when the neighbors differ, as the
explicit distinct-square example demonstrates. A global proof would
need a further restriction involving the cube or the entire digit
partition, rather than extending the local square-repetition claim
past this counterexample. Searching arbitrary coefficients blindly is
not justified by the small experiment: no second nice number was found.
