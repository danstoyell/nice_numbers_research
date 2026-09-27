# Transformations, dense digit alphabets, and growing denominators

Started 2026-09-24; extended and independently checked 2026-09-25.
These are working derivations and bounded exact experiments.
No new nice number or global uniqueness proof was obtained. The script is
[scripts/transformations.py](../scripts/transformations.py).

## Exact obstructions to simple transformations

**A fixed positive integer has at most one length-compatible integer base.**
For fixed `n`, each of `L_b(n^2)` and `L_b(n^3)` is nonincreasing as the
integer base `b` increases. Thus `L_b(n^2)+L_b(n^3)-b` is strictly
decreasing. It can equal zero at most once. In particular, a near miss
whose two powers already have exactly `b` digits cannot become nice by
merely reinterpreting the same integer in a different integer base.

**Simultaneously powering number and base does not lift niceness.**
The map `(n,b) -> (n^t,b^t)`, for integer `t>1`, preserves the lengths
of both powers: the logarithms determining the lengths are unchanged.
The alphabet, however, grows from `b` to `b^t` digits. Hence a nice
pair cannot yield another nice pair by this map. Grouping or splitting
the digits of the same integer is already excluded by the preceding
monotonicity argument. Multiplication of `n` by a positive power of its
base is also impossible: both new powers end in zero.

**A quasi-nice seed cannot simply be raised to a power in its own base.**
Here quasi-nice means that `q` and `q^2` jointly contain all base digits.
For a nontrivial such seed, `L_b(q^3)>L_b(q)`. Indeed, equality would
force `q<b` and `q^3<b`; all three numbers would then have one digit,
forcing the quasi-nice base to be two, whose only positive one-digit
candidate is `q=1` and repeats `1`. Therefore `q^2,q^3` already have
more than `b` digits. Replacing `q` by any positive integer power can
only increase the total length. A different base or a more complicated
arithmetic change would be essential.

There is also no direct matching of quasi-nice exponents to square/cube
exponents by a common exponent multiplier: `2t=1` and `3t=2` are
inconsistent. This rejects a particular proposed identity, not all
possible uses of quasi-nice seeds.

## Quasi-nice seed experiment

The script exhaustively generated quasi-nice seeds through base 14.
It used the exact input-length possibilities and digit-sum condition,
with no leading-zero padding. The three seeds were:

| Seed `q` (decimal) | Base |
|---:|---:|
| 20 | 6 |
| 174 | 8 |
| 500 | 9 |

For these seeds it tried offsets `-16..16`, powers `1..6`, expressions
`q^2+a*q+c` with `a=-2..2`, `c=-1,0,1`, digit reversal, and digit
complement in the seed's original base. Each transformed positive
integer was tested in its unique possible nice base, if one existed.
There were 168 transformation instances, including duplicates; 148
had a length-compatible base. None was nice. This is a small finite
experiment, not evidence that arbitrary quasi-nice transformations fail.

```sh
python3 scripts/transformations.py --mode quasi \
  --output results/transformations-quasi.json
```

Data: [results/transformations-quasi.json](../results/transformations-quasi.json).

## Dense small-alphabet digit strings with actual carries

The earlier carry-free theorem does not rule out long strings whose
input digits come from a small alphabet. Their convolution coefficients
can become large and carry repeatedly. This experiment directly handles
those carries.

For each admissible base up to 300, the script considers the required
input length `floor((b-2)/5)+1`. It searches digit strings from `{2,3}`
and `{1,2,3,4}`. A prefix here is built from the units end: choosing its
next input digit determines the next square and cube digits exactly.
Raw convolution plus the entering carries produces those two digits.
A repeated digit prunes the branch immediately. The input digit sum,
including attainable sums for the unchosen suffix, supplies another
exact congruence filter. Completed strings are independently evaluated
as whole integers and both ordinary power representations are checked.

```sh
python3 scripts/transformations.py --max-base 300 --seconds 120 \
  --node-limit 250000 --output results/transformations-dense.jsonl
```

The run finished in about 53 seconds:

| Quantity | Result |
|---|---:|
| Base/alphabet cases considered | 357 |
| Visited surviving-prefix nodes | 8,385,519 |
| Cases completely exhausted | 325 |
| Cases stopped at their node limit | 32 |
| Cases stopped at the global time limit | 0 |
| Solutions | 0 |

Of the 325 completed cases, 250 were excluded by the full input-length
interval and 41 by the input digit-sum congruence. These are legitimate
complete exclusions of the specified alphabet, not searches of all
integers in those bases. All admissible `{2,3}` cases through base 176
were exhausted. Its nine unfinished larger bases are
`177,197,217,232,237,257,262,277,297`. The larger alphabet has 23
unfinished cases, listed individually in the data.

The strongest large-base result is still far from nice: the recorded
complete-prefix candidates do not furnish a new unusually close near
miss. The purpose was to test a genuinely different, carry-rich family.

Data: [results/transformations-dense.jsonl](../results/transformations-dense.jsonl).
An independent direct enumeration of 26 smaller base/alphabet cases
agreed on completed-prefix counts, length-valid counts, and best
distinct-digit counts:
[results/transformations-validation.json](../results/transformations-validation.json).

### A small-alphabet obstruction in prime-plus-one bases

If `b=p+1 >= 24` for an odd prime `p`, no nice number can have all its
input digits in `0,...,4`.

Proof: put `S` equal to the sum of the input digits and `L` their count.
The total power length gives `L <= (b+3)/5`, hence
`1 <= S <= 4L <= 4(b+3)/5 < b-2 = p-1`. Because `b` is even,
the digit-sum constraint is `n^2(n+1)=0 (mod p)`. Primality forces
`n=0` or `-1 (mod p)`. But `n=S (mod p)`, and neither residue occurs
in `1,...,p-2`. Contradiction.

The proposition is a corollary of the familiar digit-sum test, rather
than a claim of a new general modular obstruction. It explains why many
dense-alphabet cases disappear before their carry trees are explored.

## Growing denominators and full-period rational expansions

The fixed-denominator obstruction in
[constructions.md](constructions.md) leaves denominators of order
`sqrt(b)` or larger open. When `d^2` is close to `b`, the square's
long-division digits can nearly encode the remainder states injectively.
Long multiplicative order can prevent the short-period repetition that
killed fixed denominators. The cube uses denominator `d^3`; its quotient
digits compress many remainder states into one digit, which reintroduces
collisions. Large order alone does not imply a permutation of digits.

### The plus-sign family is mostly killed by the digit sum

Suppose `n=(b^m+1)/d` is an integer and `gcd(d,b-1)=1`. Reducing modulo
`N=b-1` gives `d*n=2`. Multiply the necessary digit-sum congruence by
`d^3`:

`4(d+2) = [b(b-1)/2]*d^3 (mod N)`.

If `b` is even, this implies `N | 4(d+2)`, and therefore
`b <= 4d+9`. If `b` is odd, multiplying once more by two implies
`N | 8(d+2)`, hence `b <= 8d+17`. The precise odd-base congruence is
stronger than this necessary bound. Thus denominators growing only as
`sqrt(b)` cannot rescue this plus-sign family at arbitrarily large bases.

For the minus sign `n=(b^m-1)/d`, the same coprimality gives
`n=0 (mod N)`. Odd bases are therefore impossible; even bases survive
the digit-sum condition. Noncoprime denominators are outside these
particular arguments and must not be discarded on their basis.

### An explicit growing-denominator family that passes length and sum

Take a prime `d = 4 (mod 5)`, and set

`b=d^2-3`, `m=(d^2-1)/5`, `n=(b^m-1)/d`.

Here `m=(d-1)(d+1)/5` is a multiple of `d-1`, so Fermat's theorem
proves `n` is an integer. Put `B=b^m`. For `d>=19`,
`B/(2d)<n<B/d`, `4d^2<b^2`, `d^2>b`, `8d^3<b^2`, and `d^3>b`.
These inequalities give
`b^(2m-2)<n^2<b^(2m-1)` and `b^(3m-2)<n^3<b^(3m-1)`.
The power lengths are therefore `2m-1` and `3m-1`, whose sum is
`5m-2=d^2-3=b`. The base is even, and
`gcd(d,b-1)=gcd(d,4)=1`, so this also passes the digit-sum congruence.
The denominator grows as `sqrt(b)`, avoiding the previous asymptotic
fixed-denominator obstruction. The full-period question is meaningful:
`ord_(d^2)(b)` can equal `d(d-1)`.

This is a viable family of candidates, not a family of nice numbers.
All ten candidates with prime `19<=d<=199`, `d=4 mod 5`, were tested
with exact integers. They cover bases 358 through 39,598. None was
nice. Even the full-period cases had repeated digits early in their
combined suffixes. The first collision occurred after 17 to 167
distinct digits, depending on the candidate. For example, `d=29`
gives `b=838`, `m=168`, order 812 modulo `d^2`; digit 418 occurs at
cube position 4 and square position 30, counting from the units digit.

```sh
python3 scripts/transformations.py --mode growing-denominators \
  --denominator-max 199 \
  --output results/transformations-growing-denominators.json
```

Data: [results/transformations-growing-denominators.json](../results/transformations-growing-denominators.json).
The file stores the exact defining formula, verified power lengths,
orders, and a pair of positions certifying each failure. Early stopping
after an exact duplicate proves these particular candidates fail; it
does not measure their total diversity or exclude untested `d`.
All ten recorded multiplicative orders were independently rechecked by
direct modular iteration on 2026-09-25, rather than relying only on the
factor-based order routine used during the experiment. The dense-search
totals above were also recomputed from the saved JSONL records.

## Near-miss lifts into genuinely larger bases

The September 23 public dashboard snapshot was copied to
[results/public-near-misses-2026-09-23.json](../results/public-near-misses-2026-09-23.json).
Source: [public near-miss data](https://data.nicenumbers.net/cache_notable_numbers?select=number,niceness,base,num_uniques&order=off_by.desc).
It contains 896 records. Python parsed the numbers as exact integers;
every reported total length and distinct-digit count was independently
recomputed before the seeds were used. The experiment output records
the source URL and SHA-256 of this dated snapshot.

Only 58 seeds satisfy the digit-sum congruence. Permuting the input
digits preserves `n mod (b-1)`, so it cannot repair that failure for
the other 838 seeds in their original bases.

An especially sharp elementary observation applies to off-by-one
examples: if exactly `b` output digits contain `b-1` distinct symbols,
one digit `d` is duplicated and one digit `m` is missing. The required
digit-sum congruence says `d-m=0 (mod b-1)`. Since they are distinct
digits, this holds only when `{d,m}={0,b-1}`. In the highlighted
base-45 example, digit 9 is duplicated and 43 is missing, giving
`9-43=-34`, which is nonzero modulo 44. Input-digit permutations
therefore cannot repair that example in base 45. This is an elementary
consequence of the standard filter, not a novelty claim.

Simple relabelings of the same-length seed would remain close to bases
that the public project already reports searched. Instead the next
experiment grew the input length. Let the seed digit polynomial be
`P(X)=sum a_i X^i`, with `L` digits:

- **Stretch:** form `P(B^t)` for `t=2,3`. The input has
  `D=t*(L-1)+1` digits in the target base `B`.
- **Repeat:** repeat the seed digit word `t=2,...,8` times, giving
  `D=t*L` input digits. Algebraically this is
  `P(B)*(B^(t*L)-1)/(B^L-1)`.

Before either layout, the digits were mapped by selected affine maps
`a -> (u*a+v) mod B`: scales
`u in {1,2,3,floor((B-1)/(b_seed-1))}` and shifts
`v in {0,1,floor(B/3),floor(2B/3),B-1}`. Two more maps were
proportional scaling `floor(a*(B-1)/(b_seed-1))` and its digit
complement. Duplicate scale or shift choices were removed, although
different constructions can still produce the same candidate.

The input length restricts `B` to the four integers `5D-3,...,5D`.
Only target bases at least 57 and not already ruled out by the standard
base congruences were considered. A zero leading digit was rejected
rather than treated as padding. A zero units digit was rejected because
both powers would end in zero. The digit-sum and exact power-length
filters were followed by a complete integer evaluation of both powers.

```sh
python3 scripts/transformations.py --mode near-miss-lifts \
  --output results/transformations-near-miss-lifts.json
```

Data: [results/transformations-near-miss-lifts.json](../results/transformations-near-miss-lifts.json).

| Layout | Generated instances | Passed sum and length |
|---|---:|---:|
| Repeat | 384,543 | 2,482 |
| Stretch | 86,292 | 799 |
| Total | 470,835 | 3,281 |

No candidate was nice. Accepted candidates ranged from base 57 through
base 400. The greatest observed fraction of distinct digits was 108/148;
there was no especially close new near miss. The old seeds' high digit
diversity did not survive these lifts. This is a finite family result,
not an exhaustive search of any target base.

## An exact obstruction to stretching by three or more

The failed lifts suggested a stronger result. Write

`n=P(B^t)`, `P(X)=a_0+...+a_k X^k`, `0<=a_i<B`, `a_k>0`.

**Claim:** no such integer can be nice in base `B` when `t>=3`.
The main cases have direct proofs; the tiny remaining cases are
explicitly enumerated below. This does not exclude stretching by two.

If `a_0=0`, both powers end in zero, so assume `a_0>0`.
If `k>=1` and `t>=4`, the lowest `t` digits of the square are just
`a_0^2`. This number has at most two base-`B` digits. Positions 2 and
3, counting from zero at the units digit, are therefore both zero.
They lie in the ordinary square representation because `n>=B^t`.
This already rules out every nonconstant case with `t>=4`.

Now take `t=3` and `k>=2`. Length compatibility requires
`B>=15k+2>k+1`. Write `P(X)^2=sum Q_j X^j`. Each coefficient satisfies

`0<=Q_j<=(k+1)*(B-1)^2<B^3`.

Consequently the base-`B` blocks of `Q_j` at positions `3j,3j+1,3j+2`
in the square do not overlap or carry into one another. Consider the
third digits of blocks `j=0,1,2k-1`:

`floor(a_0^2/B^2)=0`,

`floor(2*a_0*a_1/B^2) in {0,1}`,

`floor(2*a_(k-1)*a_k/B^2) in {0,1}`.

These are three distinct positions, all below the leading block and
therefore present in the ordinary representation. They take at most
two values. The square repeats a digit.

For `t=3`, `k=1`, write `n=a*B^3+c`, with `1<=a,c<B`.
Length compatibility initially restricts `B` to 17,18,19,20.
The square digit at position 2 is zero. To avoid another zero at
position 5 requires `2*a*c>=B^2`; this forces `a>B/2`.
Since `B>=17`, the square then has eight digits and the cube twelve,
forcing `B=20`. Checking the 361 pairs `1<=a,c<20` leaves only four
with a nonrepeating square and the required total length:

| `a` | `c` | `n` | A repeated cube digit |
|---:|---:|---:|---:|
| 16 | 17 | 128017 | 12 |
| 17 | 16 | 136016 | 12 |
| 17 | 18 | 136018 | 12 |
| 18 | 17 | 144017 | 14 |

For completeness the verification script also enumerated all 1,230
pairs in bases 17 through 20, before using the analytic reduction.
It found no solution. When `k=0`, the input has one digit, so total
length compatibility permits only bases 2 through 5; all ten positive
one-digit candidates fail as well.

```sh
python3 scripts/transformations.py --mode stretch-exceptions \
  --output results/transformations-stretch-exceptions.json
```

The [finite-check output](../results/transformations-stretch-exceptions.json)
stores counts and the complete square/cube digit lists for the four
surviving squares. This closes the family with direct block arithmetic
and small reproducible checks, while leaving the overall nice-number
problem open.

## Remaining possibilities

Dense small-alphabet trees remain unfinished at the explicitly listed
node limits. Stretching by two is not excluded by the block argument:
square coefficients can occupy three digits and carry into the next
two-position block. Different growing-denominator formulas could still work,
especially if they enforce complementary digit sets rather than merely
long periods. A proof for all repdigits with a digit growing alongside
the base was not obtained in this branch; the bounded-denominator result
must not be stretched to cover that case.
