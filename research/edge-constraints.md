# Fixed leading and trailing checks still cannot establish uniqueness

2026-09-24. This extends the suffix-only limitation in
[obstructions.md](obstructions.md). It does not construct a nice number.

**Proposition.** Fix any positive depth `k`. Infinitely many bases have
correct-length candidates satisfying the digit-sum congruence for which
the first `k` and last `k` digits of both powers are all mutually distinct.
Thus adding any fixed number of leading-digit checks to the existing
fixed-depth suffix conditions still cannot prove global uniqueness.

We restrict to bases `b = 10h+2` and put `q=(b-2)/5`. Choose two coefficient
lists: a root prefix beginning with 3 and a root suffix beginning with 2
(listed respectively from high to low and low to high). Their initial
square/cube coefficients are 9, 27, 4, and 8, all distinct.

Extend each list to length `k`, greedily ensuring that the first `k`
coefficients of the two formal square/cube expansions, across both lists,
are all distinct. At each step each new coefficient is an affine function
of the new root coefficient, with slopes 6 and 27 for the prefix, or 4
and 12 for the suffix. Each equality with an old coefficient forbids at
most one input value; equality between the two new coefficients forbids
at most one more. Finitely many positive choices are forbidden, so the
construction always succeeds. Changing a new coefficient does not change
earlier coefficients.

Let `C` bound every coefficient of the prefix square and cube, and the
first `k` coefficients of the suffix square and cube. Choose a base in
the stated progression satisfying

`b > 2(C+75)`, `b > 64`, `b > max(prefix coefficients)+1`,
and `q >= 2k+2`.

Write the selected prefix polynomial as a root beginning at exponent `q`:

`n0 = a0*b^q + a1*b^(q-1) + ... + a_(k-1)*b^(q-k+1)`.

Here `a0=3` and `n0<4b^q`. For each exponent `e=2,3`, the first `k`
digits of `n0^e` are exactly the selected prefix coefficients, because
all raw coefficients are below `b`. The remaining value after removing
that prefix is less than

`C*b^(e*q-k+1)/(b-1)`.

Now perturb by `0 <= delta <= b^(q-k)`. The increase in the square is
at most `9*b^(2q-k)` and in the cube at most `75*b^(3q-k)`; the latter
follows from `3(n0+delta)^2*delta` and `n0+delta<5b^q`.
In either case, the remainder plus the increase is strictly less than
`b^(e*q-k+1)`, by the chosen bound on `b`. Therefore all first `k`
digits are unchanged throughout this interval. Their nonzero leading
digits also establish lengths `2q+1` and `3q+1`, totaling `b`.

Let `r mod b^k` be the chosen suffix root. CRT combines

`n = r mod b^k`, and `n = 0 mod (b-1)`.

The latter is a valid digit-sum class because `b` is even. The combined
period is `M=b^k(b-1)`. Since `q>=2k+2`, the perturbation interval has
length at least `b^(k+2)>M`, so it contains a representative. The suffix
coefficient bound guarantees the last `k` digits of both powers are
the chosen suffix coefficients. All `4k` edge digits are distinct by
construction. This proves the proposition.

**Implementation and check.** Run

```sh
python3 scripts/edge_constraints.py
```

[edge-constraints.json](../results/edge-constraints.json) contains full
integers and exact edge digits for depths 1, 2, 4, 8, and 12, in bases
212, 262, 552, 1812, and 2972. None is nice. These are explicit witnesses
to insufficiency of the filters, not record near misses.

An initial implementation bounded only the prefix coefficients and failed
an assertion at depth 12. Including the suffix coefficients in `C` fixed
the error; every recorded witness was regenerated and passes all stated
conditions. The proof was also reviewed independently by the obstruction
agent.

Research consequence: a successful proof or solver needs information
whose depth grows with the base, or a global constraint that these edge
conditions do not capture. The result does not exclude variable-depth
search or other modular conditions.
