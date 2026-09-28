# Nice numbers: progress in plain English

Updated September 28, 2026.

**We have not found a second nice number, and we have not proved that 69
is the only one.** Nothing in this repository is a solution. What it does
contain is a clear account of why the problem is hard, one real (but
modest) search speedup, and a set of tested dead ends.

The target is the trick performed by 69:

`69² = 4761` and `69³ = 328509`.

Together these contain every decimal digit exactly once. In another base b,
the square and cube must together use each of the b digits exactly once, with
no extra zeros added at the front.

## Where things stand

- **Searched so far:**
  - The public search project has checked every base up to 48 completely.
  - It has checked bases 49–54 for nice numbers only.
  - It is about 13% of the way through base 57.
  - No nice number has turned up besides 69. ([public data](https://data.nicenumbers.net/bases?select=*&order=id.asc))
- **Almost certainly false:** "69 is the only one." A simple model that treats
  the digits as random predicts the searched data very well (details below).
  It says nice numbers become likely somewhere above base 100 and plentiful
  beyond, with more than 10²⁰ expected in base 300 alone.
- **Almost certainly out of reach:** the next one.
  - With the best known search methods, finding one near base 118 would take
    about 10⁴³ checks, roughly 10²⁹ years at the public search's current rate.
  - The chance that one sits in bases 57–64, the only bases reachable in
    years to millennia, is about 0.1–0.3%.
  - ([odds and costs](critique/research-directions.md))

## Five follow-up hypotheses, tested September 28

The September 27 review proposed five bounded tests
([NEXT_HYPOTHESES.md](attack/NEXT_HYPOTHESES.md)). Four were run. None
changes the picture above; each is closed with numbers and a report.

- **H1, possible values of middle digits reject batches: killed.** For
  batches of roots with a fixed prefix and suffix and 2–3 free digits, every
  digit in the cube's middle third can take every value, so a Hall test on
  those domains rejects nothing beyond the existing end checks. With one free
  digit (a batch of b roots) the domains hold 64% of the alphabet and the
  extra rejection is at most 9 roots in a million, against a 10% target.
  Tested exactly on 5.4×10⁹ roots across nice, twice-nice and thrice-nice
  bases; all 60 known witnesses preserved. ([report](attack/h1-domains/REPORT.md))
- **H2, progressive conditioning with digit proposals: killed.** A
  subset-simulation sampler with the same score and budget as uniform random
  sampling finds 0–0.8 times as many distinct witnesses, worse as the base
  grows (none at all in 30 runs on thrice-nice base 14, where uniform
  sampling found 7). The surviving seeds descend from 1–12% of the ancestors
  and no episode ever reached the final level by conditioning. Changing any
  digit of n re-randomizes the output digits above it, so there is nothing
  for a chain to climb. ([report](attack/h2-sampler/REPORT.md))
- **H3, pandigital splits realize every residue pair the digit sum allows:
  confirmed, and proved for the modulus b+1.** An exhaustive computation
  covers every modulus up to b² coprime to b for bases 10–18 (1,057 cases,
  no exception), and every divisor of b²−1 up to base 24. A short theorem
  gives the modulus b+1 in every base b ≥ 10: once the digit sets of the two
  words are fixed, the words are independent, and subset sums of an interval
  of integers fill an interval long enough to cover every residue. So no
  congruence obstruction exists at any of these moduli; the only one is the
  digit sum. The proposed bound M ≤ b² is loose from base 12 on; the
  exceptions at bases 10–11 come from a 4-digit square word.
  ([report](attack/h3-covering/REPORT.md))
- **H5, SAT finds a first witness faster on satisfiable instances: killed.**
  On thrice-nice bases 9 and 10 the solver needs 85–285 seconds to a first
  verified witness where a filtered enumerator needs 0.2–2 milliseconds, the
  same 10⁵ gap as on the empty instances; on twice-nice bases 14–15 and
  thrice-nice base 13 it finds nothing within 400–600 seconds where the
  enumerator needs under a tenth of a second.
  ([report](attack/h5-sat-witness/REPORT.md))
- **H4** (a moment-matching limitation theorem) was not attempted; it has the
  least bearing on either goal.

What these add to the picture: the middle third of the cube resists
set-valued relaxations and stochastic conditioning as completely as it
resists exact certificates, and the last family of possible congruence
obstructions is gone. The routes that remain are the ones listed under
"What would change this picture".

### What the middle digits actually are

The follow-up asked for the structural theory behind those failures, and it
turns out to be simple to state ([report](attack/middle-digits/REPORT.md)):

- **Along any search batch** (fixed prefix and suffix, a free block of
  digits), a middle digit of the cube is the digit-coding of a polynomial
  sequence of degree at most three in the block's value. Its linear
  coefficient is a digit-tail of 3c², its quadratic coefficient a digit-tail
  of 3c, and its cubic coefficient an exact power of 1/b, where c is the root
  with the block zeroed. This is exact and was checked on 5.4 million batches.
- **That model, with a random linear coefficient and the exact quadratic and
  cubic ones, reproduces the measured distribution of how many values a
  middle digit takes along a batch** to within 0.2–1% at every position and
  batch shape tested, where independent random digits are off by up to 68%.
  It explains the excess of small domains H1 recorded and the positions where
  the cube takes more distinct values than random digits would.
- **The coefficients are equidistributed over batches wherever Weyl's
  inequality applies** (a theorem with proof), which for search-shaped
  batches is the upper half of the middle third; below that they follow the
  arithmetic of 6·Ptop·R + 3R², which is measured and produces nearly periodic
  digit sequences for structured suffixes, but no certificate.
- **A middle digit takes at most three values along a batch of b roots in
  10⁻⁶ to 10⁻³ of the cases.** These are the lattice certificates the
  algorithm report costed at one digit per factor b, seen directly; they
  account exactly for H1's negligible extra rejections.
- **Over a large batch every middle digit is uniform, and changing any root
  digit re-randomizes every output digit above it** with probability 1 − 1/b
  (both theorems with proof; measured to four digits).

The upshot: the only structure the middle digits have is the one edge and
lattice methods already use, and the one algebraic event that could open a
door (many digit-tails of 3c² small at once) is excluded by the sparsity and
structured-family results. This is the "middle-digit wall" as a description
rather than an absence.

## Search improvements

Cost is measured as *checks per expected nice number*. Each 10× speedup buys
only about 2–3 more bases, because the cost grows about 0.4 orders of
magnitude per base.

### The one real improvement: the overlap join

Existing searches prune candidates from both ends. Fixing the last few digits
of n fixes the last few digits of n² and n³. Fixing the first few digits of n
fixes the first few digits of n² and n³. Used separately, this lets a search
rule out bad candidates before doing full arithmetic on about **40%** of the
output digits.

The overlap join makes the two ends share some of n's digits:

- it builds one list of good leading-digit prefixes and one list of good
  trailing-digit endings;
- it matches them on the digits they share;
- each shared digit then checks four output digits instead of two.

In principle this reaches **80%** of the output digits.
([report](attack/p1-algorithm/REPORT.md))

**Measured** (exact search on bases where the full answer is known; every
known solution was found, and every hit was re-verified):

| Test | Fewer full checks | Fewer total operations |
|---|---:|---:|
| Nice numbers, bases 25–40 | 26–534× | 2.7–7.0×, growing with base |
| Twice-nice, bases 15–22 | 9–59× | 2.0–2.7× |
| Thrice-nice, bases 13–14 | 11–12× | about 1.2× |

**Expected speedup at larger bases** (modelled; log₁₀ of checks per expected
nice number, lower is better):

| Base | Edge search (previous best) | Overlap join | Join + colour coding (not built) | Speedup |
|---:|---:|---:|---:|---|
| 57 | 19.7 | 19.2 | 18.5 | 3× (16×) |
| 60 | 21.1 | 20.4 | 19.9 | 5× (16×) |
| 64 | 22.5 | 21.7 | 21.1 | 6× (25×) |
| 118 | 43.3 | 41.0 | 39.2 | 200× (12,600×) |

"Colour coding" is a known randomized trick for enforcing that the two lists
use different digits. It is modelled here but not implemented.

**What that buys.** At the frontier the join is worth about 1–3 bases.

- At today's public search rate, finishing the rest of base 57 through base 60
  would drop from about 100 years to about 20 (join) or about 6 (with colour
  coding, if built).
- The chance of a nice number there stays about 0.2%.
- At base 118, even 12,600× leaves about 10³⁹ checks.

**Caveats:**

- **Baseline.** The speedups are against our own edge search, not the public
  client, which already has a "cross-end" filter that may capture part of
  this gain. This comparison has not been made.
- **Not new.** The same join was used in 2021 for squares with only three
  distinct digits ([Geißer et al.](https://arxiv.org/abs/2112.00444)).
- **Test range.** Our nice-number tests stop at base 40 (128-bit arithmetic).

**Why no speedup of this kind can finish the job.** The middle third of the
cube's digits depends on every digit of n, whichever end you start from. No
method working from the two ends can check those digits early. Even a perfect
version of the overlap join would still need about 10²⁴ checks near base 118.

### Search ideas that did not help

| Approach | Result |
|---|---|
| SAT / constraint solvers | 10⁴–10⁵× **slower** than plain enumeration on bases with known answers ([critique](critique/experiments.md)) |
| Lattice methods (Coppersmith style) | Cost more per checked digit than they save; worse than edge search |
| Meet-in-the-middle, knapsack-style representations, dynamic programming over carries | No usable structure in the middle digits |
| Growing solutions digit by digit from the bottom | Digit variety rose from 63% to 67%; no practical effect |
| Random sampling with hill climbing | No improvement over plain random sampling |
| Structured families of candidates (fractions, repeating patterns, special bases) | None does better than random numbers; 18,985 roots with near-linear digit runs were all checked, none nice ([report](attack/p1-structure/REPORT.md)) |

Other tooling:

- a C++ search that independently confirmed only 69 in bases 2–30;
- a fast exact counter for twice- and thrice-nice numbers
  ([`attack/p3-analogues`](attack/p3-analogues/)), which covered twice-nice
  base 24 (5.3×10¹² candidates) in about 18 CPU-minutes;
- C ports of the verifier and family searches in [`native/`](native/),
  which are still in progress: the Makefile lists two sources that are not
  present yet.

## Testing whether 69 might be unique

A proof that 69 is the only one would need some hidden rule that forbids nice
numbers. If such a rule existed, it should show up as a shortage of near
misses and of related rare events. We looked for one in three ways. None
showed a real shortage.

- **Near misses.** Numbers missing 3–6 digits match the random model to within
  1%, across about 8×10¹⁵ publicly searched candidates.
  - Numbers missing exactly two digits looked 13% short (bases 20–48).
  - On new data from bases 49–50 that shortage vanished: 20 found against 18.3
    predicted.
  - Across 25 features, the missing cases show no pattern.
  - That lead is closed. ([report](attack/p3-obstruction/REPORT.md))
- **Twice- and thrice-nice numbers.** These are numbers whose square and cube
  use every digit exactly twice (or three times). They have the same
  arithmetic, but show up in small bases, so they can be counted exactly. For
  example, 6534² = 42693156 and 6534³ = 278957081304.
  - Earlier bases: 95 found against 97 predicted.
  - New exact counts, all verified:

    | Case | Found | Predicted (refined model) |
    |---|---:|---:|
    | Thrice-nice, base 16 | 241 | 239.7 |
    | Thrice-nice, base 18 | 533 | 568.6 |
    | Twice-nice, base 24 | 6 | 3.4 |

  - Pooled, the new bases come in at 0.96 of the prediction (p = 0.14).
    Twice-nice base 25 is still running and base 26 is pending, so these
    numbers are preliminary. ([work in progress](attack/p3-analogues/))
- **Congruences.** The only divisibility rule that "each digit once" implies
  is the digit-sum rule modulo b−1. That rule already kills every base that
  leaves 3 when divided by 4. No other congruence exists: checked exhaustively
  for every modulus up to b² in bases 10–18, and proved for the modulus b+1 in
  every base ([H3 report](attack/h3-covering/REPORT.md)), so no argument of
  this kind can rule out the rest. ([critique](critique/critique.md))

## Could someone prove a second one exists without finding it?

Not with current mathematics. ([report](attack/p2-existence/REPORT.md))

- **Why the standard tools fail.** Those techniques only bound error terms.
  The count here is produced by cancellation, which makes such arguments fail
  in principle, not just in practice.
- **Easier problems come first.** A proof would first have to settle two open
  problems:
  - a question about the digit sums of cubes
    ([Drmota–Mauduit–Rivat, Problem 2](https://www.dmg.tuwien.ac.at/drmota/dmr6.pdf));
  - the conjecture that every suitable base has a square using each digit
    exactly once ([Wu, Conjecture 1](https://arxiv.org/abs/2403.20304)).
- **Calibration.** The random model matches exact counts of those pandigital
  squares through base 19 to within 6%, yet even that easier statement is
  unproven. ([literature survey](attack/literature/REPORT.md))

## What we have proved about special cases

These rule out whole families of candidates, including infinitely many
numbers, but together they cover a negligible share of all candidates.

- **Carrying is essential.** No solution comes from a multiplication pattern
  whose cube needs no carries.
- **Spread-out digits fail.** Patterns such as `a00b00c` inevitably repeat a
  digit, as do some symmetric patterns like `a0b0c0b0a`.
- **Repeated-digit numbers** (like `7777`) are ruled out in every base one
  more than a power of an odd prime. They are also ruled out in every base
  through 2000.
- **Edge checks alone can't settle the question.** Checking a fixed number of
  leading and trailing digits can never prove uniqueness: numbers passing
  those checks exist in arbitrarily large bases.
- **One base per number.** A given number has the right total length in at
  most one base.

Proofs and scope are in [RESEARCH_LOG.md](RESEARCH_LOG.md) and
[`research/`](research/).

## Checks on the public search

- **Histograms.** We recomputed its near-miss counts for bases 10–35
  (5.8×10¹⁰ candidates) independently. Every count matches.
- **Missed candidates.** Its stored search ranges skip one valid candidate in
  26 bases. We checked all 26; none is nice.

## Related work

- **Brian Haskin (Janzert)** has independently formalized the basic
  obstructions in Lean 4, including the digit-sum and length rules. He has
  also certified by machine that 69 is the only nice number in bases 2–18.
  - His announced article series, *Nice Numbers and the Middle Digit Wall*,
    names the same barrier we hit. It is not yet published.
  - His Lean proofs are more rigorous than ours; our work adds the data tests,
    the search algorithms, and the analysis of why existence proofs fail.
  - ([Lean proofs](https://github.com/Janzert/nice-numbers-lean),
    [certified search](https://github.com/Janzert/nice-numbers-certified))
- **Prediction market.** The market
  ["Is 69 the only nice number?"](https://manifold.markets/PlasmaBallin/is-69-the-only-nice-number)
  stood at 9% YES on September 27.

## What would change this picture

- **A search method** that checks the middle third of the cube's digits
  before doing full work on each candidate. None is known.
- **A theorem** giving exponentially precise digit statistics for squares or
  cubes. None is known, even for digit sums.
- **A real shortage** of twice- or thrice-nice numbers as they get rarer. So
  far, none.

## Where to read more

| File | Contents |
|---|---|
| [critique/README.md](critique/README.md) | Independent review: the random model, the odds, why SAT and family exclusions can't solve it |
| [critique/research-directions.md](critique/research-directions.md) | The only four routes to a true solution, with honest odds |
| [attack/README.md](attack/README.md) | The September 26–27 parallel attack: one folder per hypothesis, each with a report |
| [attack/literature/REPORT.md](attack/literature/REPORT.md) | Survey of prior and related work |
| [RESEARCH_LOG.md](RESEARCH_LOG.md) | Proofs, experiments and dead ends from the first phase |

## Sources

- Public search: [client](https://github.com/wasabipesto/nice), [data API](https://data.nicenumbers.net/bases?select=*&order=id.asc)
- M. Geißer, T. Körner, S. Kurz, A. Zahn, squares with three distinct digits: [arXiv:2112.00444](https://arxiv.org/abs/2112.00444)
- C. W. Wu, pandigital squares: [arXiv:2403.20304](https://arxiv.org/abs/2403.20304); counts: [OEIS A258103](https://oeis.org/A258103)
- M. Drmota, C. Mauduit, J. Rivat, "The sum-of-digits function of polynomial sequences": [preprint](https://www.dmg.tuwien.ac.at/drmota/dmr6.pdf)
- B. Haskin: [nice-numbers-lean](https://github.com/Janzert/nice-numbers-lean), [nice-numbers-certified](https://github.com/Janzert/nice-numbers-certified)
- Manifold market: [Is 69 the only nice number?](https://manifold.markets/PlasmaBallin/is-69-the-only-nice-number)
