# Research directions: toward a true solution

2026-09-26. Companion to [critique.md](critique.md); evidence is in
[experiments.md](experiments.md).

**Only two outcomes count:**

- a second nice number, found explicitly or proved to exist;
- a proof that 69 in base 10 is the only one.

Nothing else is treated as progress here: verification, write-ups, better
heuristics, and search speedups that shave an order of magnitude off an
astronomical cost. Everything below is judged by one question: could this
produce one of those two outcomes?

## The goal, and where it stands

- **Nonexistence is almost certainly false.** The random-digit model predicts
  more than 10²⁰ nice numbers in base 300 alone. It matches every test
  available:
  - near misses (3–6 missing digits) across about 8×10¹⁵ public candidates,
    to within 1%;
  - exact solutions of the same problem with every digit used twice or three
    times: <!-- ANALOGUE_SHORT -->336 exact hits against 361 predicted<!-- /ANALOGUE_SHORT -->.
- **Existence is almost certainly true, but no known method can exhibit a
  second nice number.** The chance that one exists in the unsearched bases
  first passes 50% around base 118. There, even a search that exploits every
  leading and trailing digit costs about 10⁴³ checks per expected solution.
  At the current frontier (base 57) it is 10¹⁹·⁷, rising about 0.4 orders of
  magnitude per base.
- **So every route to a true solution needs a new idea.** Nothing in the
  existing tracks, and no amount of engineering on them, closes a gap of about
  23 orders of magnitude.

| Path | Would yield | What it needs | Honest odds |
|---|---|---|---|
| 1. Middle-digit search | An explicit second nice number | An algorithm that forces about 90% of output digits distinct before per-candidate work | Low; no known approach, but the only route to an explicit number where they should exist |
| 2. Existence proof | A proof that a second one exists | New mathematics for events of probability e^−b | Very low |
| 3. Nonexistence proof | A proof that 69 is unique | A global obstruction that all current evidence contradicts | Very low; one weak lead, cheap to test |
| 4. Frontier lottery | An explicit number, by luck | Compute only | 0.1–0.2% this decade |

## Path 1. A search that controls the middle digits

This is where an explicit second nice number would have to come from, since
the model puts them at bases of about 120 and up.

### What the method must achieve

For n with L base-b digits, fixing n's bottom digits fixes the bottom digits
of n² and n³, and fixing its top digits fixes (nearly) their top digits. So
edge methods control about two output digits per input digit, roughly 40% of
the b output digits. The remaining 60% depend on all of n at once, and a
candidate must win a lottery on them, costing about `b^M / M!` per solution
with M uncontrolled digits.

At base 120:

| Output digits forced distinct before per-candidate work | Cost per solution |
|---:|---:|
| 40% (both edges; the best existing methods) | ~10⁴⁶ |
| 60% | ~10³⁹ |
| 80% | ~10²⁶ |
| 90% | ~10¹⁶ |

**The target, stated precisely:** at a base around 120–130, enumerate about
10¹⁶–10²⁰ candidates in which roughly 90% of the output digits are guaranteed
distinct, at a cost proportional to their number. A method reaching 60% on a
family that grows like b^(cb) would be the first real advance. A method at
40% is another edge method and cannot matter.

### What a breakthrough would have to look like

A middle digit of n² is known only once n is known essentially completely,
working from either end. So the method must decide something about middle
digits for a whole *set* of candidates at once, the way the public client's
leading-digit filter certifies top digits for a whole interval. It must also
do this cheaply.

Measure cost in units of log b per certified output digit:

- edges pay **½**, since fixing one input digit shrinks the set by a factor b
  and certifies two output digits;
- plain enumeration is the baseline everything must beat;
- a method needs a rate well below ½, sustained across most of the output, to
  reach the target.

### Natural attacks, and why they fall short

These are recorded so that no one repeats them without a new ingredient:

- **Lattice (arithmetic-progression) certificates.** Along n = n₀ + d·t with
  d a multiple of b^⌈(i+1)/2⌉, the quadratic term vanishes modulo b^(i+1).
  If the cofactor of d is chosen by lattice reduction so that 2n₀·d is small
  there, digit i of n² changes slowly along the progression, so whole
  progressions can be certified.
  - *Shortfall:* each such condition certifies one digit and costs about a
    factor b of set size, a rate of 1, worse than the edges.
  - *Several digits:* certifying more requires simultaneous approximation
    conditions, and each carries its own cost.
  - *What would change this:* conditions on many digits (of both powers)
    that share cost. No mechanism for that is known.
- **Linear windows.** For n = H·b^j + L with L fixed, the output window just
  above L is affine in H. Only that window is; windows further up contain H²
  and H³ terms. This is the bottom-edge method again.
- **Structured roots.** Taking n near b^m·θ (for algebraic θ), or as a
  rational expansion, shapes only the top digits, which top-down edge search
  already controls. Forms that shape more digits hit a tension: the square's
  digits want a denominator near √b, the cube's near b^(1/3). So they repeat
  digits. Carry-free, sparse, fixed-denominator, periodic, and stretched forms
  are already proved impossible.
- **Constraint solvers (SAT/SMT).** Measured at over 10⁴ times slower than
  plain enumeration on bases with known answers
  ([experiments §4](experiments.md#4-sat-scaling-on-bases-whose-answer-is-known)).

### Testbed for any new idea

Complete solution sets are now known for analogues with the same algebra:
twice-nice numbers through base 22 and thrice-nice numbers through base 16
([experiments §3](experiments.md#3-exact-hits-in-analogues-k-nice-numbers)).
Complete near-miss counts are known for nice numbers through base 48
([experiments §2](experiments.md#2-the-random-digit-heuristic-against-the-public-histograms)).

A candidate method should, for example:

- find all 241 thrice-nice numbers in base 16 while examining far fewer than
  10¹¹ candidates;
- show a certification rate below ½ on middle digits;
- show the gain growing with the base.

This makes any claimed breakthrough checkable in hours.

**Assessment and stopping rule.** I know of no promising line. This path is
still the right place for effort aimed at an explicit number, because nothing
else can reach the bases where solutions should be. Stop after about a month
of focused work if no method beats the edge rate on the testbed.

## Path 2. A non-constructive existence proof

Since the expected count grows super-exponentially, proving that even one
large base contains a nice number would settle the question.

The natural shape is a second-moment argument: show that the variance of the
count is small compared with its squared mean, in some base or some
structured subfamily. That requires controlling the joint distribution of
*all* b digits of n² and n³, and of pairs of such candidates, at a resolution
where the event has probability about e^−b.

Existing digit-distribution theorems do not reach this:

- Maynard-type results handle restricted digits in a fixed base;
- Swaenepoel-type results prescribe only a limited proportion of the digits
  of squares;
- neither controls a permutation condition across two powers whose length
  grows with the base.

The project's own Fourier/Parseval and inclusion–exclusion analysis
([existence-counting.md](../research/existence-counting.md)) shows the generic
bounds miss by exponential factors.

**Assessment:** there is no viable route with current techniques. This path
makes sense only with an analytic number theorist who has a specific idea for
full-resolution digit equidistribution of polynomial values.

## Path 3. A nonexistence proof

Everything measured says the statement is false. A proof would need an
obstruction that:

- suppresses the pandigital event by more than twenty orders of magnitude at
  base 300;
- leaves near-miss rates within 1% of random through base 48;
- leaves twice- and thrice-nice numbers occurring at their predicted rates.

Two kinds of argument are already ruled out.

### Why modular arguments cannot work (no hidden congruences)

*Setting.* Fix b ≥ 3 and lengths s + c = b. Let 𝒫 be the set of pairs (X, Y)
where:

- X is an s-digit word and Y a c-digit word;
- both leading digits are nonzero;
- the b digits together are exactly 0, …, b−1.

Let M be coprime to b.

*Claim (sketched).* If s and c are long compared with log_b M, then
{(X mod M, Y mod M) : (X, Y) ∈ 𝒫} is exactly the set of all (x, y) with
x + y ≡ b(b−1)/2 (mod gcd(M, b−1)).

*Why.* 𝒫 is closed under swapping any two digit positions. A swap changes the
pair by (e−d)(b^i − b^j) within one word, or by ((e−d)·b^i, −(e−d)·b^j)
across the two words. Since b is a unit mod M, these moves generate (u, −u)
and (b−1)·u in each coordinate, and their orbit is the stated coset. A full
proof needs a covering argument showing that enough independent swaps exist.

*Evidence.* All 2,903,040 base-10 splits with (s, c) = (4, 6) confirm the
claim for all 39 moduli coprime to 10 from 3 to 99
([results](results/multiset-image-base10.json)). At M = 101 the words are too
short: a 4-digit word has only two base-100 blocks.

*Consequence.* By CRT, the part of a modulus sharing factors with b sees only
trailing digits. The project's edge theorems show that trailing digits plus
the digit sum leave candidates in every large base. So **no fixed-modulus
congruence argument can prove uniqueness.** A proof would need information
whose depth grows with b, from both ends at once. No known argument has that
shape.

### The only lead: the deficiency-2 shortfall

At exactly two missing digits, the public histograms show 423 candidates
against 488 predicted (bases 20–48, z ≈ −3). Deeper edge modelling and the
digit-sum coupling do not explain it, and it has no visible structure
([experiments §2](experiments.md#2-the-random-digit-heuristic-against-the-public-histograms)).

A real obstruction would show up as exactly this kind of shortfall, growing
as events get rarer. That makes it the one thing that could justify effort on
Path 3. Two cheap tests settle it:

1. **New data.** The public detailed search of bases 49 and 50 (51% and 7%
   done at the snapshot) will add deficiency-2 counts. Pre-register the
   statistic, model the exact checked sub-intervals, and see whether the
   shortfall persists.
2. **Rarer exact events.** If an obstruction suppresses rare events, it
   should also suppress exact hits in the analogues as they get rarer.
   - *Done so far:* thrice-nice base 16 came in at 241 against 264 predicted
     (0.91, about 1.4σ low). About half of that is the model's known
     simplification ([experiments §3](experiments.md#3-exact-hits-in-analogues-k-nice-numbers)).
     The rarest events tested, twice-nice bases 20–22 at 10⁻¹⁰ to 10⁻¹¹ per
     candidate, came in above prediction (14 against 12.7). So far there is
     no sign of suppression growing with rarity.
   - *Next:* twice-nice bases 24–26 (4, 39, and 50 predicted) go rarer
     still.

**Stop** Path 3 for good if the shortfall on new data is within 2σ of zero and
the analogue counts keep matching. Pursue it seriously only if a shortfall
appears and grows toward exact hits. Then study *which* digit configurations
are missing, looking for an arithmetic reason.

## Path 4. The frontier lottery

The public network searches bases in order, which is right: cost per expected
solution rises with the base.

| Bases | Chance of a nice number there | Time at today's public rate |
|---|---:|---:|
| Rest of 57, and 58 | 0.14% | ≈ 8 years |
| Through 60 | 0.19% | ≈ 100 years |
| Through 64 | 0.31% | ≈ 2,700 years |

Contributing compute is the only action that could produce a second nice
number this decade. It is a lottery ticket, not a research program. Speedups
do not change that: each 10× buys about 2–3 bases, and even 1000× (about 7
bases) leaves the odds under 1%. Even odds need about 10²³× over today's
methods, which is Path 1, not a speedup.

## What does not lead to a solution

| Activity | Why it cannot produce a true solution |
|---|---|
| Incremental search speedups | Each 10× buys 2–3 bases; even odds need about 10²³× |
| SAT/SMT/CNF solving | Measured over 10⁴× slower than enumeration where the answer is known |
| More family exclusions (repdigits, stretches, affine words, denominators) | Each removes a negligible sliver of candidates; they cannot sum to a proof |
| New congruences | Exhausted (Path 3) |
| Fixed-depth edge filters as proof tools | Provably leave candidates in every large base |
| Re-verifying the public search | Bases ≤ 48 were counted exhaustively in detailed mode, which the bugs did not affect, and I re-verified 10–35 exactly. Bases 49–54 hold only 0.003 expected nice numbers |
| Write-ups, and heuristic refinement for its own sake | Answers neither question; the heuristic tests that matter are the two in Path 3 |
| Near-miss transformations, output permutations, local search | No mechanism |

## Sources

- Public search client and changelog; the v3.3.0 entry says the unsound
  cross-check left detailed mode unaffected:
  [repository](https://github.com/wasabipesto/nice),
  [CHANGELOG.md](https://github.com/wasabipesto/nice/blob/main/CHANGELOG.md).
- Public data (2026-09-26 snapshots in `critique/results/`):
  [bases](https://data.nicenumbers.net/bases?select=*&order=id.asc),
  [search rate](https://data.nicenumbers.net/cache_search_rate_daily?order=date.asc).
- Digit-distribution theorems and their limits:
  [Maynard, arXiv:1510.07711](https://arxiv.org/abs/1510.07711);
  [Swaenepoel, squares with preassigned digits](https://webusers.imj-prg.fr/~cathy.swaenepoel/article_squares_AM.pdf).
- Lattice reduction for small-root problems: D. Coppersmith, "Small solutions
  to polynomial equations, and low exponent RSA vulnerabilities", *J.
  Cryptology* 10 (1997).
