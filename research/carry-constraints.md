# Carry constraints and sparse-input obstructions

September 24, 2026. This continues the obstruction investigation. The results
below are proved necessary conditions. The executable experiments check the
arithmetic identities and compute bounds; they are not a search of all
candidates and do not establish uniqueness.

## 1. Exact carry accounting

Write `n=P(b)`, where `P(X)=sum_(i=0)^k a_i X^i` is its ordinary digit
polynomial. Let `F_j` and `G_j` be the raw coefficients of `P²` and `P³`.
The square carries `u_j` and cube carries `v_j` satisfy

`u_0=v_0=0`,

`s_j = F_j + u_j − b*u_(j+1)`,

`c_j = G_j + v_j − b*v_(j+1)`,

where `s_j,c_j` are ordinary output digits; continue with zero raw
coefficients until the carries disappear. Every coefficient and carry is
a nonnegative integer.

If `S=sum_i a_i`, summing the two recurrences gives the exact identity

`sum_j s_j + sum_j c_j = S²+S³ − (b−1)*(sum_j u_j+sum_j v_j)`.

Consequently any nice number has a prescribed total **carry mass**
(the sum of the carry values, not their number):

`C = (S²(S+1) − b(b−1)/2)/(b−1)`.

This packages the familiar congruence together with nonnegativity and a
quantitative carry requirement. A nice cube must have a carry, by the
[complete carry-free obstruction](constructions.md#1-a-carry-free-construction-cannot-work),
so `C≥1`.

## 2. Carries must break enough cube residues modulo 3

For each exponent `j` not divisible by 3, Frobenius gives `G_j≡0 (mod 3)`.
Hence its cube digit satisfies

`c_j ≡ v_j − b*v_(j+1) (mod 3)`.

There are `2k` such positions between 0 and `3k`, and only `ceil(b/3)`
digits in the entire alphabet divisible by 3. Therefore at least

`E = max(0, 2k − ceil(b/3))`

of these positions require a nonzero carry expression modulo 3. This is
the quantitative condition found in the parallel construction note.

Two additional consequences follow:

* If `3|b`, at least `E` incoming cube carries are nonzero modulo 3.
* If `3∤b`, at least `ceil(E/2)` cube carries are nonzero modulo 3,
  because any individual carry participates in at most two of the
  displayed expressions. This also bounds the total carry mass below.

Combining these with `C≥1` and Section 1 produces a scalar constraint on
the input digit sum. The script computes the least positive `S` that
satisfies the congruence and this lower carry-mass bound. Such an `S` is
only a lower bound on a real solution's digit sum; it need not be attainable.

For powers of two, the carry expressions have particularly small domains:

* `b=2^w`, w even: `c_j≡v_j−v_(j+1) (mod 3)` for `3∤j`.
* `b=2^w`, w odd: `c_j≡v_j+v_(j+1) (mod 3)` for `3∤j`.

Thus base 64 requires at least two residue-breaking edges and at least one
nonzero-mod-3 carry. Base 128 requires seven edges and four such carries;
base 512 requires 33 edges and 17 such carries. These are unavoidable
features of a candidate, but they are too weak to exclude those bases.

For an even base, the analogous square identity is exact at every position:

`s_j ≡ u_j + [j even]*a_(j/2) (mod 2)`.

It can be encoded using carry parity without constructing each full raw
coefficient. By itself it has no comparable shortage obstruction: there
are only about `b/5` forced-even raw square positions but about `b/2`
available even digits.

## 3. Fixed sparsity is impossible even when digit values grow

Let `A={i:a_i≠0}`, let `t=|A|`, and write `2A={i+j:i,j∈A}` and
`3A={i+j+h:i,j,h∈A}`. Correct total output length implies
`k=floor((b−2)/5)`, and in particular `k+1<b`.

Every raw square coefficient is at most `(k+1)(b−1)²`. Induction in the
carry recurrence therefore gives

`u_j ≤ (k+1)(b−1) < b²`.

If two successive raw square coefficients are zero, their processing
reduces an incoming carry to zero by two divisions by `b`. Consequently
every nonzero ordinary square digit lies in

`2A + {0,1,2}`.

If its length is `L₂`, a nice square has at least `L₂−1` nonzero digits,
because zero occurs only once across both powers. Thus

`L₂−1 ≤ |2A+{0,1,2}| ≤ 3|2A| ≤ 3*t*(t+1)/2`.

Since `L₂≥2k+1`, a convenient weaker form is

**`t(t+1) ≥ 4k/3`.**

This excludes every family with a fixed number of nonzero input digits as
the base grows, even if those digits approach `b−1`. It is stronger in
scope than merely excluding fixed small coefficients or carry-free
constructions. Examples of necessary lower bounds are six nonzero input
digits in base 128 and 12 in base 512.

The same argument gives `v_j≤(k+1)²(b−1)²<b⁴`, because at most `(k+1)²`
ordered index triples contribute to a fixed raw cube coefficient. Therefore
every nonzero cube digit lies in `3A+{0,1,2,3,4}`. The support-specific
combined bound is

`b−1 ≤ |2A+{0,1,2}| + |3A+{0,1,2,3,4}|`.

This can reject a specified sparse support before trying any digit values.
Its version using only `t` is usually weaker than the square bound.

An equivalent local consequence is useful for construction templates:
four consecutive absent raw square coefficients force at least two zero
square digits; six consecutive absent raw cube coefficients force at
least two zero cube digits. These blocks must lie in the ordinary power
representations for the conclusion to apply.

## 4. Power-of-two bases require many binary 1 bits in n

Let `b=2^w` and let `H(x)` denote ordinary binary popcount. Pandigitality
implies

`H(n²)+H(n³) = w*2^(w−1)`.

There is a sharper individual constraint. Define `W_w(L)` as the least
possible sum of binary popcounts of `L` distinct digits from `0,…,2^w−1`.
It is computed exactly by taking digits of weights `0,1,…,w` in order;
there are `binomial(w,j)` digits of weight `j`. If the square and cube
lengths are `L₂,L₃`, then

`H(n²)≥W_w(L₂)`, and `H(n³)≥W_w(L₃)`.

Now let `t=H(n)`. Binary addition never increases total popcount. Expanding
the square into diagonal terms and paired cross terms proves

`H(n²) ≤ t + binomial(t,2) = t(t+1)/2`.

For the cube, equal-index triples have coefficient 1, terms with exactly
two equal indices have coefficient 3, and terms with all three distinct
have coefficient 6. The latter two coefficients each have binary weight 2,
giving

`H(n³) ≤ t + 2t(t−1) + 2*binomial(t,3)`.

These inequalities and the fixed combined weight yield the following
rigorous lower bounds. Their input sparsity columns refer to different
representations: nonzero base digits versus binary 1 bits.

| Base | Square/cube lengths | Minimum nonzero base digits in n | Minimum binary 1 bits in n | Minimum input digit sum S |
|---:|---:|---:|---:|---:|
| 64 | 26 / 38 | 4 | 10 | 21 |
| 128 | 51 / 77 | 6 | 15 | 126 |
| 512 | 205 / 307 | 12 | 36 | 146 |
| 1024 | 410 / 614 | 17 | 53 | 186 |
| 2048 | 819 / 1229 | 23 | 80 | 712 |
| 8192 | 3277 / 4915 | 47 | 177 | 8190 |

Bases 256 and 4096 are already excluded by the length condition.

For base 128, `S≥126` also proves that some input digit is at least 5,
because the input has 26 digits. More generally, if `b−1` is prime and
`b` is even, the standard congruence forces positive `S≥b−2`. For `b>22`,
this excludes an input whose digits all lie in `0,…,4`: it would instead
satisfy `S≤4(k+1)≤4(b+3)/5<b−2`. This is an exact subfamily exclusion,
not a proof against ordinary candidates with larger digits.

## 5. Solver use and limitations

These constraints are natural for a solver that already models digit
coefficients and carries:

* Restrict carry domains using the explicit magnitude bounds.
* Enforce the scalar carry-mass identity and minimum residue-breaking count.
* Reject sparse supports by computing their expanded sumsets before
  introducing coefficient variables.
* In a power-of-two bit-vector model, impose the required total output
  popcount and the individual lower bounds; low-popcount input templates
  can be discarded immediately.

The popcount equality is logically redundant once all output digits are
distinct and have the correct total length. It may nevertheless give
earlier propagation, but that is a solver-performance hypothesis requiring
timing experiments, not an established speedup. Adding carry variables to
a monolithic multiplication model may instead make it slower.

The main limitation remains substantial: none of these bounds excludes
dense, irregular inputs and carries. Random-looking candidates typically
have far more nonzero input digits and binary 1 bits than the minima, so
these results target construction families rather than the bulk search.

## 6. Reproduction and validation

```sh
python3 scripts/carry_constraints.py
```

Output: [results/carry-constraints.json](../results/carry-constraints.json).
The script computes the table exactly and verifies the coefficient
normalization, carry-mass identity, residue identities, carry upper bounds,
support coverage, and binary-weight upper bounds on `(69,10)` and 1,000
deterministically seeded random inputs across bases 10,32,64,128,512.
Random input lengths match the necessary input length; they need not have
the required square/cube lengths and are not claimed to be nice.

The general claims are supported by the proofs above. The randomized
checks are implementation validation, not evidence that an unchecked
base contains no solution. This note makes no claim of priority.
