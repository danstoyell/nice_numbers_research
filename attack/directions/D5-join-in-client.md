# D5. The overlap join in the public search client

## Goal

Measure how much of the overlap join's gain the public client
([wasabipesto/nice](https://github.com/wasabipesto/nice)) already captures
with its cross-end filter, and if a real gain remains, port the join into
the client's search path so the public fleet runs it.

## Why it matters

Contributing to the public search is the only action that could produce an
actual second nice number this decade, at about 0.1–0.3% odds
([reachability](../../critique/experiments.md)). The join is the only
algorithmic improvement this project found that is not already in production:
2.7–7× fewer operations on bases 25–40 exactly, and 3–25× at bases 57–64 by
the model ([algorithm report](../p1-algorithm/REPORT.md)). That would turn
finishing bases 57–60 from about a century into about two decades at the
fleet's current rate. It remains a lottery ticket, and the middle-digit
theory says nothing better exists in this family of methods, so this is the
ceiling for practical search, not a stepping stone.

## What is known

- The join: a list of good top prefixes and a list of good bottom residues
  that share o digits of n, hash-joined on the shared digits; each shared
  digit certifies four output digits instead of two. Exact C implementation
  and testbed in `attack/p1-algorithm/` (`overlap.c`, `run_testbed.py`,
  `cost_model.py`).
- The public client's filters: the CRT stride table (digit-sum residues mod
  b−1 with a 3-digit trailing filter), recursive leading-digit range pruning
  with Hall's condition, and a cross-end residue filter added in v3.4.1
  ([critique §3](../../critique/critique.md)). The comparison against these
  was never made; the critique flagged this as the main caveat on the join's
  numbers.
- Operation counting is the metric; wall-clock numbers in the report were
  disturbed by concurrent jobs.

## Plan

1. **Read the client's search path** (`common/src/msd_prefix_filter.rs`,
   `lsd_filter.rs`, `stride_filter.rs`, the cross-end filter) and write down
   exactly which output positions each stage certifies and at what cost per
   candidate.
2. **Instrument.** Either add operation counters to a local build of the
   client, or reimplement its pipeline's counting in `overlap.c`'s framework,
   and run both on the exact testbed (nice bases 25–40, twice-nice 15–22,
   thrice-nice 13–14) so all solutions are recovered and the counts are
   comparable.
3. **Decide.** If the client already captures most of the join's gain (say
   the join adds less than 2× at base 57 in the model after accounting for
   the cross-end filter), stop and record the comparison. Otherwise:
4. **Prototype** the join in Rust against the client's chunk interface
   (range of n in, results out), CPU first. Memory: the lists are partitioned
   by the shared digits, so each partition is small; check the fleet's
   memory limits. Then assess GPU feasibility: the join is a bucketed
   pairwise cross-check, which sort-based joins handle well; the client
   already has CUDA and CubeCL backends.
5. **Coordinate** with the client's maintainer through an issue before a
   pull request: correctness (every known solution recovered on the
   testbed), soundness proof from the algorithm report, and the measured
   operation counts.

## Deliverables

A comparison report (positions certified and operations per candidate, client
vs. join, on the exact testbed), the decision, and if positive a prototype
and an issue or pull request upstream.

## Stop rules

Stop after step 3 if the residual gain is under about 2× at base 57. Stop
after step 4 if memory or GPU constraints make the join slower in practice
than the client's current path.

## Pitfalls

Compare operations, not wall time. Re-verify every hit with the exact
verifier. The client had soundness bugs in the past (changelog v3.2.15,
v3.3.0); any new filter must come with the testbed check that finds all
known k-nice solutions.
