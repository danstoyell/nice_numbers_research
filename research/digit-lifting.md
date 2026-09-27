# Randomized digit lifting: improved sampling, still far from a solution

Experiment run 2026-09-23; reviewed 2026-09-24. No second nice number found.

The hypothesis was that choosing the base-`b` digits of `n` one at a time,
from least significant to most significant, would greatly outperform
uniform sampling. After choosing `k` digits of `n`, the bottom `k` digits
of each of `n²` and `n³` are fixed. Reject an extension as soon as two of
those `2k` output digits coincide.

The implementation also requires each partial residue to have an extension
inside the exact candidate interval satisfying the digit-sum congruence.
Since `b^k = 1 mod (b-1)`, this is an exact CRT feasibility test. Arithmetic
uses unbounded Python integers. At each step at most 64 candidate input
digits are tried without replacement. This is randomized incomplete
search, not exhaustive enumeration or a uniform distribution of survivors.

Reproduce from the repository root:

```sh
python3 scripts/digit_lifting.py --attempts 2000
```

Raw output: [digit-lifting.json](../results/digit-lifting.json). Every base
gets 2,000 attempted paths, plus 2,000 uniformly drawn candidates satisfying
the same digit-sum congruence as a baseline. The seed is `20260923 + base`.

| Base | Completed paths | Mean distinct digits, lifted | Mean, baseline | Best lifted | Best baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| 57 | 746 | 38.60 | 36.10 | 46/57 | 44/57 |
| 64 | 839 | 43.21 | 40.52 | 50/64 | 50/64 |
| 100 | 1,586 | 67.11 | 63.42 | 78/100 | 75/100 |
| 128 | 428 | 85.87 | 81.06 | 98/128 | 93/128 |
| 150 | 504 | 100.53 | 94.93 | 112/150 | 107/150 |
| 200 | 414 | 134.58 | 126.54 | 146/200 | 142/200 |
| 512 | 71 | 343.41 | 323.72 | 357/512 | 346/512 |

The effect is real within these samples but modest: roughly 67% of digits
are distinct, versus 63% in the baseline. This does not approach 100%.
The low completion rate at base 512 partly reflects the cap of 64 attempted
digits out of 512; it does not mean most exact extensions are impossible.

A heuristic explains the limit. An entire `n` has about `b/5` digits, so
this process forces only about `K=2b/5` distinct output digits before the
remaining outputs are evaluated. If those remaining `L=b-K` digits behave
randomly, the expected total distinct count is

`K + (b-K) * (1 - (1-1/b)^L)`,

approximately `0.671b`. The model probability of completing all missing
digits is `L! / b^L`, still exponentially tiny. These formulas are a
diagnostic model, not proven distributions for polynomial digits.

Decision: do not spend large computational budgets repeating this sampler
unchanged. It needs a way to constrain the remaining middle/high digits
during construction. Bit-vector solvers and carry constraints are separate
attempts at that missing step.
