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
  (535,841 roots, 10 witnesses): 285 s against 2 ms. The ratio is 10⁵ and it
  is not shrinking with the base.
- **Larger cases are recorded as they finished** (600 s wall limit per solve,
  two randomized variants each); see the table. Every witness the solver
  produced was re-verified exactly and lies in the interval.
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

Reproduce:

```sh
clang -O3 -march=native -o first_hit first_hit.c
./run_h5.sh                     # baselines, then the SAT runs (up to an hour)
python3 knice_sat.py --cases 3:9 3:10 --variants 2 --limit 300
python3 summarize.py
```

## Results

<!-- TABLES -->
<!-- /TABLES -->

"+" marks a run killed at its wall limit (no witness within the limit).

## Files

- `knice_sat.py`, `first_hit.c`, `run_h5.sh`; `results/knice_sat.jsonl`
  (one line per solve), `results/first_hit.jsonl` (one line per start);
  `summarize.py`.
