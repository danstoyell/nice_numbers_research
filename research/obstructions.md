# Exact obstructions, and limits of local filters

September 23, 2026. This investigation concerns positive integers `n` for which
the ordinary, unpadded base-`b` digits of `n²` and `n³` together are exactly
`0,…,b−1`. It proves necessary conditions and one limitation theorem. It does
**not** prove that 69 in base 10 is unique or exhibit a second nice number.

## 1. Exact length intervals

Write `x=log_b(n)`. The required digit count is

`floor(2x)+floor(3x)+2=b`.

For each nonnegative integer `q`, its complete solution is:

| Base | Allowed real interval for n |
|---|---|
| `b=5q+2` | `[b^q, b^(q+1/3))` |
| `b=5q+3` | `[b^(q+1/3), b^(q+1/2))` |
| `b=5q+4` | `[b^(q+1/2), b^(q+2/3))` |
| `b=5q+5` | `[b^(q+2/3), b^(q+1))` |

Intersect each interval with the integers. Bases `b≡1 (mod 5)` are impossible.
This follows by splitting the fractional part of `x` at `1/3,1/2,2/3`.
Every permitted interval `[b^α,b^β)` has `α≥(b−2)/5` and `β−α≥1/6`.

## 2. Complete solution of the digit-sum congruence

Put `m=b−1`. Since `b≡1 (mod m)`, every nice number satisfies

`n²(n+1) ≡ b(b−1)/2 (mod m)`.

For **every odd prime power `p^e | m`**, the allowed classes modulo `p^e` are
exactly

* `n ≡ −1 (mod p^e)`; or
* `n ≡ 0 (mod p^ceil(e/2))`.

Proof: the right side is divisible by `p^e`, and `n` and `n+1` are coprime.
The number of these classes is `1+p^floor(e/2)`.

If `b` is even, these conditions completely solve the congruence. If `b` is
odd, write `t=v₂(b−1)`. The right side modulo `2^t` is `2^(t−1)`:

* `t=1`: no solution. This proves the known exclusion `b≡3 (mod 4)`.
* `t≥2`, `n` odd: exactly `n≡2^(t−1)−1 (mod 2^t)`.
* `t≥2`, `n` even: possible precisely when `t` is odd, and then exactly
  `v₂(n)=(t−1)/2`, giving `2^((t−1)/2)` classes modulo `2^t`.

For odd `n`, the valuation comes entirely from `n+1`; once that valuation is
`t−1`, multiplication by the odd square preserves the target residue. For
even `n`, the valuation is `2v₂(n)`, which proves the stated cases.

Thus the total root count is the product of the odd-prime factors above,
times `1 + [t odd]·2^((t−1)/2)` when `t≥2`, or zero when `t=1`.
**There are no further excluded bases obtainable from this congruence alone.**
For example, base 57 has six classes modulo 56, while base 54 has only two
classes modulo 53. A search can enumerate these classes directly with CRT.

## 3. Last-digit collisions and CRT independence

The last digits coincide exactly when `n²(n−1)≡0 (mod b)`. For every prime
power `p^e | b`, the solutions are `n≡1 (mod p^e)` or
`n≡0 (mod p^ceil(e/2))`. Consequently the number of colliding residue classes
modulo `b` is

`R(b) = product_(p^e || b) (1+p^floor(e/2))`.

Exactly `b−R(b)` classes have distinct last digits. Base 2 has none.
Every other base has some: each factor `1+p^floor(e/2)≤p^e`, with strict
inequality unless `p^e=2`.

More generally, the last `k` square digits and last `k` cube digits depend
only on `n mod b^k`. Because `gcd(b^k,b−1)=1`, their residue condition is
independent in the exact CRT sense of the digit-sum condition. If `S_k(b)`
residues survive the suffix test and `A(b)` survive the digit-sum condition,
there are exactly `S_k(b)·A(b)` combined classes modulo `b^k(b−1)`.

This does not assert independence of the remaining digits, and interval
boundaries can affect the number of representatives in a particular search.

## 4. A constructive limitation theorem for fixed-depth filters

**Theorem.** For every positive integer `k`, every sufficiently large base
`b` with `b≢1 (mod 5)` and `b≢3 (mod 4)` has integers of the correct length
that satisfy the digit-sum congruence and have all `2k` trailing square/cube
digits distinct. The explicit sufficient bound `b>64k⁵` works.

This does **not** say those integers are nice: almost all of their other
digits remain unchecked.

**Construction of a suffix.** Choose nonnegative-coefficient polynomials

`P(X)=a₀+a₁X+…+a_(k−1)X^(k−1)`, with `a₀=2`,

so the coefficients of degrees `0,…,k−1` in `P²` and `P³` are all distinct.
Start with the distinct constants 4 and 8. Having chosen through `a_(j−1)`,
the new coefficients at degree `j` have the form

`C_j=4a_j+c_j`, and `D_j=12a_j+d_j`.

Each can collide with one of the `2j` old coefficients at at most `2j`
values of `a_j`. The new coefficients can collide with each other at at most
one further value. Among `1,…,4j+2`, at least one choice therefore works.
The new choice does not change coefficients of lower degree. This proves
the induction and gives `a_j≤4j+2≤4k`.

Every low square coefficient is at most `16k³`. Every low cube coefficient
is at most `64k⁵`: there are at most `k²` ordered triples of indices summing
to a fixed degree below `k`, and each term is at most `(4k)³`.
For `b>64k⁵`, these coefficients are actual digits, without carries, so
`r=P(b) mod b^k` supplies the desired suffix residue.

**Digit sum and length.** Section 2 supplies a digit-sum residue `s mod b−1`.
CRT combines `n≡r (mod b^k)` and `n≡s (mod b−1)` into a class of period
`M=b^k(b−1)`. In the required length interval, the real interval width is
at least `b^((b−2)/5)(b^(1/6)−1)`. For `b≥64` and `b≥5k+12`, this is at
least `b^(k+2)>M`. Thus every such residue class has a representative in
the required interval. Both inequalities follow from `b>64k⁵`.

The bound is deliberately loose. The greedy construction implemented in
the script works at much smaller bases:

| Suffix depth k | Coefficients of P, low to high | All bases b above |
|---|---|---:|
| 2 | `2,3` | 36 |
| 3 | `2,3,1` | 66 |
| 5 | `2,3,1,1,1` | 81 |
| 10 | `2,3,1,1,1,2,1,2,1,2` | 250 |
| 20 | See JSON artifact | 849 |

For these sharper thresholds, apply the separate length bound too. An even
simpler depth-4 construction is `P(X)=2X+3`: the low coefficients of its
square are `9,12,4,0`, and of its cube are `27,54,36,8`, all distinct for
every `b>54`. Since the zero is one of the selected digits, this example
uses the normal padded *suffix* convention; the full candidate constructed
by CRT has enough digits in both powers.

**Consequence:** no argument that uses only the length, the standard
digit-sum congruence, and a fixed number of trailing digits can prove global
uniqueness. It must use information whose depth grows with the base, or
some genuinely different global property.

## 5. A restriction on completely carry-free constructions

**This route has been superseded by a complete obstruction proved in the
parallel construction investigation.** The proof in
[constructions.md](constructions.md#1-a-carry-free-construction-cannot-work)
shows that every nice number must have a carry in its raw cube. I independently
checked that argument: a carry-free cube implies a carry-free square; the
cube's Frobenius congruence forces degree at most four and base at most 22;
the leading and trailing input digits must then both be 2, repeating square
digit 4. The algebraic observation and finite experiment below are retained
as a record of a separate route explored before that stronger proof.

Suppose the full polynomials for `n²` and `n³`, obtained by replacing the
base by `X` in `n`'s digit expansion, have all coefficients below `b`.
Let `S` be the sum of `n`'s digits. Evaluating these polynomials at 1 gives
the **exact** equality

`S²(S+1)=b(b−1)/2`, equivalently `(2b−1)²=8S³+8S²+1`.

Also, if `n` has degree `d` as a polynomial in `b`, its square and cube have
`2d+1` and `3d+1` digits. Thus such a construction requires `b=5d+2`.
This is much stronger than the usual digit-sum congruence.

Exhaustive exact checking for `1≤S≤2,000,000` finds only `(S,b)=(3,9)` in
the displayed equation. Its base does not satisfy `b≡2 (mod 5)`, so it
cannot be a completely carry-free nice construction. This excludes that
construction strategy for the stated digit-sum range, **not** for all S.

The equation becomes the elliptic curve `y²=x³+2x²+1` after `x=2S`.
No completeness claim about those integral points is made here. Certifying
them is unnecessary for the carry-free obstruction because the preceding
Frobenius argument already settles that construction strategy.

## 6. Reproducible experiments and dead ends

Run from the project root:

```sh
python3 scripts/obstructions.py
```

The resulting `results/obstructions.json` contains:

* Exact brute-force verification of both root-count formulas for every
  base `2≤b≤2000`.
* Exhaustive enumeration of all residues modulo `b³` for `6≤b≤64`.
  **Every base has at least one suffix survivor.** Selected counts:
  `S₃(10)=126`, `S₃(54)=101239`, `S₃(57)=133645`, `S₃(64)=180003`.
  This is enumeration of local necessary conditions, not full candidates.
* Explicit carry-free *suffix* constructions for every depth from 1 to 20.
* The bounded exact check of the completely carry-free digit-sum equation.

Dead ends or limitations established:

1. Factoring `b−1` cannot strengthen the set of excluded base classes from
   the standard digit-sum congruence, although it improves search strides.
2. Combining that congruence with bounded suffix depth cannot yield a global
   nonexistence theorem, by the constructive proof above.
3. Modulo `b+1`, alternating digit sums depend on which digits occupy the
   negative-sign positions. For a fixed number `h` of such positions,
   possible subset sums fill the interval from `h(h−1)/2` to
   `h(2b−h−1)/2`; for large b this covers the needed residue classes. Thus
   the bare alternating-sum idea gives no immediate new base obstruction.
   Digit assignment restrictions could still make it useful in a search.
4. The bounded digit-sum scan alone could not settle completely carry-free
   constructions; the parallel Frobenius proof does. Neither argument
   excludes constructions with carries, which include the decimal example.

All mathematical derivations here are self-contained. They are not claims
of priority over existing nice-number literature.
