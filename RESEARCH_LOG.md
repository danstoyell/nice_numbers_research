# Research log

Started 2026-09-23; latest checkpoint 2026-09-25. Objective: find an exactly verified second square–cube pandigital, or prove that `(69, 10)` is the only solution across all integer bases.

**Status: open; neither requested result has been achieved.** Negative searches cover only their stated finite domains. Statistical estimates and incomplete solver runs do not establish uniqueness.

The definition is fixed: `n` is a positive integer, `b >= 2` is an integer, and the unpadded base-`b` digits of `n²` and `n³` together are exactly the multiset `{0, ..., b-1}`. Trivial signed variants do not count.

## Research tracks

| Track | Question | Files |
| --- | --- | --- |
| Exact obstructions | Can congruences exclude further infinite classes of bases or n? | `research/obstructions.md`, `scripts/obstructions.py` |
| Constructive identities | Can structured n and carry patterns generate a family or explicit solution? | `research/constructions.md`, `scripts/constructions.py` |
| Constraint search | Can a carry CSP, SMT solver, or guided local search overcome brute-force rarity? | `research/constraint-search.md`, `scripts/constraint_search.py` |
| Digit lifting and validation | Can exact prefix and suffix constraints prune a search efficiently? | `research/digit-lifting.md`, `scripts/verify.py` |
| Carry and sparsity constraints | Can carries or sparse inputs be ruled out structurally? | [Carry constraints](research/carry-constraints.md) |
| Transformations | Can quasi-nice numbers, near misses, or rational-power families yield a solution? | [Transformations](research/transformations.md) |
| Fixed edge constraints | Do finitely many leading/trailing checks suffice for uniqueness? | [Edge-constraint theorem](research/edge-constraints.md) |
| Analytic existence | Can exact counting or existing distribution theorems establish positivity? | [Literature applicability](research/analytic-existence.md), [exact counting and limitations](research/existence-counting.md) |
| Dedicated SAT backend | Can a different Boolean solver overcome Z3's bottleneck? | [SAT backend](research/sat-backend.md), [streamed Boolean circuits](research/direct-cnf.md) |
| Structured outputs | Can an explicitly pandigital word also split into a square and cube? | [Affine output permutations](research/structured-outputs.md) |
| Double stretching | Can roots with alternating zero positions exploit overlapping carries? | [Boundary obstruction and asymmetric survivors](research/double-stretch.md) |
| Repdigits | Can a repeated root digit survive the congruence and carry conditions? | [Prime-power-plus-one base theorem](research/repdigits.md) |

## Initial evidence

- Public project data reported complete listed chunks through base 54 and partial base 57; see `nice-numbers-research.md`. These are external reports, not independently replicated exhaustive computations.
- Known exact exclusions: `b = 1 mod 5` (digit count) and `b = 3 mod 4` (parity of digit sum).
- The base-45 example `330169542960890` has 44 of 45 distinct digits; it is not nice.
- `scripts/verify.py` provides an independent exact-integer verifier and inclusive candidate bounds. Every claimed solution must pass this verifier and a separate direct arithmetic check.

Experiments will record commands, seeds, bounds, timeouts, and conclusions under `results/` and the track notes. No external project submissions are part of this work.

## Results established so far

**Proved within this investigation, with derivations in the linked notes:**

- A nice number must have a carry in its raw cube expansion. Carry-free polynomial construction cannot work in any base. [Proof](research/constructions.md)
- If `n=(a*b^m+r)/d`, `r²<b^m`, and the square has at least `m` digits, a square with no repetitions requires `m-length_b(r²) <= d²` (use length zero when `r=0`). This excludes fixed-denominator, bounded-offset templates eventually. [Proof](research/constructions.md)
- Fixed input sparsity is impossible as the base grows, even when nonzero digits grow with the base. If `n` has top exponent `k` and `t` nonzero digits, necessarily `t(t+1) >= 4k/3`. Additional carry-mass and binary-weight bounds are recorded. [Proof](research/carry-constraints.md)
- The usual digit-sum congruence has no additional base exclusions beyond `b=3 mod4`; exact root counts are known prime-power by prime-power. [Derivation](research/obstructions.md)
- Any fixed number of suffix checks, even augmented by a fixed number of leading-digit checks and digit sum, leaves candidates in arbitrarily large bases. Explicit witnesses are saved; they are not nice. These particular filters cannot establish global uniqueness. [Suffix proof](research/obstructions.md), [both-edge proof](research/edge-constraints.md)
- A fixed integer has at most one base meeting the total-length requirement. Thus direct rebasing cannot repair a length-correct near miss. The natural `(n,b)->(n^t,b^t)` transformation preserves digit lengths and cannot produce a nice number in the larger base. [Proofs](research/transformations.md)
- No root `P(b^t)` with ordinary digit coefficients can be nice when `t>=3`. At `t=2`, mirrored endpoint coefficient pairs are also impossible, excluding every palindromic coefficient polynomial in that family. Asymmetric examples with entirely distinct squares demonstrate a limit to the proof. [Stretch theorem](research/transformations.md), [double-stretch theorem](research/double-stretch.md)
- No repdigit is nice in any base `b=p^e+1` for an odd prime p. In large bases of this class, the only remaining repeated-digit template is forced to repeat digit 60 between its square and cube; a small exhaustive check closes the remaining bases. This excludes repdigits only. [Proof and finite closure](research/repdigits.md)

**Finite experiments; scope must not be enlarged:**

- 19,252,100 structured family instances through base 1000; 133,350 passed length and digit-sum filters. Only `(69,10)` succeeded. Counts include duplicate family instances. [Raw results](results/constructions-b1000.json)
- Dense small-alphabet search explored 8,385,519 partial nodes. Some cases were exhaustive and others hit a node cap; consult the individual records before claiming exclusion. No solution. [Scope and results](research/transformations.md)
- Suffix lifting: 14,000 attempted paths across seven bases produced 4,588 completed distinct candidates; compared against 14,000 modularly conditioned random candidates. Average diversity improved from about 63% to 67%, still far from 100%. [Results](research/digit-lifting.md)
- Integer, carry, bit-vector, Karatsuba, and sorting encodings recovered 69 in validation. Larger-base runs returned UNKNOWN from timeout or memory limits. None of those runs proves nonexistence. [Solver report](research/constraint-search.md)
- 300,000 stochastic proposals compared uniform sampling with digit hill climbing in bases 64, 128, and 512; no significant practical improvement and no solution. [Solver report](research/constraint-search.md)
- A separate C++ search exhaustively checked bases 2 through 30 after exact necessary-condition pruning. Only 69/base10 was found. This reproduces a small known bound, not an advance beyond the public project's frontier. [Raw results](results/bounded-exhaustive.json)
- 470,835 lifted or repeated public near-miss instances into bases 57–400 produced 3,281 candidates passing length and digit sum; none was nice. [Scope](research/transformations.md)
- 13,349,176 affine permutations of the entire output word through base 500 all failed an exact modular square/cube compatibility test. This exhausts that output family only. [Scope](research/structured-outputs.md)
- A streamed Boolean encoder successfully generated the base-512 formula at about 41 MiB observed RSS, overcoming the previous export failure. The solver loaded it, then exceeded its 1.5 GiB threshold during early solving. Base 128 reached its conflict limit. Both outcomes are UNKNOWN. [Measurements and validation](research/direct-cnf.md)
- Exact counting formulations exposed specific dead ends: generic Fourier/Parseval bounds cannot establish positivity, and low-order digit-distribution evidence cannot justify the required rare-event estimate. Refined expected counts remain heuristic. [Derivations](research/existence-counting.md)

## Validation and reproducibility

Run `python3 -m unittest discover -s tests` for the independent verifier's tests.
Two independently implemented interval formulas agree for bases 2 through
600. All six saved SAT answers at the first cross-check were independently
verified; all were 69/base10. [Cross-check record](results/cross-validation.json)
Solver-circuit checks include exact random products, symbolic equivalence,
and digit-sorting cases. [Circuit checks](results/constraint-search-circuit-validation.json)
Each track includes its own command lines and raw result paths. A timeout,
node cap, or resource failure is always an incomplete experiment.

## Current direction

Focus on information about the entire square/cube pair: full constraint
solving, exact counting, or constructions with dense, irregular carries.
Do not spend large budgets repeating unchanged random sampling, fixed-depth
edge filters, or the already-excluded sparse and carry-free templates.
The direct SAT exporter now works at base 512, but solver memory and search
difficulty remain unresolved. Intermediate nonbinary bases are the next
bounded solver experiment. The repdigit and stretching proofs eliminate
specific construction families; they do not approach a complete exhaustion
of all possible roots. Neither requested result has yet been obtained.
