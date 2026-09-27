# A repeated cube digit excludes the five-sixths repdigit family

2026-09-26. This closes one of the seven odd-base templates in
[repdigit-odd-bases.md](repdigit-odd-bases.md), above its stated threshold.
It is a working proof with an exact six-case rational certificate.

**Proposition.** For `b>=1,000,000`, `b=25 mod180`, put

`L=b/5`, `a=5*(b-1)/6-5`, `n=a*(b^L-1)/(b-1)`.

The cube of n has a repeated digit: position7 counted from the units
digit equals position10 counted from the leading digit (indices start
at zero). Thus this family cannot be nice.

The base progression is the necessary one for the fraction5/6 in the
odd-base reduction. There `gcd(a²,b-1)=3`. Writing `b-1=6u`, the
condition `3|a=5(u-1)` gives `u=1 mod3`, hence `b=7 mod18`.
The existing parity condition gives `b=1 mod4`, so `b=25 mod36`.
Finally `b=5L` gives `b=25 mod180`.

## Exact coefficients at the two ends

Put `r=5/6`, `m=b-1`. For the first11 cube digits we may use the
rational quantity `(r-5/m)^3`. In powers of `z=1/b`, its constant
coefficient is `r³`; its coefficient at positive degree j is

`U_j = (125/12)*(-6j²+24j-19)`.

For the last8 digits, `n=-r+5/(b-1) mod b^8`, with denominators
interpreted by modular inversion. This is valid because b is coprime
to6 and `L>=8`. The formal expansion of its cube in powers of b has
coefficients

`V_0=-(35/6)^3`,

`V_j=-(125/12)*(6j²+24j+19)` for `j>=1`.

In particular **`U_(j+4)=V_j` for every `j>=1`**. We must still
account for carries and fractional parts: matching raw coefficients
alone would not prove matching digits.

## The six exact digit formulas

The base progression leaves six possibilities modulo216. Carry
propagation using the coefficients above gives this table; its second
column is both the cube digit at units index7 and the cube digit at
leading index10:

| b modulo216 | Common digit |
|---:|---|
|25|`(173b-1082381)/216`|
|61|`(29b-1082417)/216`|
|97|`(101b-1082453)/216`|
|133|`(173b-1082273)/216`|
|169|`(29b-1082309)/216`|
|205|`(101b-1082345)/216`|

These expressions are integers in `0,...,b-1` throughout the stated
range. The following recurrences specify a short, reproducible exact
certificate for the table rather than relying on numerical fitting.

For the low digits, start with rational carry `C_0=0`. At step j write
`V_j+C_j=q/D` in lowest terms. Choose `k=0,...,D-1` satisfying
`q+k*b=0 modD`; if k is zero and q negative, replace k by D.
The digit is `(k/D)b+q/D`, and `C_(j+1)=-k/D`.
All denominators divide216, so the chosen k depends only on the row
of the table. The certificate checks digit range for every stage0..7.

For the high digits start with `gamma_0=r³`. At step j let f be the
fractional part of `b*gamma_j+U_(j+1)`. Set `gamma_(j+1)=f`, except
that if f is zero and the following nonzero coefficient is negative,
use1. The digit is then

`gamma_j*b+U_(j+1)-gamma_(j+1)`.

Again the fractions depend only on b modulo216. The remainder bounds
below justify the flooring step, including the case f=0. Rational
arithmetic in the script verifies equality of the two affine digit
formulas in all six rows, with no rounding.

## Why the omitted terms cannot change a digit

At any high-digit stage j=0,...,10, the first omitted coefficient is
`U_(j+2)`. For k=2,...,12 and h>=1, the explicit quadratic formula gives

`|U_(k+h)| <= 1200*(h+1)^2*|U_k|`.

At `b>=1,000,000`, summing this geometric tail shows that terms after
the first omitted one have magnitude less than that first term.
Indeed `sum_(h>=1)1200*(h+1)^2/b^h < 0.006`.
The total omitted remainder therefore has the sign of `U_(j+2)` and
magnitude less than `2*|U_(j+2)|/b`.

For every nonzero f in the six-case recurrence, exact arithmetic gives

`|U_(j+2)| / min(f,1-f) <= 130050`.

Thus the omitted remainder is strictly smaller than the distance to
either integer boundary. For f=0, its known sign determines the
one-unit correction already used in the recurrence. This validates
every high-digit step for the entire infinite base range.

Finally the actual normalized root is
`n/b^L=(a/m)*(1-b^-L)`. Replacing `a/m` with this value changes the
scaled11-digit cube prefix by less than `3b^(11-L)`. The rational
prefix `b^11*a³/m³` is nonintegral: its reduced denominator is a
nontrivial divisor of `m³`, coprime to b. Its distance above the lower
integer boundary is at least `1/m³`, much larger than the correction
because `L>=15`. Therefore the finite root has the same prefix.

Its cube has3L digits, and the two selected positions are distinct.
Their equality proves the proposition.

## Reproduction and scope

```sh
python3 scripts/repdigit_five_sixths.py
```

[The certificate](../results/repdigit-five-sixths.json) records all six
affine formulas, the exact margin bound, and numerical checks at every
base in the progression between1,000,000 and1,100,000.
The proof leaves the other six odd-base fractions open. It does not
exclude arbitrary roots or all repeated-digit numbers in odd bases.
