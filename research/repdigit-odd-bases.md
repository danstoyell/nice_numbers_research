# A finite list of repdigit templates in sufficiently large odd bases

2026-09-26. This is a further necessary-condition reduction, not a
solution and not a complete repdigit exclusion. The arguments use the
carry-period bound from [constructions.md](constructions.md) and extend
the [even-base reduction](repdigit-composite-bases.md).

**Claim.** If a nice repdigit exists in an odd base `b>=1,000,000`,
then `b=5L` and its repeated digit is

`a=r*(b-1)-5`,

where

`r in {1/6, 1/2, 5/6, 1/8, 3/8, 5/8, 7/8}`.

The digit a must be an integer. Further congruence restrictions remain
necessary. The claim does not certify any member of these families,
and it leaves smaller odd bases unresolved by this argument.

## Carry period and common factors

Put `m=b-1` and `g=gcd(a²,m)`. The known base exclusion requires
`b=1 mod4`, hence `4|m`. As in the even-base proof,

`ord_((m/gcd(a,m))²)(b) = m/g`.

Indeed, put `D=m/gcd(a,m)`. Since `D|m`, the binomial theorem gives
`(1+m)^t=1+t*m mod D²`. The order is therefore
`D²/gcd(D²,m)=m/g`. No special assumption about the prime factors
of m is needed for this calculation.

Writing `m=5L-d`, `d in {1,2,3,4}`, the square period bound again
forces `g<=5` once `L>=12`. The value5 cannot occur because `5|m`
would give the impossible base class `b=1 mod5`. The value2 cannot
occur because `4|m` and an even a has `4|a²`. Thus

`g in {1,3,4}`.

## The odd-base digit-sum equation

Let `x=aL`, and `H=gcd(x²,m)`. The digit-sum condition is

`x²*(x+1) = m/2 mod m`.

It first requires `H | m/2`. Dividing through by H gives a congruence
modulo the even number `N=m/H`. The coefficient `x²/H` is coprime
to N, so its inverse is odd; multiplying `N/2` by any odd number
preserves that residue. Therefore

`x+1 = N/2 mod N`.

Multiplying by five and using `5L=m+d` now gives

`a*d+5 = (t+1/2)*m/H`

for an integer t. Since the left side is positive, `t>=0`.
Also `gcd(L,m)` divides d, whence

`H <= gcd(a²,m)*gcd(L²,m) <= g*d² <= 4d²`.

It follows that

`n/b^L >= (b-1-10H)/(2*H*d*b)`.

## Shorter power lengths are impossible at large bases

For `b>=1,000,000` the bound excludes d other than one:

- For `d=2`, use `H<=16`. The ratio exceeds `1/65`, since
  `(b-161)/(64b)>1/65`. As `b>=65³`, the cube has3L digits,
  contradicting the required3L-1.
- For `d=3`, use `H<=36`. The ratio exceeds `1/217`, since
  `(b-361)/(216b)>1/217`. As `b>=217²`, the square has2L
  digits, contradicting the required2L-1.
- For `d=4`, use `H<=64`. The ratio exceeds `1/1024`, since
  `(b-641)/(512b)>1/1024`. As `b²>=1024³`, the cube is at
  least `b^(3L-2)`, contradicting its required3L-2-digit length.

Thus `d=1`, `b=5L`, and `gcd(L,m)=1`, so `H=g`.
The equation reduces to

`a=((2t+1)/(2g))*m-5`, with `0<=t<=g-1`.

For `g=1,3,4` these are exactly the seven fractions in the claim
(the value1/2 appears twice before duplicates are removed).
Some listed fractions have additional divisibility requirements; keeping
them only enlarges the necessary family and does not assert sufficiency.

## Status

This is an algebraic working reduction awaiting a separate full audit.
Every repdigit in odd bases through 2000 has now been excluded in an exact
finite check. Of 999,000 possible repeated digits at the required root
length, 2,649 survive the base and digit-sum filters, and every survivor
has a repeated output digit. The separate even-base check already covers
the other bases through 2000. These finite searches do not close the gap
from 2001 to the theorem's threshold.

```sh
python3 scripts/repdigit_reduction_check.py --parity odd --max-base 2000 \
  --output results/repdigit-odd-finite.json
```

[Finite odd-base results](../results/repdigit-odd-finite.json).
No search of all odd bases up to the stated threshold has been performed.
The denominator-eight and denominator-six families may require constraints
deep inside the powers, as happened for the surviving even-base families.
