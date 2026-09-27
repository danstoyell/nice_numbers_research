# Independent audit of the repdigit reductions

2026-09-26. Audited the root agent's
[prime-power note](repdigits.md), its finite-check script, and the
subsequent arbitrary-even-base reduction. No mathematical error was found
in the stated propositions. This is an independent derivation check,
not a claim of external peer review or mathematical priority.

## Prime-power-plus-one bases

Let `n=a*(b^L-1)/(b-1)`, `m=b-1=p^e`, and `1<=a<=m`.
For the large-base argument, `b>=125`, the length condition gives
`m=5L-d`, `1<=d<=4`, and `L>=25`. Since the base is even, the
necessary digit-sum congruence is `(aL)^2*(aL+1)=0 mod m`.

The split into `aL=-1 mod m` and `p^ceil(e/2)|aL` is exact: consecutive
integers are coprime, so the full prime power must occur in the square
factor or the successor factor.

For `gcd(L,m)=1` in the second branch, write
`g=gcd(a,m)`, `D=m/g`, `A=a/g`. Then `D^2|m`, and
`n=(A*b^L-A)/D`. The earlier rational carry lemma applies without a
hidden length or padding assumption: `A<=D<=m<b`, so `A^2<b^2<b^L`;
and the square of an `L`-digit input has at least `L` ordinary digits.
The downward carry sequence modulo `D^2` is fixed because
`b=1 mod D^2`. Above the at most two digits of `A^2`, at most one
distinct digit is possible. Thus `L<=3`, a contradiction. `D=1` is
covered by its single carry state.

In the successor branch, `ad+5=tm` with `1<=t<=d` follows from
positivity and `ad+5<=dm+5<(d+1)m`. Consequently
`n/b^L >= (b-6)/(4b)>1/5`. At `b>=125`, this forces square length
`2L` and cube length `3L`, including the endpoint `b=125` because
the inequality is strict. Hence `b=5L`, `d=1`, `a=b-6`.

I independently expanded the cube-prefix expression and obtained

`b^2*(1-5/m)^3 = (b-15)*b+60 + 10/m-175/m^2-125/m^3`.

For `m>=124`, the remainder is strictly between `8/b` and 1. The
finite repunit factor changes this expression by less than
`3*b^(2-L)<=3/b`, which cannot cross an integer boundary. The claimed
leading cube digits and trailing square digit 60 are therefore exact,
not an asymptotic approximation.

In the nonunit-length case, `p|L` implies `p|d`, so necessarily
`p=3,d=3`. The claimed valuation `v_3(L)=1` is correct and gives
`D^2|9m`. The binomial proof of `b^9=1 mod 9m` is valid, yielding
period at most nine and the contradiction `L<=11`.

An optional stronger bound is available: integrality of
`L=(3^e+3)/5` forces `e=3 mod 4`, so `e` is odd. The same valuation
estimate then gives `D^2|3m`, and `b^3=1 mod 3m`. The period is at
most three and `L<=5`. This strengthening is unnecessary for the proof.

The finite script correctly includes every potentially length-compatible
repdigit in bases 2 through 124. Bases `1 mod 5` have no valid input
length; the script harmlessly generates one length and rejects it by
the exact output-length test. The saved totals are 7,626 generated
roots, 1,494 length-valid roots, and 376 checks of the digit-60 identity.

## Arbitrary even bases: audit of the two-family reduction

For any repdigit, put `g0=gcd(a,m)`, `D=m/g0`. Since `D|m`,
`(1+m)^t=1+t*m mod D^2`. Therefore

`ord_(D^2)(b) = D^2/gcd(D^2,m) = m/gcd(a^2,m)`.

The `D=1` case again means period one. Applying the carry lemma gives
`L-2<=m/g`, where `g=gcd(a^2,m)`. For `b>=2000` and `m=5L-d`,
this bounds `g<6`. Since `m` is odd and `5` does not divide `m`,
`g` is either 1 or 3.

Set `H=gcd(a^2 L^2,m)`. For `d=1,2,4`, `gcd(L,m)=1`, hence
`H=g<=3`. For `d=3`, only the prime 3 can divide `gcd(L,m)`.
If `v_3(L)>=2`, then `v_3(m)=1`; if `v_3(L)=1`, then its square
adds at most two powers of 3. Also `g=3` already forces `v_3(m)=1`.
These cases establish `H<=9`.

The digit-sum condition implies `(m/H)|(aL+1)` and therefore
`(m/H)|(ad+5)`. This yields the lower bound

`n/b^L >= (b-1-5H)/(H*d*b)`.

For `d=2,3,4`, this is respectively greater than `1/7`, `1/28`,
and `1/13` at `b>=2000`. The length class `d=2` requires a cube
shorter than `3L` digits; `d=3,4` require a square shorter than
`2L` digits. These conditions contradict the lower bounds because
`b>7^3`, `b>28^2`, and `b>13^2`, respectively.

Thus `d=1`, `b=5L`, and `a=t*m/g-5`, with `1<=t<=g`.
The `g=1` case is the established digit-60 template. For `g=3`,
`t=3` reduces to that same template and actually has `g=1`.
The two remaining possibilities are

- `a=m/3-5`, requiring `b=70 mod 90`;
- `a=2m/3-5`, requiring `b=40 mod 90`.

To check the residue classes, write `m=3q` with `3` not dividing `q`.
The condition `3|a` gives `q=2 mod 3` for the first formula and
`q=1 mod 3` for the second. Combining with `b=0 mod 10` produces
the two stated classes. Other prime factors of `m` cannot divide `a`
because `a=-5 mod q` and `5` does not divide `m`.

This reduction is valid but does not itself exclude the two residual
families. Finite or shallow-edge experiments must not be presented as
their proof of impossibility.
