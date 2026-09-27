# Direct, streamed Boolean circuits

Updated September 26, 2026. **No second nice number or new nonexistence result.**

The hypothesis was that Z3's intermediate expression trees, rather than the
final propositional problem alone, caused the base-512 export failure. This
experiment supports that hypothesis: base 512 now exports successfully in
14.19 seconds using about 41 MiB observed resident memory. However, its SAT
solver subsequently exceeds the unchanged memory limit. These are separate
outcomes; a completed export is not progress toward satisfying the instance.

Implementation: [`scripts/direct_cnf.py`](../scripts/direct_cnf.py). It uses
only the Python standard library and the existing exact-bound helper. SAT
solving reuses [`scripts/sat_backend.py`](../scripts/sat_backend.py).

## Exact formulation

The generator gives each input bit of `n` a propositional variable, constrains
`n` to the exact integer-root interval, and constructs exact unsigned square
and cube circuits. It streams clauses immediately to disk. It retains short
lists of live bit literals, without a global expression tree or gate cache.

The arithmetic uses:

- constant and alias simplification for AND, XOR, and majority gates;
- ripple-carry addition and ripple-borrow subtraction;
- small column-compressed multiplication circuits; squaring shares symmetric
  terms, counting off-diagonal terms at twice their positional weight;
- recursive Karatsuba multiplication, with 16-bit leaf products by default;
- direct digit slicing for power-of-two bases, and exact division by a
  constant for the small non-power-of-two validation cases.

Product widths are sufficient for full products. Temporary subtraction results
in Karatsuba are nonnegative: `(a_low+a_high)(b_low+b_high)` contains both the
low and high products, and subtraction leaves the two cross products. Output
digits obey the required lengths; any excess high bits are constrained to
zero, and both leading digits are nonzero. Shared occupancy decoders require
each digit value to occur. With exactly `b` positions, this is a bijection.

The optional digit-sum residue filter from the older Z3 models is omitted.
That filter is mathematically redundant, but its omission can change solver
behavior. Circuit-size comparisons are therefore comparisons of complete
equivalent formulations, not a change to only one internal component.

## Validation

`python3 scripts/direct_cnf.py --validate` completed these checks:

| Check | Assignments |
|---|---:|
| Complete AND/XOR/majority input-output truth tables | 32 |
| Exhaustive small products, including recursive and unequal-width cases | 6,116 |
| Exhaustive small squares | 510 |
| Exact quotient/remainder in bases 2, 3, 5, 8, 10, and 13 | 1,536 |
| Exhaustive occupancy arrays in bases 2, 3, and 4 | 287 |
| Exact interval comparator | 32 |
| Random larger products through 179×179 bits | 50 |

All passed; validation also evaluates every emitted gate clause for each
tested assignment. These tests are reproducible implementation evidence, not
a formal arbitrary-width proof. The record is
`results/direct-cnf-validation.json`.

The complete encoding returned SAT with `n=69` in base 10 and UNSAT in base 4.
The separate `scripts/verify.py` confirmed 69's exact square and cube digits.
Its independently formulated interval enumerator agreed with all exported
bounds and lengths for bases 4, 10, 128, and 512; see
`results/direct-cnf-independent-bounds.json`.

## Export results

The controller retains the 1,536 MiB RSS threshold. It checks memory and wall
time every 0.25 seconds, so observed peaks can overshoot the threshold and can
miss very short peaks. Export wall limit was 120 seconds; all completed much
sooner. CNF files and intermediate logs are in temporary directories recorded
in the result JSON, rather than hundreds of megabytes in the project folder.

| Base | Variables | Clauses | CNF bytes | Construction/export time | Observed RSS |
|---|---:|---:|---:|---:|---:|
| 10 | 1,744 | 6,381 | 97,332 | 0.0069 s | Small run finished between samples |
| 128 | 222,069 | 904,419 | 19,662,725 | 0.88 s | 23.8 MiB |
| 512 | 3,239,188 | 13,157,168 | 330,008,689 | 14.19 s | 40.6 MiB |

The previous Z3 occupancy export for base 128 required 234,008 variables,
1,138,341 clauses, and about 1,302 MiB observed RSS. The streamed version uses
roughly 20% fewer clauses and vastly less exporter memory. The previous
base-512 Z3 export never completed within the resource threshold.

The base-512 arithmetic portion accounts for 2,718,356 variables and
11,594,160 clauses; adding occupancy gives the totals above.

## Backend results, separately from export

Each backend stage includes loading and solving under a 60-second wall limit,
100,000-conflict budget, and the same 1,536 MiB RSS threshold. CaDiCaL was used
for small validation cases; Kissat 4.0.4 was used for the larger cases.

| Base | Load time | Solve outcome | Observed RSS |
|---|---:|---|---:|
| 10 | Small | SAT, exactly `n=69`, independently verified | Small validation run |
| 4 | Small | UNSAT, already-known small case | Small validation run |
| 128 | 0.44 s | UNKNOWN after 15.82 s solving at conflict budget | 365 MiB |
| 512 | 7.30 s | Loaded completely; early solving stopped at RSS threshold | 1,544 MiB |

The base-512 worker was terminated after 12.80 seconds total wall time. Thus it
got beyond the previous export barrier and completed loading, but solving
still exceeded the allowed memory. Neither high base yielded a candidate or
UNSAT conclusion. The old backend script's top-level `encoding` field is its
default argument; `source_encoding`, `source_distinct`, `reused_from`, and the
referenced direct-export file identify the actual circuit used.

## Leaf-size dead end

A count-only base-512 arithmetic experiment compared leaf widths 16, 24, 32,
48, and 64, without creating files or starting solvers. These counts omit
bounds and occupancy, so they are intentionally lower than full-export counts.

| Leaf width | Arithmetic variables | Arithmetic clauses |
|---|---:|---:|
| 16 | 2,716,516 | 11,588,637 |
| 24 | 2,712,457 | 11,571,906 |
| 32 | 2,940,585 | 12,528,926 |
| 48 | 2,940,585 | 12,528,926 |
| 64 | 3,471,491 | 14,770,314 |

Width 24 improves clause count only about 0.14%; larger leaves are worse. This
does not justify another resource-intensive solver run on a nearly identical
base-512 circuit. Results are in `results/direct-cnf-leaf-size.json`.

## Reproduction

```sh
python3 scripts/direct_cnf.py --validate --output results/direct-cnf-validation.json
python3 scripts/direct_cnf.py --base 128 --output results/direct-cnf-base128.json
python3 scripts/direct_cnf.py --base 512 --output results/direct-cnf-base512.json
PYTHONPATH=/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 10 --backend cadical300 --reuse-export results/direct-cnf-base10.json --output results/direct-cnf-solve-base10.json
PYTHONPATH=/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 128 --backend kissat404 --reuse-export results/direct-cnf-base128.json --output results/direct-cnf-solve-base128.json
PYTHONPATH=/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 512 --backend kissat404 --reuse-export results/direct-cnf-base512.json --solve-timeout 60 --conflicts 100000 --rss-mb 1536 --output results/direct-cnf-solve-base512.json
```

The monitored commands require permission for `ps` to inspect their own
workers, as described in the preceding SAT-backend note. Generating a base-10
export first requires `python3 scripts/direct_cnf.py --base 10 --output
results/direct-cnf-base10.json`.

**Remaining obstacle:** memory during SAT solving, followed by mathematical
search difficulty. Raising the cap was deliberately not attempted. Smaller
circuits or a solver configuration with less preprocessing memory would be a
different bounded hypothesis; another identical longer run would not address
the observed failure.

## Intermediate bases 150 and 200

The next hypothesis traded convenient binary digit extraction for smaller
products in bases where the project's conditional random-digit heuristic
expects more solutions. This is only a motivation for selecting instances;
heuristic abundance does not guarantee existence or an easy SAT search.

Both complete formulas exported within the same 1,536 MiB RSS threshold and a
120-second wall limit:

| Base | Variables | Clauses | CNF bytes | Export time | Observed RSS |
|---|---:|---:|---:|---:|---:|
| 150 | 1,733,228 | 6,391,112 | 152,748,640 | 7.97 s | 24.9 MiB |
| 200 | 2,511,432 | 9,313,623 | 228,086,331 | 8.90 s | 26.1 MiB |

The smaller base-150 formula was selected for the one permitted backend
attempt. Kissat loaded it in 3.334 seconds, then the controller terminated it
at 45.15 seconds total wall time. Observed RSS peaked at 1,187 MiB, below the
threshold. **Result: UNKNOWN due to wall timeout**, not memory exhaustion and
not UNSAT. The configured conflict budget was 100,000, but Kissat's wrapper
does not expose how many conflicts were reached before termination. Base 200
was exported only; no backend run was started for it.

The separate verifier again agreed with the exact bounds and digit lengths.
An additional 526 constant-division checks covered these two bases: for each,
tested the seven boundary values `0, b−1, b, b+1, b²−1, b², 65535` and 256
pseudorandom 16-bit values, using Python's `random.Random(20260925)` across
the bases in order. Every quotient/remainder and every emitted gate clause
passed. Results are in `direct-cnf-intermediate-validation.json` and
`direct-cnf-intermediate-breakdown.json` under `results/`.

The formula decomposition identifies a concrete new bottleneck:

| Base | Multiplication and bounds clauses | Radix-conversion clauses | Occupancy clauses |
|---|---:|---:|---:|
| 150 | 1,105,816 | 5,150,146 | 135,150 |
| 200 | 1,961,031 | 7,113,592 | 239,000 |

Repeated restoring division accounts for approximately 81% and 76% of the
clauses respectively. A specific next encoding hypothesis is to introduce
bounded output digit variables and constrain their values by Horner packing,
`accumulator ← b·accumulator + digit`, equating the final accumulators to the
already-built square and cube. Multiplication by a fixed base can use shifted
addition. This targets the measured conversion cost rather than increasing
the limits of the same search. The following experiment implements that idea.

```sh
python3 scripts/direct_cnf.py --base 150 --timeout 120 --rss-mb 1536 --output results/direct-cnf-base150.json
python3 scripts/direct_cnf.py --base 200 --timeout 120 --rss-mb 1536 --output results/direct-cnf-base200.json
PYTHONPATH=/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 150 --backend kissat404 --reuse-export results/direct-cnf-base150.json --solve-timeout 45 --conflicts 100000 --rss-mb 1536 --output results/direct-cnf-solve-base150.json
```

## Horner packing and base 192

Added `--digit-encoding horner` as a separate option; division remains the
default so earlier experiments remain reproducible. Output digits are unknown
binary vectors constrained to `0…b−1`, with nonzero leading digits. Their
Horner-packed values are equated bit by bit to the full square and cube.

Every prefix after `j` digits has an exact maximum `b^j−1`. Shifted additions
first compute each full intermediate value; any bits above that maximum's bit
width are explicitly constrained to zero before retaining the prefix. The
final equality also covers any extra bits of either the product or packed
value. There is no unchecked arithmetic wraparound.

Base 192 was selected because `192=128+64`: multiplication of a Horner
accumulator by the base requires one addition of two shifted copies. It also
has a larger candidate interval than base 128. Neither this structural
convenience nor heuristic solution abundance guarantees successful search.

Validation added 332 exhaustive small Horner-packing assignments to the prior
component checks. More substantially,
[`scripts/direct_cnf_horner_check.py`](../scripts/direct_cnf_horner_check.py)
enumerates every CNF solution by its input `n` in bases 2, 4, 5, 8, 9, 10, 12,
13, and 14, and compares those complete solution sets to independent integer
brute force over each exact candidate interval. Every set matched: only 69 in
base 10. All finite SAT enumeration runs concluded with UNSAT after blocking
their found inputs. No formal proof certificates were exported. Files:
`results/direct-cnf-horner-components.json`,
`results/direct-cnf-horner-full-validation.json`, and independent interval
checks in `results/direct-cnf-horner-independent-bounds.json`.

| Base / encoding | Variables | Clauses | Export time | Observed exporter RSS |
|---|---:|---:|---:|---:|
| 150 / division, previous | 1,733,228 | 6,391,112 | 7.97 s | 24.9 MiB |
| 150 / Horner | 770,178 | 3,305,745 | 3.20 s | 24.5 MiB |
| 192 / Horner | 863,982 | 3,558,251 | 3.47 s | 25.5 MiB |

In base 150, Horner packing reduces variables by about 56% and clauses by
about 48%. The complete base-192 file is 82,315,928 bytes. Both formulas
exported within the unchanged limits. Base 150 was used for the encoding
comparison only; this experiment's single larger-base solve was base 192.

Kissat loaded the base-192 formula in **1.881 seconds**, then returned
**UNKNOWN at its 100,000-conflict budget after 25.423 seconds solving**.
Total controller wall time was 27.56 seconds, and observed RSS peaked at
860.4 MiB, below the 1,536 MiB threshold. Its wall limit was 45 seconds. No new
candidate was returned. Detailed results are in
`results/direct-cnf-horner-base150.json`,
`results/direct-cnf-horner-base192.json`, and
`results/direct-cnf-horner-solve-base192.json`.

This changes the immediate obstacle: the selected nonbinary instance now
exports, loads, and performs a bounded SAT search within the memory limit.
The remaining problem is finding a satisfying assignment. Increasing the
expected number of solutions or shrinking the encoding has not yet supplied
one, and the conflict-budget result is not evidence of nonexistence.

```sh
python3 scripts/direct_cnf.py --validate --output results/direct-cnf-horner-components.json
PYTHONPATH=/private/tmp/nice-pysat python3 scripts/direct_cnf_horner_check.py > results/direct-cnf-horner-full-validation.json
python3 scripts/direct_cnf.py --base 150 --digit-encoding horner --output results/direct-cnf-horner-base150.json
python3 scripts/direct_cnf.py --base 192 --digit-encoding horner --output results/direct-cnf-horner-base192.json
PYTHONPATH=/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 192 --backend kissat404 --reuse-export results/direct-cnf-horner-base192.json --solve-timeout 45 --conflicts 100000 --rss-mb 1536 --output results/direct-cnf-horner-solve-base192.json
```
