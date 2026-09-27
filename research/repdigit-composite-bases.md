# Two surviving repdigit templates in large even bases

2026-09-25; finite closure added 2026-09-26. This extends the reduction in [repdigits.md](repdigits.md).
It leaves two explicit families open, rather than proving that every
repdigit is impossible.

**Reduction.** If a nice repdigit `n=a*(b^L-1)/(b-1)` exists in an even
base `b>=2000`, it must belong to one of these families:

| Base restriction | Repeated root digit a | Root length |
|---|---|---|
| `b=70 mod 90` | `(b-1)/3-5` | `L=b/5` |
| `b=40 mod 90` | `2(b-1)/3-5` | `L=b/5` |

These are necessary templates, not solutions. An exhaustive repdigit
check through base 2000 now closes the smaller even-base range. Thus
**every possible nice repdigit in an even base must lie in one of these
two families above base 2000**. Odd bases are outside this result.

## A short period eliminates most common factors

Put `m=b-1`, `g0=gcd(a,m)`, `D=m/g0`, and `A=a/g0`. The root is
`(A*b^L-A)/D`. Here `m` is odd and `b=1+m`, and prime-power arithmetic
gives

`ord_(D²)(b) = m/gcd(a²,m)`.

Use order one when `D=1`. There is a direct elementary proof:
since `D|m`, the binomial theorem gives `(1+m)^t=1+t*m mod D²`.
Thus the order is `D²/gcd(D²,m)`, which equals the displayed expression
by comparing the exponent of each prime. The independent audit supplied
this simplification; it also works when m is even.

The square carry-period bound from [constructions.md](constructions.md)
therefore implies, with `g=gcd(a²,m)`,

`L-2 <= m/g`.

The subtraction of two allows for the at most two digits of `A²`.
Length compatibility says `m=5L-d`, `d in {1,2,3,4}`. Once `L>=12`,
any `g>=6` would give `m/g <= (5L-d)/6 < L-2`, a contradiction.
So `g<=5`. Since m is odd, and `5|m` would be the excluded base class
`b=1 mod 5`, the only possibilities are **g=1 or g=3**.

## The digit sum and length leave only thirds

Let `H=gcd(a²L²,m)`. The digit-sum condition implies
`m/H | aL+1`; multiplying by five yields

`a*d+5 = t*m/H` for a positive integer t.

If `d` is 1,2, or4, then `gcd(L,m)=1` because m is odd, and hence
`H=g<=3`. If `d=3`, the only possible common prime of L and m is3.
When its exponent in m is at least two, `v_3(L)=1`; when the exponent
is one, H contains at most one factor of3. Combining this with `g=1`
or3 shows `H<=9` in every case. Other primes cannot divide H.

Consequently

`n/b^L >= (b-1-5H)/(H*d*b)`.

For `b>=2000` this eliminates d other than one:

- If `d=2`, the lower bound exceeds `1/7`. Then the cube has3L
  digits, whereas length compatibility in this case requires3L-1.
- If `d=3`, it exceeds `1/28`. The square has2L digits, whereas
  this case requires2L-1.
- If `d=4`, it exceeds `1/13`, again forcing2L square digits
  instead of2L-1.

The numerical implications use `b>=7³`, `b>=28²`, and `b>=13²`,
respectively, all implied by2000. The fraction bounds themselves follow
from `(b-16)/(6b)>1/7`, `(b-46)/(27b)>1/28`, and
`(b-16)/(12b)>1/13` at these bases.

Thus `d=1`, `b=5L`, and `a=t*m/g-5` with `1<=t<=g`.
For `g=1`, this is `a=b-6`, already excluded by the repeated digit60
in [repdigits.md](repdigits.md). For `g=3`, the t=3 case is the same
excluded template and actually has g=1. The remaining values are
`a=m/3-5` and `a=2m/3-5`.

The condition `gcd(a²,m)=3` means `v_3(m)=1` and `3|a`.
For the first template this forces `m/3=2 mod3`, hence `b=7 mod9`.
For the second it forces `m/3=1 mod3`, hence `b=4 mod9`.
Combining these with even `b=0 mod5` gives the two progressions in
the table. This proves the reduction.

## Finite closure and an independent order check

```sh
python3 scripts/repdigit_reduction_check.py --max-base 2000 \
  --output results/repdigit-reduction-check.json
```

The even bases through 2000 have 1,000,000 potential repdigits at the
uniquely possible root length. After the exact base-length and digit-sum
filters, 4,638 remain. Every one has an explicitly detected repeated
digit in its square/cube pair. No candidate survives. This closes the
finite gap without extending the claim to unrestricted roots.

The script also independently computes the multiplicative order by
direct iteration for 22,500 `(a,b)` pairs in even bases through 300.
All agree with the order formula above. The finite search uses exact
integer arithmetic and stops only after finding a duplicate; it never
uses a floating-point power or a probabilistic rejection.

[Results and per-base counts](../results/repdigit-reduction-check.json).

## A fixed-edge attempt did not close the remaining families

At six large sample bases covering the three lifts modulo270 of each
progression, the first30 and last30 digits of both powers are all
mutually distinct. These120 edge digits therefore give no collision.
The middle of either power was not checked, and these are not claimed
to be nice numbers or close near misses.

The bases are `1080070,1080160,1080250` for the first template and
`1080040,1080130,1080220` for the second. The script uses exact modular
suffixes and rationally bounded prefixes, avoiding construction of
the enormous full roots. For depth K, the prefix comes from
`floor(b^K*(a/m)^e)` for `e=2,3`. The finite-root correction is less
than `3b^(K-L)`; at these lengths it is smaller than the minimum
nonzero fractional gap `1/m³`, so the floor is unchanged. The code
asserts that the fractional part is nonzero.

```sh
python3 scripts/repdigits.py --output results/repdigits.json
```

The `residual_edge_probe` section of [the results](../results/repdigits.json)
records each base, digit, length, and collision count. This is a precise
dead end for these six bounded edge checks, not a general limitation
theorem or a proof about the unchecked digits.
