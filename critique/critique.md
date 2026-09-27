# Critique of the nice-number research program

Reviewed 2026-09-26, covering `nice-numbers-research.md`, `RESEARCH_LOG.md`, all
eighteen notes in `research/`, their scripts, and their saved results, as they
stood on that date. Supporting computations are in
[experiments.md](experiments.md); recommendations are in
[research-directions.md](research-directions.md).

**The standard applied throughout:** only two outcomes count as success, a
second nice number (found, or proved to exist) or a proof that 69 in base 10
is the only one. Work is judged by whether it could produce either one.
Verification, write-ups, heuristic refinement, and speedups that leave the
cost astronomically out of reach are not progress by this standard.

## Verdict

**The mathematics is careful and, as far as I checked, correct. The strategy
is the problem.** The program ran as a breadth-first sweep over twelve
tracks (eighteen notes) without first asking, of any track, how likely it was
to change the answer to either stated question. Measured against those
questions, nearly all of the effort went into three categories that could not
move them:

1. **Excluding families of negligible size.** Repdigits alone produced five
   notes (one of them an audit) and four scripts, and were still growing
   during this review. A repdigit family has at
   most `b-1` members per base; the bases beyond the frontier have 10¹⁹ to
   10²⁷⁷ candidates. No number of such exclusions adds up to a uniqueness
   proof.
2. **SAT and SMT at bases 128 to 512** (and now 150 and 192), the largest
   engineering and compute sink. The encoding was never timed on a base whose
   answer is known. When I did that, solve time grew almost as fast as the
   number of candidates, at **over a millisecond per candidate, 10⁴–10⁵ times
   slower than a naive enumerator** ([experiments §4](experiments.md#4-sat-scaling-on-bases-whose-answer-is-known)).
   The UNKNOWN results at large bases therefore carry no information.
3. **Transformations with no mechanism**: near-miss lifts, affine output
   permutations, quasi-nice seed transforms. No reason was given why these
   families should beat the random model, and none did.

The program never did the calculation that decides strategy: what fraction of
the chance of a second nice number lies within reach, and at what cost. Using
the project's own conditional model (which I reproduced to 10⁻¹¹ in log₁₀):

| Region | Expected nice numbers | Cost at today's public throughput |
|---|---:|---|
| All bases searched so far (12–54, 12% of 57) | 0.054 | done: finding none was the likely outcome (≈95%) |
| Remainder of 57, plus 58 and 60 | 0.0019 | ~100 years |
| Everything through base 80 | 0.013 | ~10¹¹ years |
| Everything through base 118 (where the odds pass 50%) | 0.96 | ~10²⁹ years |

Base 10 alone had an expectation of 0.050, so 69 was roughly a 1-in-20 event
under the model. That is unremarkable given selection: the question exists
only because base 10 happened to have one.

It also never engaged with the state of the art. The public client already
implements, in production, the ideas the digit-lifting and edge tracks treat as
open ([§3](#3-missed-prior-art-and-duplicated-effort)). And although the log
correctly says the public results were "not independently replicated", nobody
replicated them. Doing it for bases 10–35 took under ten minutes on a laptop
(the histograms match exactly), and it turned up a small, genuine gap: the
public intervals omit one valid candidate in every base ≡ 2, 3, 4 (mod 5).
None of the 26 omitted candidates is nice
([experiments §5](experiments.md#5-a-gap-in-the-public-coverage-record)).

### What to keep doing

These habits are better than most research of this kind and should survive
any change of direction:

- **Scope discipline.** Every note separates proof from experiment and states
  what a negative result does not show.
- **Validation of every encoding against known answers.** This caught a real
  bug: the invalid CNF relaxation that "found" n = 81.
- **Honest recording of UNKNOWN, timeout, and resource failures**, with seeds,
  limits, and commands.
- **Independent audits of proofs**, as in the repdigit audit.
- **Correctly identifying analytic dead ends**
  ([existence-counting.md](../research/existence-counting.md)).

The recommendations below redirect this machinery; they do not replace it.

## 1. The two goals are not symmetric, and neither is reachable by the chosen means

### A uniqueness proof is almost certainly impossible, because uniqueness is almost certainly false

The model predicts an expected count that crosses 1 at base 122 and reaches
10⁷ at base 200, 10²⁰ at base 300, and 10⁵⁷ at base 512. For 69 to be the
only nice number, the model would have to be wrong by more than twenty orders
of magnitude at base 300.

The model is not an untested assumption; it can be checked where data exist.

- **The near-miss tail matches.** The public detailed histograms cover every
  candidate in bases 10–48, and I recomputed bases 10–35 exactly. Their far
  tail, candidates missing 3 to 6 digits (counts from 3×10⁴ to 8×10⁸), agrees
  with an "exact edge digits, random middle digits" model to within 0.6%
  ([experiments §2](experiments.md#2-the-random-digit-heuristic-against-the-public-histograms)).
  The one discrepancy, a 13% shortfall at exactly 2 missing digits (about 3σ),
  shows no trend with the base. It is worth watching, but nothing in it
  suggests a suppression that grows exponentially.
- **Exact hits match.** Consider the analogues where n² and n³ together use
  every digit exactly *twice* or *three times*. They have the same exponents
  and carry structure, and the model predicts solutions at bases small enough
  to search exhaustively. The solutions exist, close to the predicted rate: <!-- ANALOGUE_SENTENCE -->24 twice-nice numbers through base 22 against 20.7 predicted, and 312 thrice-nice numbers through base 16 against 339.9 predicted<!-- /ANALOGUE_SENTENCE -->
  ([experiments §3](experiments.md#3-exact-hits-in-analogues-k-nice-numbers)).
  An example is 6534 in base 10: 6534² = 42693156 and 6534³ = 278957081304.

The tools the program used to seek an obstruction cannot, in principle,
produce one:

- **Fixed-depth edge information is provably insufficient.** The project's
  own theorems show this ([obstructions §4](../research/obstructions.md),
  [edge-constraints](../research/edge-constraints.md)).
- **Modular information adds nothing.** For a modulus coprime to b, the
  residues that a pandigital split of the digits can realize are exactly those
  allowed by the digit-sum congruence, and nothing else. I checked this
  exhaustively in base 10 for every such modulus up to 99; the argument is
  sketched in [research-directions, Path 3](research-directions.md#why-modular-arguments-cannot-work-no-hidden-congruences).
  Moduli sharing factors with b see only the trailing digits, and suffix
  distinctness is already covered by the edge theorems. So there is no hidden
  congruence left to find. The obstructions track guessed as much for
  alternating sums; this settles it for every modulus.
- **Family exclusions cannot accumulate.** Each excluded family (carry-free,
  fixed sparsity, fixed denominator, stretched, double-stretched with mirrored
  ends, repdigits, affine outputs) has measure zero among candidates.

### A second nice number almost certainly exists, and is almost certainly out of reach

At the frontier, even an idealized search that exploits every leading and
trailing digit needs 10¹⁹·⁷ checks per expected solution at base 57, 10³⁶·⁵
at base 100, and 10⁴³ near base 118. The public network covers roughly
5×10¹⁶ integers of range per day in nice-only mode. The reachable probability
over the next decade is on the order of 0.1–0.2%. SAT does not change this: it
is slower than enumeration where the answer is known.

The research log is right that "neither requested result has yet been
obtained". It does not say that, on the evidence available, neither is likely
to be obtained by any continuation of the current tracks. That sentence should
be in the log.

## 2. Specific weaknesses

### 2.1 Solution count was used where solution density matters

[direct-cnf.md](../research/direct-cnf.md) chose bases 150 and 200 because
"the project's conditional random-digit heuristic expects more solutions", and
[constraint-search.md](../research/constraint-search.md) calls base 512
"interesting" because it expects 10⁵⁷ solutions. For any search method, what
matters is solutions per unit of search space. At base 150 that is about
10⁻⁶³, and at base 512 about 10⁻²²⁰. For a CDCL solver on a multiplication
circuit, that is equivalent to no solutions. Density falls roughly like e^−b,
so the cheapest place to look is always the smallest unsearched base (57,
then 58, then 60).

### 2.2 No calibration before scaling up

Every SAT run at an unsearched base ended UNKNOWN, by timeout, memory, or
conflict budget. The notes acknowledge that UNKNOWN proves nothing, then
schedule the next larger or differently-encoded run: Karatsuba, sorting
networks, occupancy decoders, streamed CNF, Horner packing, base 192. The
missing step was a single table of solve time against base on bases 12–25,
where brute force is instantaneous. That table (§4 of the experiments) would
have ended the track on day one.

### 2.3 Diminishing-return momentum in the family track

The repdigit sequence ([repdigits](../research/repdigits.md),
[composite bases](../research/repdigit-composite-bases.md),
[odd bases](../research/repdigit-odd-bases.md),
[five-sixths](../research/repdigit-five-sixths.md),
[audit](../research/repdigit-audit.md)) grew on 2026-09-25 and 2026-09-26 into
residual templates, finite closures to base 2000, and certificates. The latest
note, written while this review was under way, closes one template for bases
of at least 1,000,000 with a six-case rational certificate. The work
is rigorous. Its relevance to either goal was zero from the start, and nothing
in the notes flags that. The same pattern shows in stretch → double stretch →
asymmetric probes.

### 2.4 Randomized experiments where exact ones were cheap

Digit lifting sampled 2,000 random paths per base, capped at 64 digits per
step, and reported mean diversity. The informative experiment was an exact
count, over whole bases, of how many candidates survive edge filters of each
depth. The public project has that measurement (its `filter_effectiveness`
script), and it is what determines search cost.

### 2.5 External data used but not checked

The log cites the public frontier as external and unreplicated, which is
correct, but never tests it, even though the public changelog records three
soundness bugs that silently dropped candidates (quoted in §3).

Judged by the goal, the gap turns out not to matter. A re-check could produce
a solution only if a bug had hidden one, and:

- bases ≤ 48 were counted exhaustively in detailed mode, which the bugs did
  not affect;
- I re-verified bases 10–35 exactly, and checked the 26 candidates the stored
  intervals omit;
- bases 49–54 carry only 0.003 expected nice numbers under the model.

So verification is not a route to a second nice number. The lesson is about
method: coverage claims should be checked before they are relied on.

### 2.6 Documentation does not rank results

`RESEARCH_LOG.md` lists "Results established" with equal weight: a theorem that
kills all fixed-depth local filters sits beside the double-stretch mirrored-
endpoint lemma. A reader cannot tell which results bear on the goals. There is
no single "current best understanding" paragraph that states the probability
picture.

## 3. Missed prior art and duplicated effort

The public client ([wasabipesto/nice](https://github.com/wasabipesto/nice))
already does the following in production:

- **A CRT stride table** combining the digit-sum residues mod `b-1` with a
  3-digit trailing filter mod `b³`, iterating only valid residues
  ([stride_filter.rs](https://github.com/wasabipesto/nice/blob/main/common/src/stride_filter.rs),
  [lsd_filter.rs](https://github.com/wasabipesto/nice/blob/main/common/src/lsd_filter.rs)).
  This supersedes the research's suffix-filter and CRT observations as a
  search tool.
- **Recursive leading-digit range pruning.** It gives each near-fixed output
  position a conservative interval of possible digits and skips a range when
  Hall's condition fails, recursing down to ranges of about 8,000
  ([msd_prefix_filter.rs](https://github.com/wasabipesto/nice/blob/main/common/src/msd_prefix_filter.rs);
  changelog v3.4.0–v3.4.1).
- **A cross-end residue filter.** Digits certified at the top for a whole range
  exclude stride residues whose trailing digits reuse them (v3.4.1). This is
  the "both ends" search that [digit-lifting.md](../research/digit-lifting.md)
  and the edge notes point toward.
- **A least-significant-first backtracking search**, i.e. digit lifting, as an
  explored script
  ([radix_tree_search.rs](https://github.com/wasabipesto/nice/blob/main/scripts/radix_tree_search.rs)).
- **GPU kernels** (CUDA, CubeCL, Vulkan) and a Vast.ai fleet. On 2026-09-26 the
  fleet covered about 5×10¹⁶ of range in nice-only mode
  ([search-rate data](https://data.nicenumbers.net/cache_search_rate_daily?order=date.asc)).

The same changelog records soundness bugs that make independent checking
worthwhile
([CHANGELOG.md](https://github.com/wasabipesto/nice/blob/main/CHANGELOG.md)):

- v3.3.0: "Remove an unsound MSD x LSD cross-check, which could silently skip
  valid nice numbers searched in niceonly mode by the CPU client."
- v3.2.15: "valid nice numbers would be silently skipped in some bases between
  10-25 due to an invalid prefilter configuration" (GPU; the entry says live
  fields were unaffected).
- v3.3.0: an off-by-one "which dropped one trailing candidate per base where
  base % 5 ∈ {2,3,4}". The stored public intervals still stop one short. I
  checked those 26 candidates directly and none is nice.

## 4. Track-by-track assessment

"Correct" means I found no error in the parts I checked (listed in §6).
"Bearing" means the plausible effect on either goal.

| Track | What it established | Correct | Bearing | Recommendation |
|---|---|---|---|---|
| Exact obstructions (length, digit sum, last digit) | Complete solution of the digit-sum congruence; exact residue counts | Yes | Useful for search strides; no new exclusions exist | Stop seeking more congruences (none exist; research-directions, Path 3) |
| Fixed-depth suffix / edge theorems | No fixed-depth edge test can prove uniqueness | Yes | **High (negative)**: closes a whole approach | Keep in view: a uniqueness proof must use information these cannot |
| Carry-free impossibility, sparsity bound, carry mass | No carry-free construction; ≥ ~√(4k/3) nonzero input digits | Yes | Low: excludes constructions nobody expected to work | Stop |
| Fixed-denominator bound, growing denominators | Fixed-denominator families eventually repeat a digit | Yes | Low | Stop |
| Stretch / double stretch | Stretch ≥ 3 impossible; mirrored double stretch impossible | Yes | Negligible | Stop |
| Repdigits (five notes) | Prime-power-plus-one bases excluded; residual templates | Key steps yes (audit agrees) | Negligible (≤ b candidates per base) | Stop |
| Structured outputs (affine words) | No affine output word through base 500 | Yes | Negligible | Stop |
| Near-miss lifts, quasi-nice transforms | Nothing found | Yes | None; no mechanism | Stop |
| Digit lifting, local search | Edge forcing helps only modestly; local search fails | Yes | Superseded by the public client | Stop |
| Z3 / SAT / CNF (four notes) | Valid encodings; UNKNOWN everywhere that matters | Encodings validated | **None**: slower than enumeration (§4 of experiments) | Stop |
| Existence counting, analytic | Parseval and uniform-error routes cannot prove positivity | Yes | Correctly identifies a dead end | Stop; the dead end is established |
| Bounded exhaustive (≤ base 30) | Reproduces a trivial range | Yes | None | Stop; bases ≤ 48 are covered by detailed-mode counts, and 10–35 are now re-verified |

## 5. Smaller corrections to existing notes

- [constraint-search.md](../research/constraint-search.md): "Base 512 remains
  interesting under the random-digit heuristic" should add that the solution
  density there is about 10⁻²²⁰, far worse than at any smaller base.
- [direct-cnf.md](../research/direct-cnf.md): the base-selection rationale
  ("bases where the ... heuristic expects more solutions") is the count/density
  confusion of §2.1. (Its harness, which uses conflict budgets and process
  termination, is sound. I mention this because my own first harness relied
  on PySAT's `interrupt()`, which the CaDiCaL 1.9.5 binding silently does not
  implement.)
- [RESEARCH_LOG.md](../RESEARCH_LOG.md), "Current direction": "Intermediate
  nonbinary bases are the next bounded solver experiment" is contradicted by
  the scaling data and should be withdrawn.
- [RESEARCH_LOG.md](../RESEARCH_LOG.md) and
  [nice-numbers-research.md](../nice-numbers-research.md): "complete listed
  chunks through base 54" is accurate about the listed chunks, but the listed
  intervals omit one endpoint per base ≡ 2, 3, 4 (mod 5). Those endpoints are
  now checked; see [experiments §5](experiments.md#5-a-gap-in-the-public-coverage-record).
- [existence-counting.md](../research/existence-counting.md): its refined-model
  table is right, but it stops short of the conclusion the table implies (the
  reachability table in the verdict above). That conclusion belongs in the note.

## 6. What I checked, and what I did not

**Rechecked by hand**, with no error found:

- the length intervals and base-class exclusions;
- the complete digit-sum root counts, including the 2-adic cases;
- the last-digit collision count R(b);
- the carry-free cube proof (Frobenius step and the endpoint argument);
- the carry bounds and the `2A+{0,1,2}` support argument behind `t(t+1) ≥ 4k/3`;
- the binary-popcount table entry for base 64;
- the fixed-denominator carry-state argument;
- the one-base-per-integer monotonicity argument;
- the small-alphabet prime-plus-one corollary;
- the 0.671·b lifting estimate;
- the base-512 bit arithmetic;
- the refined expected counts (reproduced independently).

**Checked computationally**: the expected counts, the public histograms for
bases 10–35 (exact), the omitted endpoints, and that the CNF encoding answers
correctly on small bases.

**Read but not re-derived line by line**: the edge-constraint construction
bounds, the double-stretch carry indices, the odd-base repdigit reduction, and
the five-sixths repdigit certificate. The odd-base reduction is marked
"awaiting a separate full audit" by its own authors.

## Sources

- Nice Numbers project and data API: [nicenumbers.net](https://nicenumbers.net/),
  [bases](https://data.nicenumbers.net/bases?select=*&order=id.asc),
  [chunks](https://data.nicenumbers.net/chunks?select=id,base_id,range_start,range_end,range_size,minimum_cl&base_id=gte.35&order=id.asc),
  [daily search rate](https://data.nicenumbers.net/cache_search_rate_daily?order=date.asc)
  (all fetched 2026-09-26; dated copies in `critique/results/`).
- Search client source: [repository](https://github.com/wasabipesto/nice),
  [CHANGELOG.md](https://github.com/wasabipesto/nice/blob/main/CHANGELOG.md),
  [msd_prefix_filter.rs](https://github.com/wasabipesto/nice/blob/main/common/src/msd_prefix_filter.rs),
  [lsd_filter.rs](https://github.com/wasabipesto/nice/blob/main/common/src/lsd_filter.rs),
  [stride_filter.rs](https://github.com/wasabipesto/nice/blob/main/common/src/stride_filter.rs),
  [radix_tree_search.rs](https://github.com/wasabipesto/nice/blob/main/scripts/radix_tree_search.rs).
- Original problem and heuristic: [Is 69 unique?](https://beautifulthorns.wixsite.com/home/post/is-69-unique),
  [Progress update](https://beautifulthorns.wixsite.com/home/post/progress-update-on-the-search-for-nice-numbers),
  [Manifold market](https://manifold.markets/Conflux/will-i-learn-of-a-nice-number-besid).
- PySAT solver API (interrupt support varies by backend):
  [pysathq.github.io](https://pysathq.github.io/docs/html/api/solvers.html).
