# Exact counting: what an existence proof would have to control

2026-09-25. Work begun by the obstruction agent and completed/reviewed by
the parent after a worker limit interrupted that turn. No existence or
uniqueness theorem has been obtained.

## A single-polynomial reformulation

Fix a base `b` and its exact candidate interval `I`, with square length
`s` and cube length `c`, where `s+c=b`. Let

`F_b(n) = n² + b^s*n³`, and `M=b^b`.

For every `n` in `I`, the base-`b` digits of `F_b(n)` are exactly the
cube followed by the square. The blocks do not overlap, since `n²<b^s`.
Let `P_b` be the set of digit permutations with nonzero digits at both
block-leading positions. Then the exact number of nice candidates is

`C_b = sum_(n in I) 1_(P_b)(F_b(n))`.

There are `(b-2)*(b-1)!` elements of `P_b`. This reformulates the problem
as a cubic taking a value in a permutation set. It does not remove the
arithmetic correlations: the cubic coefficient `b^s`, the modulus, and
the number of digit positions all grow with the base.

With `e_M(t)=exp(2*pi*i*t/M)`, define

`P_hat(a) = sum_(x in P_b) e_M(-a*x)`,
`S(a) = sum_(n in I) e_M(a*F_b(n))`.

Finite Fourier inversion gives the exact identity

`C_b = (|I|*|P_b| + sum_(a=1)^(M-1) P_hat(a)*S(a)) / M`.

A sufficient positivity criterion is

`sum_(a=1)^(M-1) |P_hat(a)*S(a)| < |I|*|P_b|`.

No bound establishing this inequality has been found. `P_hat(a)` itself
is a permanent of a matrix of phases, with two entries forbidden to stop
leading zeroes. Permutation constraints do not factor by digit position.
Large terms associated with digit-sum congruences also need explicit
treatment; discarding all nonzero frequencies as small is unjustified.

The straightforward Parseval/Cauchy estimate is inadequate. Because
`0<=F_b(n)<M` and `F_b` is strictly increasing, it is injective on `I`.
Writing `N=|I|` and `P=|P_b|`, Parseval bounds the absolute remainder by

`sqrt((M*P-P²)*(M*N-N²))/M`.

This exceeds the proposed main term `N*P/M` unless `N+P>M`.
Here the permutation set and candidate set are far smaller than `M`.
Thus this generic norm estimate cannot prove positivity, even where the
random-digit expected count is enormous.

## Inclusion-exclusion and quantitative accuracy

For each subset `J` of the digit alphabet, let `A(J)` count candidates
whose two powers avoid every digit in `J`. Since there are exactly `b`
output positions, covering all `b` digits is equivalent to pandigitality:

`C_b = sum_(J subset {0,...,b-1}) (-1)^|J| * A(J)`.

This is exact. To substitute a random-string model, define `p(J)` as the
probability that a uniformly sampled `b`-digit string with the two leading
positions nonzero avoids `J`. There are `(b-1)²*b^(b-2)` legal strings.
Their pandigital probability is exactly

`p = (b-2)*(b-1)! / ((b-1)²*b^(b-2))`.

If every avoidance probability `A(J)/N` differed from `p(J)` by at most
`epsilon`, a sufficient condition would be `epsilon < p/2^b`. If instead
every avoidance probability had relative error at most `delta`, a
sufficient condition would be `delta < p / sum_J p(J)`. These are
conditional criteria, not bounds we have proved for polynomial digits.

The script computes the requirements exactly before taking logarithms:

| Base | First positive odd Bonferroni depth in the legal-string model | Sufficient uniform absolute error, log10 | Sufficient uniform relative error, log10 |
| ---: | ---: | ---: | ---: |
| 64 | 49 | -45.76 | -34.18 |
| 128 | 99 | -92.67 | -69.56 |
| 512 | 399 | -374.73 | -282.47 |

Even the ideal model needs deep inclusion-exclusion for this crude lower
bound. The accuracy demands also reveal how wasteful bounding every term
separately is. In moderate bases the absolute-error criterion is smaller
than the granularity `1/N` of candidate probabilities. An argument with
cancellation or a much more specialized sieve would be needed.

## Marginal uniformity does not suffice

There is a simple exact counterexample to inferring pandigitality from
low-order uniformity alone. Sample `b-1` slots independently and uniformly
from `0,...,b-1`; choose the last slot so the total is a fixed residue
modulo `b` different from `b(b-1)/2`. Every selection of `b-1` slots is
uniform, but no resulting string is pandigital. This is an abstract
distributional example, not a model claimed to obey our arithmetic or
leading-digit constraints.

More generally, condition the legal-string model on not being pandigital.
Its total variation distance from the original model is only `p`, which
is exponentially small. It nevertheless has no successes. Apparently
random marginals and fitted histograms therefore cannot settle the rare
event without sufficiently strong quantitative control.

## A refined heuristic, explicitly not a proof

The script counts candidates in the exact interval satisfying both the
digit-sum congruence and distinct final square/cube digits using CRT.
For a candidate with fixed final digits and correct digit sum, it treats
the remaining positions as uniform among legal strings of that sum.
This conditional model predicts these expected counts:

| Base | Expected count in conditional model |
| ---: | ---: |
| 57 | about 0.00111 |
| 128 | about 0.411 |
| 150 | about 58.0 |
| 200 | about 8.19 million |
| 512 | about `1.49e57` |

These are expectations in a stipulated distribution, not estimates with
proved error bars and not probabilities of existence. In particular,
base 128 may well have no solution despite being convenient for bit
vectors. Abundance in the model at base 512 does not make an individual
candidate likely to succeed.

Reproduce with `python3 scripts/existence_counting.py`. Raw exact counts,
logs, an exhaustive base-4 legal-string check, and a base-4 verification
of the marginal counterexample are in
[existence-counting.json](../results/existence-counting.json).
The [literature applicability note](analytic-existence.md) explains why
the cited existing restricted-digit theorems do not directly supply the
missing joint bounds.
