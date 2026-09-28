# H5: does SAT find a first witness faster on satisfiable instances?

2026-09-28. Hypothesis H5 of [NEXT_HYPOTHESES.md](../NEXT_HYPOTHESES.md): on
naturally satisfiable, unplanted K-nice instances, a SAT solver's time to the
first verified witness scales better than exact enumeration's, even though
SAT lost by 10⁴–10⁵ on the small ordinary bases, which have no solutions.

## Verdict: killed

- **The first-witness job is lost by the same factor as the empty-box job.**
  On thrice-nice base 9 (63,778 roots, 7 witnesses) CaDiCaL needs 85–114 s to
  produce a first verified witness; the stride-filtered enumerator needs
  0.2 ms on average from six different start points. On thrice-nice base 10
  (535,841 roots, 10 witnesses) one variant took 285 s and the other found
  nothing in 300 s, against 2 ms. The ratio is about 10⁵.
- **From twice-nice base 14 on, the solver produced no witness at all** within
  its wall limit: 600 s on both variants at twice-14 (716,121 roots), 400 s at
  twice-15 (6.8×10⁶ roots) and at thrice-13 (1.2×10⁸ roots, 16 witnesses),
  where the enumerator needs 3 ms, 0.08 s and 0.07 s. The gap therefore
  widens with the base; the lower bounds on the ratio in the table are the
  wall limits divided by the enumerator's time. Every witness the solver did
  produce was re-verified exactly and lies in the interval.
- **Nothing was planted.** The solver sees the exact interval, the arithmetic
  and the multiplicity constraint only. The randomized variants rename the
  variables and shuffle the clauses; the enumerator starts at the interval's
  low end and at five random points, wrapping around, and stops at its first
  hit.
- **Why.** A CDCL solver on a multiplier circuit propagates bit by bit; a
  witness sits at density about 10⁻⁵–10⁻⁷ among roots, and the solver has no
  digit-level locality to exploit that the enumerator's stride filter does
  not already exploit at a cost of nanoseconds per candidate. The ordinary
  nice-number instances at bases ≥ 57 are 10¹⁵ times sparser again.

The hypothesis's continue rule ("a reproducible advantage that increases with
problem size and survives a held-out case") fails at the first case. Do not
precede another attempt with an encoding rewrite; the encoding is not the
bottleneck.

## Method

`knice_sat.py` reuses `scripts/direct_cnf.py`'s validated `Circuit` (exact
interval, Karatsuba products, Horner digit extraction, occupancy decoder). The
one change multiplicity K needs is the constraint "each digit value occurs at
least K times", a sequential-counter cardinality constraint from PySAT in
place of a single clause (the interval fixes the total length K·b, so "at
least K" is "exactly K"). Each solve runs in a child process under a wall
limit; the first model is decoded to n and checked with the exact Python
verifier.

`first_hit.c` is the baseline: it walks the interval upward from a start
point, visits only residues modulo b(b−1) that pass the digit-sum and
distinct-last-digit filters, and stops at the first K-nice root, reporting
full checks and wall time. Six starts per case: the low end and five random
points.

Runs: thrice-9 and thrice-10 with two variants at a 300 s limit; twice-14 with
two variants at 600 s; twice-15 and thrice-13 with one variant at 400 s (the
campaign's remaining 600 s solves were stopped as redundant once these had
timed out). About 55 solver-minutes in total.

Reproduce:

```sh
clang -O3 -march=native -o first_hit first_hit.c
./run_h5.sh                     # baselines, then twice-14/15 and thrice-13
python3 knice_sat.py --cases 3:9 3:10 --variants 2 --limit 300
python3 knice_sat.py --cases 2:15 --variants 1 --limit 400
python3 knice_sat.py --cases 3:13 --variants 1 --limit 400
python3 summarize.py
```

## Results

<!-- TABLES -->
| Case | Roots N | Witnesses | CNF variables / clauses | SAT: result per variant | SAT: seconds to first witness | Enumerator: full checks to first hit (mean of 6 starts) | Enumerator: seconds (mean, max) | SAT / enumerator (seconds) |
|---|---:|---:|---|---|---|---:|---|---:|
| thrice-9 | 63,778 | 7 | 7,610 / 29,088 | SAT, SAT | 114, 85 | 2,250 | 0.0002, 0.0004 | 495,781 |
| thrice-10 | 535,841 | 10 | 9,572 / 36,812 | SAT, TIMEOUT | 285, 300+ | 20,434 | 0.0020, 0.0040 | 147,513+ |
| twice-14 | 716,121 | 1 | 12,391 / 49,595 | TIMEOUT, TIMEOUT | 600+, 600+ | 25,576 | 0.0028, 0.0042 | 215,456+ |
| twice-15 | 6,771,952 | 1 | 17,356 / 71,377 | TIMEOUT | 400+ | 739,500 | 0.0782, 0.1416 | 5,116+ |
| twice-16 | 25,498,720 | 1 | — | not run | — | 2,577,481 | 0.2841, 0.4295 | — |
| thrice-13 | 120,679,425 | 16 | 22,406 / 90,549 | TIMEOUT | 400+ | 426,234 | 0.0686, 0.1362 | 5,828+ |
<!-- /TABLES -->

"+" marks a run killed at its wall limit (no witness within the limit).

## Files

- `knice_sat.py`, `first_hit.c`, `run_h5.sh`; `results/knice_sat.jsonl`
  (one line per solve), `results/first_hit.jsonl` (one line per start);
  `summarize.py`.
