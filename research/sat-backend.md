# Dedicated SAT backends and occupancy encoding

Updated September 25, 2026. **No second nice number found; no new base ruled out.**

Question: were the previous failures specific to Z3's SAT backend or its
all-different encoding? This experiment separates exact circuit construction
from solving, exports propositional CNF, then starts a fresh CaDiCaL or Kissat
process. The script is [`scripts/sat_backend.py`](../scripts/sat_backend.py).
It imports the previously validated Karatsuba circuit without modifying the
older search script.

## Setup and bounds

Installed `python-sat 1.9.dev15` and its small `six` dependency only in
`/private/tmp/nice-pysat`. The wheel provides CaDiCaL 3.0.0 and Kissat 4.0.4;
their supported methods differ, so the wrapper avoids unavailable Kissat
statistics queries. These are local installations, not global dependencies.
[PySAT solver API](https://pysathq.github.io/docs/html/api/solvers.html).

Each export stage and solve stage had a 60-second wall limit. Each backend had
a 100,000-conflict budget. A parent process polled worker resident memory every
0.25 seconds and terminated it above 1,536 MiB. This is a monitored threshold,
not an instantaneous allocation cap: sampled peaks can overshoot, and very
short workers can finish between samples. CaDiCaL seed was `20260924`; Kissat
used its default seed. Z3 was `5.1.0`.

The sandbox blocks `ps`; running the monitored experiment outside that sandbox
was approved. The controller inspects only its own worker. The old Z3 solver's
`timeout_ms` field appears in exported configuration metadata because the
model builder is reused; no Z3 `check()` runs in this stage. Actual export
limits are the parent process's stated wall and RSS limits.

## Export correctness issue caught by validation

The naive pipeline `simplify → bit-blast → tseitin-cnf` left 45 residual
bit-vector equalities in the small base-10 example. `Goal.dimacs()` treated
those relations as free Boolean atoms, producing a relaxation. CaDiCaL found
an apparent model reconstructing `n=81`, which the independent exact-digit
check immediately rejected.

The fix is to use `simplify(blast_distinct=True)` before bit blasting and
**require `is-propositional` on the final goal** before exporting. Named Boolean
variables encode every bit of `n`; their DIMACS identifiers are saved so a SAT
model reconstructs an exact integer. Corrected runs recovered `69`, with the
expected square and cube digit arrays, in both backends. The invalid attempt is
retained as `results/sat-backend-base10-invalidcnf.json`, explicitly marked as
diagnostic and invalid. It is not evidence about any candidate's niceness.

## Corrected pairwise-uniqueness results

| Base | CNF variables | CNF clauses | Backend | Result |
|---|---:|---:|---|---|
| 10 | 1,268 | 5,971 | CaDiCaL 3 | SAT, `n=69`, independently valid; 0.017 s solving |
| 10 | 1,268 | 5,971 | Kissat 4 | SAT, `n=69`, independently valid; 0.026 s solving |
| 128 | 265,886 | 1,340,407 | CaDiCaL 3 | UNKNOWN at conflict budget; 19.97 s solving |
| 128 | 265,886 | 1,340,407 | Kissat 4 | UNKNOWN at conflict budget; 14.90 s solving |
| 512 | Not completed | Not completed | Export stage | Stopped by RSS monitor before backend solving |

The base-128 CNF is 37,045,232 bytes and took 1.84 seconds to export. Its
CaDiCaL run reported 100,001 conflicts, 1,104,013 decisions, and 94,242,283
propagations. The one-conflict excess reflects the backend's budget semantics.
Observed backend RSS was about 774 MiB for CaDiCaL and 418 MiB for Kissat.
Kissat reused the exact same exported file. Its Python wrapper does not expose
detailed conflict statistics. Base-512 export was terminated at an observed
1,619 MiB; no SAT conclusion was obtained.

Dedicated backends therefore reach substantive search with lower resident
memory than the previous monolithic Z3 runs, but changing backends did not
produce a solution or an UNSAT result in the unsearched bases.

## Shared occupancy decoder

Since there are exactly `b` output digits, requiring every value `0…b−1` to
occur at least once is equivalent to requiring a permutation: `b` different
required values fill all `b` positions. The code builds a shared binary decoder
for each position. Each prefix node is the conjunction of its parent's prefix
and the next digit bit. Its equivalence uses three CNF clauses. One final
coverage clause per value requires at least one corresponding leaf to be true.
This removes pairwise digit comparisons and shares common prefixes explicitly.

| Base | CNF variables | CNF clauses | CaDiCaL result |
|---|---:|---:|---|
| 4 | 62 | 234 | UNSAT, as expected for this already-known small case |
| 10 | 1,263 | 5,611 | SAT, `n=69`, independently valid |
| 128 | 234,008 | 1,138,341 | UNKNOWN at 100,000-conflict budget; 31.56 s solving |
| 512 | Not completed | Not completed | Arithmetic export hit RSS threshold before decoder construction |

In base 128 the decoder reduces variables by about 12% and clauses by 15%
against the pairwise export. It used about 732 MiB observed backend RSS.
Nevertheless, its 100,001 conflicts took longer and did not decide the problem.
The arithmetic and bit-binding portion alone contains 201,752 variables and
1,041,445 clauses; adding the decoder supplies the remainder. In base 512,
that arithmetic portion exceeded the threshold even with the uniqueness
constraint removed. This isolates the main remaining export bottleneck:
large multiplication circuits and their representation in Z3, not just
pairwise all-different constraints.

These are bounded implementation comparisons. UNKNOWN means neither existence
nor nonexistence was established. No UNSAT proof certificate was exported.

## Reproduction and artifacts

```sh
python3 -m pip install --target /private/tmp/nice-pysat --no-cache-dir python-sat==1.9.dev15
PYTHONPATH=/private/tmp/nice-z3:/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 10 --output results/sat-backend-base10.json
PYTHONPATH=/private/tmp/nice-z3:/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 128 --output results/sat-backend-base128.json
PYTHONPATH=/private/tmp/nice-z3:/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 128 --backend kissat404 --reuse-export results/sat-backend-base128.json --output results/sat-backend-kissat-base128.json
PYTHONPATH=/private/tmp/nice-z3:/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 128 --distinct occupancy --output results/sat-backend-occupancy-base128.json
PYTHONPATH=/private/tmp/nice-z3:/private/tmp/nice-pysat python3 scripts/sat_backend.py --base 512 --distinct occupancy --output results/sat-backend-occupancy-base512.json
```

The earlier Z3 installation in `/private/tmp/nice-z3` is also required. Each
result JSON in `results/sat-backend*.json` records configuration, timings,
measured memory, export sizes, named input bits, and any reconstructed candidate.
CNF files and worker logs remain at the temporary paths recorded in those JSON
files; they can be regenerated if the operating system clears `/private/tmp`.

A distinct next engineering hypothesis would be a streaming Boolean circuit
writer that avoids Z3's large intermediate ASTs. Simply changing the SAT
backend again would not address the demonstrated base-512 export bottleneck.
