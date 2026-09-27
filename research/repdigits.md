# Repdigits in bases one greater than an odd prime power

2026-09-25. A repdigit means `n=a R_L`, where
`R_L=(b^L-1)/(b-1)` and `1<=a<=b-1`. Its ordinary base-b root consists
of L copies of a. This note proves an infinite family exclusion. It
does not exclude arbitrary roots in these bases.

**Proposition. No repdigit is nice in any base `b=p^e+1`, where p is
an odd prime and `e>=1`.**

The small range is checked exhaustively below. The following argument
handles every `b>=125` in this class.

## Length and digit-sum reductions

Write `m=b-1=p^e`. The root length implies `5L-3<=b<=5L`, so put
`d=5L-m`, where `d` is one of 1,2,3,4. Also `L>=25`.
Because b is even, the digit-sum congruence is

`(aL)^2(aL+1) = 0 mod m`.

For a prime power, coprimality of consecutive integers gives two
branches: `aL=-1 mod m`, or `p^ceil(e/2)` divides `aL`.

First suppose `gcd(L,m)=1`. In the second branch let
`g=gcd(a,m)`, `A=a/g`, and `D=m/g`. Then

`n=(A*b^L-A)/D`, and `D²` divides m.

In the carry argument from [constructions.md](constructions.md), the
lowest L square digits, above the at most two digits of `A²`, follow
a downward carry recurrence modulo `D²`. Since `b=1 mod D²`, each
successive carry state is the same, and so are its output digits.
For `D=1` the single carry state gives the same conclusion. A distinct
square would require `L<=3`, contrary to `L>=25`.

In the other branch, multiply `aL=-1 mod m` by five. Since `5L=m+d`,

`a*d+5=t*m`, for an integer `1<=t<=d`.

The upper bound on t follows from `a<=m` and `m>5`. Consequently

`n/b^L = (a/m)(1-b^-L) >= (b-6)/(4b) > 1/5`.

Here we used `d<=4` and `1-b^-L >= 1-1/b`. For `b>=125`, the square
and cube therefore have their maximum possible lengths, `2L` and `3L`.
Niceness now forces `b=5L`, hence `d=1` and `a=b-6`.

## The surviving template repeats digit 60

For `b=5L>=125` and `a=b-6`, reduction modulo `b²` gives

`n = -5b-6 mod b²`, so `n² = 60b+36 mod b²`.

Thus the second square digit from the units end is 60.
The first two cube digits are `b-15,60`, as follows exactly.

Let `r0=1-5/m`. Then `n/b^L=r0(1-b^-L)` and

`b²*r0³ = (b-15)*b+60+R`,

`R = 10/m - 175/m² - 125/m³`.

For `m>=124`, `8/b<R<1`: indeed
`175/m+125/m²<2`, while `10/m<1`.
Replacing r0 with `n/b^L` decreases its cubed expression by less than
`3b^(2-L)<=3/b`. Thus the floor remains `(b-15)*b+60`.
This floor is precisely the first two digits of the cube, whose length
is `3L`. Digit 60 is repeated between the powers, a contradiction.

## The exceptional nonunit root length

If `gcd(L,m)>1`, then `p` divides `d`, since `5L=m+d`.
For odd p and `d` in 1..4 the only possibility is `p=3,d=3`.
As `m>=124`, we have `e>=5`, and

`L=3*(3^(e-1)+1)/5`, so `v_3(L)=1`.

The branch `aL=-1 mod m` is impossible. The zero-square branch gives
`v_3(a)>=ceil(e/2)-1`. With A and D defined as above this implies
`D² | 9m`.

Furthermore `(1+m)^9=1 mod 9m`. In the binomial expansion, the linear
term is `9m`, the quadratic term is `36m²`, and every higher term
contains `m³`, divisible by `9m`. Therefore the downward carry
sequence modulo `D²` has period dividing nine. Its output digits also
have period at most nine. Since `A²` has at most two digits, a square
with distinct digits would require `L<=11`, again impossible.

This closes both cases for every `b>=125` in the proposition.

## Finite closure and reproducibility

```sh
python3 scripts/repdigits.py --output results/repdigits.json
```

The script checks every repdigit with the potentially compatible root
length in **every** base 2 through 124, a superset of the remaining
prime-power-plus-one bases. Each length-valid candidate is checked
again by the independent verifier. It also checks the digit-60 identity
in every multiple-of-five base from 125 through 2000.

[Exact results](../results/repdigits.json) accompany the proof.
The proof is a self-contained working derivation, not a claim of priority.
Repdigits in other base classes remain outside this proposition; the
previous finite scan through base 1000 must not be read as a general
repdigit impossibility theorem.
