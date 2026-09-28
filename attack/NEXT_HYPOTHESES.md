# Five intermediate hypotheses worth testing next

**Status, 2026-09-28.** H1 killed ([h1-domains](h1-domains/REPORT.md)),
H2 killed ([h2-sampler](h2-sampler/REPORT.md)), H3 confirmed through base 18
for all M ≤ b² and proved for M = b+1 in every base
([h3-covering](h3-covering/REPORT.md)), H5 killed
([h5-sat-witness](h5-sat-witness/REPORT.md)), H4 not attempted. The text
below is the original proposal, unchanged.

2026-09-27. Synthesis of the earlier `research/` work, the independent
`critique/`, and the newer `attack/` results. This is a research proposal;
the five hypotheses below have **not** been established or tested in this
review. No new search campaign or C rewrite was undertaken.

## Recommendation

Put the main effort into **H1: rejecting whole batches using middle-digit
possibilities**, followed by **H2: sampling through progressively stronger
conditions**. These address the part of the problem that existing searches
do not handle cheaply. For a proof-oriented task, start with **H3: a precise
residue-covering theorem**. H4 and H5 are bounded diagnostic projects: each
should either produce a useful certificate or close a specific remaining
question, without becoming another long campaign.

| Priority | Hypothesis | First useful result | Tractability of first step | Connection to the goal |
|---|---|---|---|---|
| 1 | H1. Middle-digit domains reject batches | Exact evidence that a cheap relaxation could prune substantial batches | High for the feasibility test; uncertain for a fast algorithm | Directly attacks the unresolved middle of the cube |
| 2 | H2. Sequential conditioning retains diversity | Calibrated sampling that finds actual witnesses more efficiently | Moderate; failure is readily observable | Could replace an exponentially wasteful search |
| 3 | H3. Pandigital words cover compatible residues | A theorem first modulo `b+1`, then for a larger class | Moderate for the first modulus; harder uniformly | Closes a broad obstruction route or reveals a new constraint |
| 4 | H4. Conditioned low-order statistics still cannot force a hit | Exact finite certificates, then a general limitation theorem | Moderate for small cases | Identifies what an existence proof must measure beyond fitted statistics |
| 5 | H5. SAT can exploit positive instances | A decisive first-witness benchmark on unplanted analogues | High for the benchmark; low expectation of success | Tests one distinction left open by the poor SAT results |

These are different kinds of progress. A feasibility test is not a search
speedup; a speedup is not a solution; a limitation theorem is useful only
when it rules out a broad class of arguments. None deserves indefinite
funding merely because its first experiment works.

## What the existing work actually establishes

A nice number has a square and cube whose ordinary base-`b` digits together
use every digit `0,…,b−1` exactly once. The project still has only the known
example: `69² = 4761`, `69³ = 328509` in base 10. It has neither another
example nor a proof of uniqueness.

The earlier work supplied genuine restrictions: exact length and digit-sum
conditions, a proof that a completely carry-free construction cannot work,
and theorems showing that fixed-depth end filters cannot settle all bases.
The structured-family searches and repdigit reductions are useful records,
but extending those narrow families offers a weak route to the main goal.
See [obstructions](../research/obstructions.md),
[constructions](../research/constructions.md), and the
[structure assessment](p1-structure/REPORT.md).

Three newer findings change the priorities:

* **Overlap search genuinely improves the algorithm.** Matching compatible
  leading and trailing descriptions gave 9–534 times fewer full checks,
  but only 1.2–7 times fewer total operations. Matching the lists becomes
  the bottleneck. Its model still projects about `10^42` checks per expected
  solution at base 120; even its idealized 80% end-certification limit leaves
  about `10^25`. These are model projections, not computational lower bounds
  for every algorithm. [Algorithm report](p1-algorithm/REPORT.md)
* **The proposed statistical obstruction has weakened.** The new
  deficiency-two sample contained 20 cases against about 18.3 predicted.
  This test had little power against a modest effect, so it does not
  statistically disprove the old shortfall. It supplies no convincing
  growing obstruction to pursue. [Obstruction report](p3-obstruction/REPORT.md)
* **The analogue testbed is stronger than the older summaries say.** The
  completed twice-nice base-24 search has 6 solutions; the completed
  thrice-nice base-18 search has 533. Both result files record independent
  exact verification. Across the pooled analogue data there are 875 hits
  against about 900 in the refined model, versus about 975 in the simpler
  model. Model choice matters. This supports using these cases as testbeds;
  it does not prove that ordinary nice numbers exist elsewhere.
  [Base 24](p3-analogues/results/run_k2_b24.json),
  [base 18](p3-analogues/results/run_k3_b18.json),
  [analysis](p3-analogues/results/analysis.json)

Several broad claims need narrower wording. The overlap result already
exceeds the earlier 40% edge accounting. The 80% argument concerns the
specified fixed-digit certificates from the two ends, not set-valued
constraints or every possible algorithm. The structure report's count of
varying positions is not a measurement of joint entropy. The congruence
coverage argument in the critique still lacks a covering proof. Finally,
the failed absolute-value estimates in the existence report do not rule
out every signed or combinatorial positivity argument. Proving existence
in one base would not automatically settle a conjecture about every base.

## H1. Possible middle digits can rule out whole batches

**Plain-language idea.** Even when we cannot determine a digit, we might
know its possible values. If five output positions have only four values
available between them, the entire batch is impossible. This is stronger
than inspecting each position separately.

**Hypothesis.** Among batches of roots with a fixed prefix and suffix and
two or more free root digits, a substantial fraction of batches surviving
the existing end checks fail a joint capacity test involving the cube's
middle positions. The rejection should persist as batch size increases,
rather than appearing only when nearly every root digit is already fixed.

For a batch `B`, let `u_a` count the already certified occurrences of digit
`a`, and let `D_j` contain every value that occurs at unresolved output
position `j` for any root in `B`. In a `K`-nice problem, digit `a` has
remaining capacity `K−u_a`. A necessary condition for a completion is

```
|J| <= sum of (K-u_a) over a in the union of D_j, j in J
```

for every collection `J` of unresolved positions. A maximum-flow or
matching calculation checks this condition. For ordinary niceness, it is
the familiar rule that each position needs a different available digit.
Failure safely rejects the batch. Passing says nothing about whether one
root realizes the suggested assignment.

**Why this is new enough.** Public searches already use compatibility/Hall
ideas at the ends. The proposed addition is sound domains for genuinely
unfixed middle cube digits, approximately positions `L,…,2L−1` when the
root has `L` digits. It is not another test of already fixed edge digits.

**First experiment.** Enumerate complete, bounded batches with two and
three free root digits on the existing testbed. Build their exact domains
and compare matching with and without the middle cube positions. Report
both batch-weighted and root-weighted rejection. Include ordinary
`K=1` cases with known negative answers and `K=2,3` cases with known hits.
Preserve every known witness.

This is an **oracle feasibility test**: enumerating a batch to learn its
domains cannot itself save work. Only if exact domains are informative
should we derive cheap supersets from interval arithmetic, residues, or
shared carry constraints. Supersets preserve sound rejection; accidentally
omitting a possible digit does not.

**Continue / stop.** As a practical screening threshold, require at least
10% additional root-weighted rejection on several cases, persisting from
two to three free digits. This threshold is a budget choice, not a theorem.
Stop this relaxation if domains rapidly fill the alphabet or rejection
vanishes. A positive screen must next show that domain construction plus
matching costs less than the work saved, including all preprocessing.

**Bridge to a solution.** An effective implementation would supply a
specific way to constrain the unresolved middle for many roots at once.
Ultimately the savings must grow substantially with base and window size;
one more constant-factor filter cannot close the current gap.

## H2. Progressive conditioning can reach the rare event without collapsing

**Plain-language idea.** Rather than repeatedly trying a whole number,
keep a population of candidates that pass a moderately difficult test,
refresh that population, and then strengthen the test. The crucial question
is whether refreshing really produces different candidates.

**Hypothesis.** There is a sequence of exact conditions and reversible
root proposals for which population sampling retains diversity as middle
digit constraints are added, and its total cost per verified witness grows
more slowly than the best existing enumerator on the analogue testbed.

One concrete sequence fixes an ordering of output positions and defines
`A_r` to be the correct-length, congruence-compatible roots for which the
first `r` selected positions use each digit at most `K` times. Then

```
A_0 contains A_1 contains ... contains A_(Kb),
```

and the last set consists exactly of the `K`-nice roots. Process useful edge
constraints early, but ensure that the difficult later stages actually
include middle cube positions. Resampling survivors alone is insufficient:
use explicit reversible block proposals on roots, with the correct
acceptance rule for the desired conditional distribution.

**Why this is distinct from failed work.** The earlier single-digit hill
climbing and suffix lifting improved scores little or stalled after
controlling the ends. Here the claim concerns the conditional distribution,
population diversity, and actual witness cost—not a better average score.
See [digit lifting](../research/digit-lifting.md) and
[constraint search](../research/constraint-search.md).

**First experiment.** On small, fully enumerable cases, compare the sampled
root distribution and each conditional survival probability with exact
answers. Then use unplanted twice/thrice-nice cases. Record distinct
ancestors, acceptance rates, autocorrelation, missed modes, actual distinct
witnesses, and all proposal costs. Compare with random restarts and the
best available end/overlap search under equal budgets.

**Continue / stop.** Continue only if independent runs retain diversity
through the middle stages, pass exact small-case calibration, and show an
improving cost advantage on held-out cases. Stop if the population becomes
copies of a few ancestors, proposals almost never move, or the apparent
gain disappears after charging for rejuvenation. Reversibility alone does
not establish fast mixing or connectivity.

**Bridge to a solution.** A successful sampler could find a witness without
enumerating the enormous ambient interval. Transfer from `K=2,3` to `K=1`
must still be tested; the analogues allow collisions that ordinary niceness
forbids. A stable probability estimate is not a proof of existence. An
independently verified new witness would be.

## H3. Compatible residues are covered by pandigital split words

**Plain-language idea.** Before looking for a new divisibility obstruction,
settle whether rearranging the digits already realizes every remainder
pair that the usual digit sum permits.

**Hypothesis.** For sufficiently large `b`, lengths `s+c=b` with
`s,c >= b/3`, and any `M <= b²` coprime to `b`, the residue pairs of
pandigital words `(X,Y)` of those lengths, with neither leading digit zero,
are exactly the pairs satisfying

```
x+y = b(b-1)/2   modulo gcd(M,b-1).
```

This is a precise, deliberately bounded replacement for the critique's
broader sketch. It is a conjecture. The decimal enumeration verifies the
predicted image for the 39 coprime moduli from 3 through 99, but that does
not prove uniform coverage in growing bases.
[Sketch](../critique/research-directions.md),
[enumeration](../critique/results/multiset-image-base10.json)

**First theorem to try.** Set `M=b+1`. Because `b=-1` modulo `b+1`, each
word's residue is an alternating digit sum. The task becomes partitioning
the digits among four groups: the positive and negative positions of each
word, with prescribed group sizes. This offers a concrete additive
combinatorics problem without multiplication carries. Preserve the two
nonzero leading positions explicitly.

The missing step in the existing argument is important: showing that swap
increments generate a group does not show that one permutation of the
available digits reaches every residue. A proof must construct the
partition or bound the number of representations, not just list generators.

**Continue / stop.** First produce an explicit threshold and proof for
`b+1`, or a verified counterexample. Then test the proposed range up to
`b²` on manageable cases before seeking a uniform theorem. A small-base
exception only changes a sufficiently-large-base threshold; it does not
refute the asymptotic statement. If the broad statement fails, study the
missing residues and whether the power curve `(n²,n³)` actually meets them.

**Bridge to a solution.** A proof removes a broad class of possible
congruence obstructions and supplies a local compatibility ingredient for
an existence argument. A systematic counterexample could expose a new
necessary condition. Neither outcome identifies a common root `n` by
itself. Coverage separately modulo several numbers also does not imply
simultaneous coverage modulo their product without an additional argument.

## H4. Even correctly conditioned low-order statistics cannot force a hit

**Plain-language idea.** How much evidence of random-looking digits is
enough? Can a distribution reproduce all the statistics we know how to
measure, yet give nice configurations probability zero?

**Hypothesis.** After imposing nonzero leading digits and the correct
digit-sum congruence, statistics of degree up to a fixed positive fraction
of `b` still cannot force a pandigital outcome. A concrete initial target
is degree at most `floor(b/4)` for all sufficiently large admissible even
bases. The fraction `1/4` is a proposed theorem target, not an established
threshold.

Let `h_a` be the number of occurrences of digit `a`, with `sum h_a=b`.
The desired histogram is `(1,…,1)`. Let `mu` be the uniform legal-word model
conditioned on

```
sum a*h_a = b(b-1)/2   modulo b-1.
```

Ask whether a probability distribution `nu` on the same admissible
histograms can assign zero mass to `(1,…,1)` while satisfying

```
E_nu Q(h) = E_mu Q(h)
```

for every symmetric polynomial `Q` of total degree at most `t`.
“Symmetric” here means unchanged by relabelling the digit counts; it does
not mean that the congruence-conditioned model itself has that symmetry.

**Why this is not repeating an established counterexample.** The earlier
[counting note](../research/existence-counting.md) already gives an
unconditioned distribution with uniform marginals through `b−1` positions
and no pandigital outcome. Re-proving an unconditioned low-order limitation
would add little. The new issue is preserving the known arithmetic and
leading-digit restrictions; a useful extension would also condition on
fixed legal end digits.

**First experiment.** This is a finite linear feasibility problem in small
bases: unknown nonnegative histogram weights, known exact model moments,
and zero weight at the target. Use exact rational verification of any
certificate. A numerical solver's tolerance is not a proof. If no such
distribution exists, extract and verify a separating polynomial: it would
give a lower bound on target mass from those moments.

**Continue / stop.** Continue only toward a general construction of fake
distributions under the stated conditioning, or an unexpectedly low-degree
positivity certificate whose arithmetic moments might be bounded. Stop
after the small-case certificate study if it offers neither. Do not turn
this into another large table of reassuring fitted moments.

**Bridge to a solution.** A theorem would show precisely which information
an existence proof must add: positional structure, carries, higher-order
correlations, or a constructive mechanism. A separating polynomial could
instead offer a more economical proof target than uniform control of an
entire high-dimensional characteristic function. Neither direction proves
anything about actual power digits until its hypotheses are established
for those digits. [Existing analytic barriers](p2-existence/REPORT.md)

## H5. SAT may find witnesses better than its negative-instance tests suggest

**Plain-language idea.** Proving that a box is empty and finding one object
in a nonempty box are different jobs. Most of our SAT calibration measured
the first job, while the large-base heuristic suggests the second.

**Hypothesis.** On naturally satisfiable, unplanted `K`-nice instances,
time to the first verified witness scales better than the existing exact
search, despite SAT's poor performance on small ordinary bases with no
solutions.

The evidence is unfavorable, so this gets the smallest budget. The
[SAT calibration](../critique/results/sat-scaling.json) and
[direct-CNF work](../research/direct-cnf.md) show that reducing formula
size or successfully loading a large instance does not establish useful
search performance. Nevertheless, negative-instance timing alone does not
settle the first-witness hypothesis.

**First experiment.** Use the existing arithmetic encoding with the
minimum change needed for multiplicity `K`. Benchmark first-witness time
on known positive twice/thrice-nice cases. Keep the known roots out of the
solver input; do not plant digits or select intervals around witnesses.
Use multiple seeds, fixed CPU and memory limits, and include encoding time.
The comparison must also stop the enumerator at its first hit, using
predeclared traversal/randomization rules—not compare SAT's first hit with
exhaustive enumeration of every solution.

Train on smaller cases and reserve larger existing cases, such as
twice-nice base 24 or thrice-nice base 18, for validation only if the small
tests pass. Compare against the fastest applicable existing baseline,
including overlap or filtered analogue search.

**Continue / stop.** Require a reproducible advantage that increases with
problem size and survives a held-out case. Otherwise close this line after
one bounded campaign. Recovering 69, saving clauses, a single lucky run,
or obtaining `UNKNOWN` at a large base are not success criteria. Do not
precede the benchmark with another general encoding rewrite.

**Bridge to a solution.** A strong positive result would justify testing
ordinary nice-number instances where the model predicts many witnesses.
It would still need to survive the tighter `K=1` constraint. A negative
result closes the specific SAT-versus-UNSAT distinction and prevents
further speculative solver engineering.

## Order of work and stopping discipline

Start with H1's oracle test and H3's `b+1` theorem attempt. H2 deserves a
small calibrated prototype, not a large unvalidated population run. H4
and H5 should each have one fixed-budget diagnostic pass. These are future
tasks; this report does not start them.

Use the saved exact solution sets instead of launching more analogue
enumerations merely to enlarge the testbed. Charge algorithms for list
generation, joins, rejected proposals, preprocessing, and memory—not only
full power expansions. Record a failed hypothesis with its precise scope.

Defer further repdigit/fixed-family scans, renewed deficiency-two hunting,
frontier brute force, and the C rewrite. The missing ingredient is a way
to constrain or reason about the globally coupled output digits. The five
proposals above are useful only insofar as they test specific ways to do
that, or precisely delimit which information is insufficient.
