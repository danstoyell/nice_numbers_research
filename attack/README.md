# Parallel attack, started 2026-09-26

Goal: a second nice number (explicit, or proved to exist) or a proof that 69
in base 10 is the only one. Nothing else counts.

Five hypotheses run in parallel, one folder each. Each folder gets a
`REPORT.md` with the verdict, the numbers behind it, and code.

| Folder | Path | Hypothesis | Killed if |
|---|---|---|---|
| `p1-structure/` | 1 | A structured family of (n, b) boosts the chance of niceness by about e^(cb), like the families behind the Hadamard-668 and rank-31 records | Family size × boost stays ≪ 1 at every base ≤ 1000 |
| `p1-algorithm/` | 1 | An algorithm certifies middle digits for many candidates at once, beating edge enumeration | No gain over the edge rate on the k-nice testbed |
| `p3-analogues/` | 3 | Exact twice- and thrice-nice counts at rarer bases fall below the random model | Counts match the model |
| `p3-obstruction/` | 3 | The deficiency-2 shortfall has an arithmetic cause that could scale to a nonexistence proof | Shortfall explained or gone |
| `p2-existence/` | 2 | Some very large base provably contains a nice number | No approach closes its exponent bookkeeping |
