# Constraint solving and local-search track

Started 2026-09-23; updated 2026-09-24. **No second nice number found. No nonexistence proof.**

This track tries to escape sequential enumeration by expressing the entire
problem as a constraint system. The executable is
[`scripts/constraint_search.py`](../scripts/constraint_search.py); complete
configurations, candidates, digit arrays, solver statistics, and outcomes are in
[`results/constraint-search*.jsonl`](../results/).

## Exact encodings

For a base `b` other than `1 mod 5`, write `b = 5k+r`, with
`r ∈ {2,3,4,5}`. The square/cube digit lengths are respectively
`(2k+1,3k+1)`, `(2k+1,3k+2)`, `(2k+2,3k+2)`, or `(2k+2,3k+3)`.
Taking exact integer square and cube roots gives the finite interval for `n`.
Every encoding requires both leading digits nonzero, all `b` output digits in
`[0,b-1]`, and all those digits different.

1. **Nonlinear integer arithmetic:** weighted digit sums equal `n²` and `n³`.
2. **Bit vectors:** exact-width multiplication with weighted digit sums. The
   exact upper bound on `n` prevents modular wraparound. In power-of-two bases,
   the output digits concatenate directly into the product; no radix conversion
   circuit is necessary. Optional `n mod (b-1)` constraints use sums of small
   chunks in those bases, avoiding division of a large bit vector.
3. **Carry equations:** write `n = Σ a_i b^i`, square digits `s_i`, cube digits
   `t_i`. Then impose the grade-school product recurrences
   `u_k + Σ_(i+j=k) a_i a_j = s_k + b u_(k+1)` and
   `v_k + Σ_(i+j=k) a_i s_j = t_k + b v_(k+1)`.
   Initial and terminal carries are zero. If `n` has `d` digits, every carry is
   in `[0,d(b-1)]`; induction follows because a column has at most `d` products
   of two digits. This replaces huge nonlinear integer variables with bounded
   digit products. It is an exact reformulation, not an existence theorem.

An optional pinned suffix narrows the problem to a residue class. An UNSAT
answer for such a run would exclude only that residue class. No pinned runs
were used in the initial experiments.

## Initial results

All runs used seed `20260923` and Z3 `5.1.0` from the `z3-solver 5.1.0.0` wheel
installed only in `/private/tmp/nice-z3`. No project dependency was modified.

| Experiment | Bases | Bound per base | Outcome |
|---|---|---|---|
| Bit-vector validation | 2, 4, 5, 8, 9, 10, 12, 13, 14 | 3 seconds | SAT only in base 10; recovered `n=69` in 0.026 seconds; others UNSAT |
| Nonlinear integers | 10, 12, 57, 58, 64, 100, 130, 200 | 10 seconds | All UNKNOWN / timeout, including known-solvable base 10 |
| General bit vectors | 57, 58, 100, 130, 200 | 15 seconds | All UNKNOWN / timeout |
| Initial power-of-two bit vectors | 32, 64, 128 | 45 seconds | All UNKNOWN / timeout |
| Direct digit concatenation, no residue filter | 10, 64, 128, 512 | 30 seconds, 1,024 MB | Base 10 recovered 69; 64 timed out; 128 and 512 exceeded memory cap |
| SAT local search, concatenation plus residue filter | 10, 128, 512 | 30 seconds, 1,024 MB | Base 10 timed out; 128 and 512 exceeded memory cap |

The memory setting is a Z3 resource limit, not a hard operating-system cap or a
statement about physical machine memory. Its checks can overshoot: an optimized
base-128 run reported peak allocation of 2,291 MB despite the 1,024 MB setting.
UNKNOWN, timeout, and memory exhaustion imply nothing about mathematical
existence. Runtime limits exclude model-construction time, and cancellation may
slightly exceed the requested timeout. No proof certificate was exported for
the small UNSAT validation cases.

Base 512 remains interesting under the random-digit heuristic: candidates have
up to 921 bits, while the log-probability cost of collision-free random digits is
about 733 bits. This comparison ignores arithmetic dependencies and is not a
proof of existence or an efficient search algorithm. The direct model uses
1,845 square bits, 2,763 cube bits, and 512 output digits of nine bits each.
The oversized multiplication circuits are a concrete implementation barrier.
Base 256, despite being computationally convenient, is excluded by `b=1 mod 5`.

## Local search experiment

For each of bases 64, 128, and 512, compared 50,000 uniform candidate proposals
against 50,000 proposals that change one radix digit of `n`. The latter keeps a
proposal if it increases the number of distinct square/cube digits, using fewer
pairwise collisions to break ties, and restarts after 200 unsuccessful or equal
proposals. Every candidate has the correct combined digit length. These are
proposal counts, not guaranteed distinct candidates.

| Base | Best uniform distinct digits | Best digit-mutation distinct digits |
|---|---:|---:|
| 64 | 51 / 64 | 51 / 64 |
| 128 | 96 / 128 | 97 / 128 |
| 512 | 356 / 512 | 355 / 512 |

Exact candidate integers and full digit arrays are saved in
`results/constraint-search-stochastic.jsonl`. They are benchmarks, not claimed
record near misses. Neither method came close to all digits unique.

The lack of improvement has a structural explanation, but this explanation is
heuristic: if `n` has about `m` radix digits, a change of order `b^j` changes its
square by order `b^(m+j)` and cube by order `b^(2m+j)`. The bottom `j` digits stay
fixed, but about `m` square digits and `2m` cube digits remain exposed to change.
Thus changing one input digit can disturb roughly three-fifths of the output
digits, even for a high input position. This limits conventional hill climbing.

## Reproduction

```sh
python3 -m pip install --target /private/tmp/nice-z3 --no-cache-dir z3-solver==5.1.0.0
PYTHONPATH=/private/tmp/nice-z3 python3 scripts/constraint_search.py --bases 2 4 5 8 9 10 12 13 14 --encoding bv --timeout 3 --output /private/tmp/nice-bv-validation.jsonl
PYTHONPATH=/private/tmp/nice-z3 python3 scripts/constraint_search.py --bases 10 12 57 58 64 100 130 200 --encoding int --timeout 10 --output /private/tmp/nice-int.jsonl
PYTHONPATH=/private/tmp/nice-z3 python3 scripts/constraint_search.py --bases 10 64 128 512 --encoding bv --timeout 30 --no-residue-filter --memory-mb 1024 --output /private/tmp/nice-concat.jsonl
python3 scripts/constraint_search.py --bases 64 128 512 --encoding stochastic --trials 50000 --output /private/tmp/nice-stochastic.jsonl
```

The script now contains explicit concatenation and chunked residue reduction;
the first baseline runs predated these optimizations. Their JSONL files record
what was run, but rerunning the current script does not reconstruct the older
internal expression trees exactly.

## Next bounded hypotheses

Test explicit Karatsuba multiplication instead of Z3's default multiplication
circuits, and a sorting network enforcing that output digits sort to `0…b−1`
instead of a quadratic pairwise distinctness encoding. Neither is justified as
more than a potential circuit-size reduction until benchmarked. Carry-system
results and any subsequent experiments will be appended below.

## Carry and circuit experiments, September 24

The carry model recovered `n=69` in base 10 in 2.49 seconds, compared with the
direct nonlinear integer model's failure within 10 seconds. It also returned
UNSAT for base 4. Bases 57, 64, 128, and 512 timed out with a 10-second setting.
The base-128 cancellation completed after 12.82 seconds. These results are in
`results/constraint-search-carry.jsonl`.

Implemented explicit unsigned Karatsuba multiplication, splitting operands
recursively until 16-bit leaf products. It uses exact full-width products and
only trims output bits when the proven bound on `n` makes them zero. The sorting
alternative uses a bitonic network and requires its sorted result to be
`0,1,…,b−1`. Non-power-of-two lengths are padded with the sentinel digit `b`.

Before searching, validated 100 randomly instantiated exact products at widths
up to 921×921 bits; proved three small symbolic equivalences by asking Z3 for
counterexamples and obtaining UNSAT; and ran 301 sorting checks, including
exhaustive arrays in bases 2, 3, and 4, plus good/bad permutations through base
512. Reproduction:

```sh
PYTHONPATH=/private/tmp/nice-z3 python3 scripts/constraint_circuit_check.py
```

The result artifact is `results/constraint-search-circuit-validation.json`.
These checks caught and fixed an AST-identifier cache-lifetime bug before the
optimization searches ran. They support implementation correctness; they are
not a formal proof of the full arbitrary-width implementation.

Every optimized configuration recovered 69 in base 10. Karatsuba plus sorting
also returned UNSAT in bases 4 and 14. Larger-base results:

| Multiplication | Digit uniqueness | Base | Outcome |
|---|---|---:|---|
| Karatsuba | Pairwise | 128 | UNKNOWN, timeout after 32.09 seconds with 30-second setting |
| Karatsuba | Sorting network | 64 | UNKNOWN, timeout after 30.08 seconds |
| Karatsuba | Sorting network | 128 | UNKNOWN, memory limit |
| Built-in | Sorting network | 128 | UNKNOWN, memory limit |
| Karatsuba | Pairwise, fresh process | 512 | UNKNOWN, memory limit after 8.04 seconds |
| Karatsuba | Sorting, fresh process | 512 | UNKNOWN, memory limit after 2.78 seconds |

For base 128, Karatsuba plus pairwise uniqueness reached actual SAT search with
453,315 Boolean variables and 23,881 conflicts; Karatsuba plus sorting created
680,797 variables and exhausted the resource setting much sooner. Thus the
sorting network was **worse in this implementation**. This is an empirical
circuit result, not a general argument against sorting networks. Separate fresh
base-512 processes confirmed that its memory failures were not merely inherited
allocations from a preceding base-128 attempt.

Logs: `constraint-search-karatsuba-pairwise.jsonl`,
`constraint-search-karatsuba-sort.jsonl`, `constraint-search-bv-sort.jsonl`, and
the two `constraint-search-karatsuba-*-fresh512.jsonl` files in `results/`.

```sh
PYTHONPATH=/private/tmp/nice-z3 python3 scripts/constraint_search.py --bases 10 128 512 --encoding karatsuba --distinct pairwise --timeout 30 --memory-mb 1024 --output /private/tmp/nice-karatsuba.jsonl
PYTHONPATH=/private/tmp/nice-z3 python3 scripts/constraint_search.py --bases 512 --encoding karatsuba --distinct sort --timeout 45 --memory-mb 1024 --output /private/tmp/nice-karatsuba-sort512.jsonl
```

**Remaining obstacle:** expressing an instance is easy; finding a satisfying
assignment or ruling out an entire unsearched base is not. The useful result
here is a validated collection of exact encodings and documented resource
failures. None has yet supplied a new nice number or a general impossibility
argument. Increasing the same timeouts alone is not supported by this evidence
as a promising research direction.
