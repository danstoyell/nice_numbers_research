# Supporting experiments

2026-09-26, Apple M4 (10 cores, 16 GB), Python 3.14, Apple clang 17.
Everything here is either an exact computation or explicitly labelled as a
heuristic expectation. Scripts are in `critique/scripts/`, outputs in
`critique/results/`. The project's own `scripts/verify.py` is used as the
independent checker throughout.

**Scope warning.** Sections 1–3 test and apply a heuristic; they are evidence,
not proof. Sections 4–6 are exact computations whose scope is stated in each.

## 1. Reachability: where a second nice number would be

**Question.** Under the conditional random-digit model the project already
uses ([existence-counting.md](../research/existence-counting.md)), how much
expected "nice-number mass" lies in each base, and what would it cost to
reach it?

**Method.** [`reachability.py`](scripts/reachability.py) reimplements that
model exactly, using CRT counts of candidates that pass the digit-sum and
last-digit filters. It agrees with the note's saved values to 10⁻¹¹ in
log₁₀ at all ten saved bases. It adds three things:

- cumulative expectation from the public frontier upward (bases ≤ 54
  complete, base 57 12.44% done, per the 2026-09-26 API snapshot);
- years at the public network's nice-only throughput on 2026-09-26, about
  5×10¹⁶ integers of range per day
  ([rate snapshot](results/public-search-rate-2026-09-26.json));
- an idealized "every edge digit" search cost. Here 2·(root digits) − 2
  leading and trailing output digits must be distinct before a full check;
  this is roughly what the public client's MSD, LSD, and cross-end filters
  achieve.

**Results** ([full table, bases 10–600](results/reachability.json)):

| Base | log₁₀ candidates | Expected nice in base | Cumulative unsearched | P(≥1 so far) | Years at current rate (cumulative) | log₁₀ ideal checks per expected solution |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 1.7 | 0.050 | — | — | — | 2.5 |
| 57 | 19.8 | 0.0011 | 0.00097 | 0.10% | 2.8 | 19.7 |
| 58 | 20.0 | 0.00044 | 0.0014 | 0.14% | 7.9 | 20.2 |
| 60 | 21.2 | 0.00045 | 0.0019 | 0.19% | 98 | 21.1 |
| 64 | 22.6 | 0.00085 | 0.0031 | 0.31% | 2.7×10³ | 22.5 |
| 70 | 25.7 | 0.0015 | 0.0056 | 0.56% | 3.4×10⁶ | 24.9 |
| 80 | 30.3 | 0.0016 | 0.013 | 1.3% | 1.3×10¹¹ | 28.8 |
| 100 | 39.9 | 0.048 | 0.14 | 13% | 4.6×10²⁰ | 36.5 |
| 118 | 48.4 | 0.32 | 0.96 | 62% | 2.3×10²⁹ | 43.3 |
| 122 | 50.7 | 1.6 | 3.0 | 95% | 3.0×10³¹ | 44.8 |
| 150 | 65.2 | 58 | 345 | ≈100% | 10⁴⁶ | 55.9 |
| 200 | 92.0 | 8.2×10⁶ | 2.8×10⁷ | ≈100% | 10⁷³ | 75.4 |

- The expected total over every base searched so far (12–54, plus 12% of 57)
  is **0.054**, so the model gave about a 5% chance of any success there.
- Base 10 alone had **0.050**.
- The cumulative unsearched expectation passes ln 2 (odds above 50%) at base
  118, and the per-base expectation first exceeds 1 at base 122.
- Solution density, not count, sets search cost: it falls roughly like e^−b.
  Cost per expected solution rises monotonically, so the cheapest place to
  search is always the lowest unsearched base.

```sh
python3 critique/scripts/reachability.py --max-base 600
```

## 2. The random-digit heuristic against the public histograms

**Question.** The public project's detailed mode records, for every
candidate in a base's interval, the number of distinct digits across n² and
n³. Bases 10–48 are complete: about 8×10¹⁵ candidates. Does the tail of that
histogram behave as the heuristic assumes?

**Data integrity first.**
[`recompute_histograms.py`](scripts/recompute_histograms.py) drives an
independent C enumerator, [`histogram.c`](scripts/histogram.c). It advances n
by digit-array additions (n² += 2n+1, n³ += 3n²+3n+1), seeded per thread by
exact 128-bit arithmetic, and counts distinct digits with a 64-bit mask.

- It recomputed **every bin of every public histogram for bases 10–35**:
  21 bases, 5.8×10¹⁰ candidates, about 9 minutes in total.
- **All 21 histograms match the public data exactly.**
- Every candidate with at most two missing digits (219 of them) was
  re-verified with `scripts/verify.py`.

Bases 37–48 were not recomputed (about 2 weeks for 37–44 and 2 years for
45–48 on this laptop); they rely on the public data.
([results](results/histogram-recompute.json);
[snapshot](results/public-bases-2026-09-26.json), SHA-256 recorded inside.)

**Models** ([`tail_validation.py`](scripts/tail_validation.py)):

- **M0, uniform legal strings.** The b digits are uniform, and both leading
  digits are uniform on 1..b−1. Exact inclusion–exclusion, checked by brute
  force for b ≤ 5.
- **M1, exact edges with a random middle.** The top 2 digits of each power
  follow their exact distribution over the interval, from exact
  integer-root segment weights. The bottom 3 digits follow their exact
  distribution over residues mod b³. The other b−10 digits are uniform.
  Middle-digit occupancy probabilities are exact rationals, checked by brute
  force.

**Pooled results, bases 20–48** (per-base values in
[tail-validation.json](results/tail-validation.json)):

| Missing digits | Observed | M0 | M1 | Obs / M0 | Obs / M1 | z vs M1 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 (nice) | 0 | 0.011 | 0.009 | — | — | — |
| 1 | 4 | 4.5 | 3.8 | 0.89 | 1.06 | +0.1 |
| 2 | 423 | 571.1 | 488.1 | 0.74 | **0.867** | −2.9 |
| 3 | 33,430 | 38,935.6 | 33,640.5 | 0.86 | 0.994 | −1.1 |
| 4 | 1,432,803 | 1,650,172.6 | 1,433,361.1 | 0.87 | 1.000 | −0.5 |
| 5 | 40,141,669 | 46,083,377.5 | 40,195,445.9 | 0.87 | 0.999 | (−8.5) |
| 6 | 774,039,670 | 884,584,035.7 | 775,119,574.6 | 0.88 | 0.999 | (−38.8) |

**Reading.**

- The uniform model is 12–15% too optimistic throughout. Nearly all of that
  comes from the exact structure of the last and leading digits; after
  correcting the edges, M1 matches to 0.6% or better from 3 to 6 missing
  digits.
- The z-scores in parentheses reflect the enormous counts: a 0.1% residual is
  "significant" at 10⁸–10⁹ events. It shrinks as the edges are modelled more
  deeply (next table), so it is model resolution, not a signal.
- The mean distinct fraction agrees with M1 to within 0.002 in every base
  from 17 upward, and within 0.0002 from base 34 upward.

**Sensitivity to edge depth** (Monte Carlo over exact edges, 4×10⁵ samples
per base, bases 30–48;
[tail-sensitivity.json](results/tail-sensitivity.json)):

| Missing digits | Observed | M1 (2 top, 3 bottom) | M1 (3, 4) | M1 (4, 5) |
|---:|---:|---:|---:|---:|
| 2 | 337 | 390.1 (0.864) | 389.6 (0.865) | 389.2 (0.866) |
| 3 | 30,854 | 31,051.7 (0.994) | 30,994.0 (0.995) | 30,939.4 (0.997) |
| 4 | 1,395,486 | 1,397,680 (0.998) | 1,394,786 (1.001) | 1,391,948 (1.003) |

**The deficiency-2 shortfall.** At exactly two missing digits the data sit
13% below the model, about 3σ, in both halves of the range:

- bases 20–33: 133 observed vs 151.1 predicted (0.88);
- bases 34–48: 290 observed vs 337.0 predicted (0.86).

Two candidate explanations were ruled out:

- **Deeper edges** change the prediction by under 0.3%.
- **The digit-sum identity** couples each digit multiset to n mod (b−1),
  which the model ignores. Computing that coupling exactly
  ([`digit_sum_coupling.py`](scripts/digit_sum_coupling.py),
  [results](results/digit-sum-coupling.json)) changes predicted deficiency-1
  counts by −20% to +4%, depending on the base, but deficiency-2 counts only
  by −0.3% to +1.6%. It cannot produce a 13% shortfall.

The shortfall also has no visible structure. Across the 162 deficiency-2
events in bases 20–35, the duplicated values fall within the square, within
the cube, or split between them in the proportions expected from
exchangeable positions: 49, 97, and 156 against 46.2, 105.1, and 150.7. Zero
and b−1 are missing at the naive rate
([`near_miss_placement.py`](scripts/near_miss_placement.py),
[results](results/near-miss-placement.json)).

With six bins examined, a single bin this far out has a look-elsewhere
p-value of about 2% (two-sided Poisson p ≈ 0.003 per bin). It is the only
anomaly found, it does not trend with the base, and even a constant 13%
suppression would change no conclusion. The follow-up protocol
is in [research-directions, Path 3](research-directions.md#the-only-lead-the-deficiency-2-shortfall).

```sh
python3 critique/scripts/recompute_histograms.py --bases 10 12 13 14 15 17 18 19 20 22 23 24 25 27 28 29 30 32 33 34 35
python3 critique/scripts/tail_validation.py
python3 critique/scripts/tail_sensitivity.py --samples 400000 --min-base 30
```

## 3. Exact hits in analogues (k-nice numbers)

**Question.** The tail test probes near misses. Can the model be tested on
*exact* events, for the same exponents?

**Analogues.** Call n *k-nice* in base b if n² and n³ together contain every
digit exactly k times (total length k·b); nice numbers are the case k = 1.
The square/cube algebra, carry structure, and digit-sum congruence are
unchanged: the target is n²(n+1) ≡ k·b(b−1)/2 mod (b−1). Only the length
condition shifts. Larger k moves the predicted onset of solutions down: from
about base 120 for k = 1 to about base 15 for k = 2 and about base 9 for
k = 3. There, exhaustive search is cheap.

**Model.** The same conditional construction the project uses for nice
numbers: exact last digits (x, y), the digit-sum class, and the remaining
k·b−2 digits uniform among legal strings. [`twice_nice.py`](scripts/twice_nice.py)
computes it exactly in rational arithmetic (`--mult k`). At k = 1 it
reproduces the nice-number expectation for base 10 (0.0504).

**Search.** `histogram.c`, in exact-multiplicity mode, enumerates every
integer in each exact interval. Each hit is re-verified in Python, and for
intervals under 3×10⁶ an independent Python brute force produced identical
solution sets.

<!-- ANALOGUE_TABLES -->
**k = 2** ([results](results/twice-nice.json)):

| Base | Candidates | Expected | Found | Solutions |
|---:|---:|---:|---:|---|
| 5 | 10 | 0.32 | 0 | — |
| 6 | 30 | 0.14 | 0 | — |
| 7 | 50 | 0.18 | 1 | 173 |
| 9 | 670 | 0.14 | 0 | — |
| 10 | 5,358 | 0.42 | 1 | 6534 |
| 11 | 17,921 | 0.45 | 0 | — |
| 12 | 36,856 | 0.11 | 0 | — |
| 14 | 716,121 | 0.19 | 1 | 1641939 |
| 15 | 6,771,952 | 1.02 | 1 | 7218806 |
| 16 | 2.5×10⁷ | 1.06 | 1 | 32006130 |
| 17 | 6×10⁷ | 0.95 | 1 | 114542504 |
| 19 | 1.5×10⁹ | 2.98 | 4 | 2538864573, 2835013373, 2895211416, 3714571043 |
| 20 | 1.6×10¹⁰ | 1.99 | 4 | 11302355902, 14354028609, 19794571393, 20836371375 |
| 21 | 6.7×10¹⁰ | 7.24 | 5 | 55056876615, 55871180764, 56711438444, 60226749060, 72003849760 |
| 22 | 1.7×10¹¹ | 3.50 | 5 | 279564695073, 322978806156, 355675306532, 405883732758, 428953190595 |
| **Total** | | **20.7** | **24** | observed/expected 1.16; Poisson P(≤24) = 0.80, P(≥24) = 0.26 |

Model predictions for the next bases (not searched): base 24: 4, base 25: 39, base 26: 50, base 27: 26.

**k = 3** ([results](results/thrice-nice.json)):

| Base | Candidates | Expected | Found | Solutions |
|---:|---:|---:|---:|---|
| 5 | 51 | 0.23 | 0 | — |
| 6 | 137 | 0.30 | 0 | — |
| 8 | 4,798 | 0.71 | 0 | — |
| 9 | 63,778 | 3.22 | 7 | 72150, 78674, 108518, 112291, 118382, 118418, 122342 |
| 10 | 535,841 | 8.37 | 10 | 497375, 539019, 543447, 586476, 589629, 601575, 646479, 858609, 895688, 959097 |
| 13 | 1.2×10⁸ | 13.15 | 16 | 16 values, listed in the JSON |
| 14 | 2.1×10⁹ | 50.21 | 38 | 38 values, listed in the JSON |
| 16 | 10¹¹ | 263.67 | 241 | 241 values, listed in the JSON |
| **Total** | | **339.9** | **312** | observed/expected 0.92; Poisson P(≤312) = 0.07, P(≥312) = 0.94 |

Model predictions for the next bases (not searched): base 18: 610.

Bases missing from a table are excluded by the length condition, or have zero expectation because the digit-sum congruence has no solution (for odd k, when b ≡ 3 mod 4).
<!-- /ANALOGUE_TABLES -->

Two decimal examples:

- **Twice-nice:** 6534² = 42693156 and 6534³ = 278957081304, which together
  use each digit exactly twice.
- **Thrice-nice:** the ten base-10 thrice-nice numbers are 497375, 539019,
  543447, 586476, 589629, 601575, 646479, 858609, 895688, and 959097.

**Reading.** Across <!-- ANALOGUE_TOTAL_EVENTS -->336<!-- /ANALOGUE_TOTAL_EVENTS --> exact hits the counts come in at 0.93 of
prediction: twice-nice 16% above, thrice-nice 8% below (one-sided Poisson
P = 0.07).

- **Part of the gap is expected.** The model fixes only the last digits
  exactly. On the near-miss data, that simplification over-predicts by about
  4.5% relative to the exact-edge model
  ([`model_calibration.py`](scripts/model_calibration.py),
  [results](results/model-calibration.json)).
- **Rarer events are not more suppressed.** The rarest events tested,
  twice-nice numbers in bases 20–22 at 10⁻¹⁰ to 10⁻¹¹ per candidate, come in
  above prediction: 14 against 12.7.
- **The regime is still far from nice numbers.** These probabilities are
  many orders of magnitude above a nice number's 10⁻²³ at base 57. The test
  supports the model's *form* at exact hits; it cannot reach the nice-number
  regime directly.

```sh
python3 critique/scripts/twice_nice.py --max-base 22 --model-only-max-base 40 --threads 10
python3 critique/scripts/twice_nice.py --mult 3 --max-base 16 --model-only-max-base 18 \
    --output critique/results/thrice-nice.json
python3 critique/scripts/model_calibration.py
```

## 4. SAT scaling on bases whose answer is known

**Question.** The SAT/CNF tracks produced only UNKNOWN at bases 128–512. How
does the same encoding perform where brute force has already settled the
answer?

**Method.** [`sat_scaling.py`](scripts/sat_scaling.py) builds the project's
validated Horner-digit CNF with `scripts/direct_cnf.py`'s `Circuit`,
unchanged: exact interval constraint, Karatsuba products, Horner packing,
occupancy decoder. It solves with CaDiCaL 1.9.5 through PySAT, enumerating
all solutions. Each base runs in its own process with a hard wall-clock kill.

*Caution:* PySAT's CaDiCaL binding does not implement `interrupt()`, so a
timer-based limit is silently ignored, and my first harness had this bug.

- Bases 10–20 were timed with that first harness. Each finished long before
  its limit, so the ignored timer made no difference, and the machine was
  otherwise idle.
- Bases 22 and 24 were rerun with a process-kill harness, as two
  single-threaded jobs in parallel on the otherwise idle 10-core machine.

<!-- SAT_TABLE -->
| Base | Candidates | After digit-sum and last-digit filters | CNF variables / clauses | CaDiCaL time | Per candidate | × naive enumerator |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 53 | 15 | 1,097 / 4,138 | 0.07 s | 1.36 ms | 15,976 |
| 12 | 186 | 17 | 1,727 / 6,620 | 0.17 s | 0.92 ms | 10,872 |
| 13 | 212 | 30 | 2,615 / 10,442 | 1.38 s | 6.51 ms | 76,538 |
| 14 | 405 | 46 | 3,041 / 12,197 | 1.82 s | 4.50 ms | 52,920 |
| 17 | 7,720 | 425 | 4,189 / 16,348 | 13.29 s | 1.72 ms | 20,248 |
| 18 | 9,459 | 619 | 4,749 / 18,618 | 18.46 s | 1.95 ms | 22,956 |
| 20 | 101,055 | 7,446 | 6,568 / 26,077 | 158 s | 1.57 ms | 18,451 |
| 22 | 422,139 | 65,787 | 9,576 / 39,181 | 2,400 s (TIMEOUT, killed at limit) | >5.69 ms | > 66,887 |
| 24 | 1,135,124 | 74,030 | 9,473 / 37,832 | 1,605 s | 1.41 ms | 16,638 |
<!-- /SAT_TABLE -->

**Comparison with enumeration.** On the same laptop, `histogram.c` processes
about 1.2×10⁷ candidates per second per thread (8×10⁻⁸ s each) while
computing every digit of every candidate, with no filters. A filtered
nice-only checker would be faster still.

<!-- SAT_CONCLUSION -->
**Result.** Across the bases that finished (13–24), solve time grows as roughly N^0.83 in the number of candidates N (log–log fit over 6 bases). Base 22 did not finish within its 40-minute limit (over 5.7 ms per candidate), taking longer than base 24 with fewer candidates. So solver times are erratic, and leaving the timeout out of the fit flatters SAT. The cost per candidate stays in the millisecond range: about 1.4 ms at base 24, or about 1.7×10⁴ times a naive single-threaded enumerator. Adding the digit-sum filter to the CNF could save at most its filtering factor (about 10–20×), which still leaves a gap of at least three orders of magnitude.

Take the fitted sub-linear exponent at face value, which is optimistic because CDCL costs on arithmetic circuits usually grow faster at scale. Base 57 would then need about 3×10¹⁴ single-core seconds, about 8×10⁶ core-years. An edge-pruned enumerator needs about 5.5×10¹⁶ checks for the same base: a few hundred core-years at 10⁷ checks per core-second, and about three calendar years for the public GPU fleet. The SAT runs at bases 128–512 were therefore never going to end in anything but UNKNOWN.
<!-- /SAT_CONCLUSION -->

## 5. A gap in the public coverage record

The exact interval for each base comes from `scripts/verify.py`, using
integer roots. For **every base ≡ 2, 3, 4 (mod 5) from 12 to 57 except 27**,
both the public `bases` table and the public `chunks` table end one short of
it. Their exclusive upper bound equals the exact inclusive maximum.

This matches the off-by-one the public project fixed in client v3.3.0
("dropped one trailing candidate per base where base % 5 ∈ {2,3,4}"). The
stored field bounds were apparently not regenerated. Base 27's range happens
to end at 3¹⁶, which covers its endpoint.

**Checked directly.** All 26 omitted endpoints have exactly b total digits.
None is nice, or even close: at most 67% of their digits are distinct
([results](results/public-endpoint-gap-check.json)). The public record
through base 57 is therefore complete in fact, though not as stored.

## 6. No hidden congruences

**Question.** Could a modulus other than b−1 give a further necessary
condition from pandigitality alone?

[`multiset_image.py`](scripts/multiset_image.py) enumerates all 2,903,040
splits of the digits 0–9 into a 4-digit "square" word and a 6-digit "cube"
word, with leading digits nonzero. For each modulus M it compares the set of
realizable (X mod M, Y mod M) with the set the digit-sum congruence allows.

- For all 39 moduli coprime to 10 from 3 to 99, **the two sets are
  identical**.
- At M = 101 the words are too short: a 4-digit word has only two base-100
  blocks, and 202 of 10,201 pairs are missed.

The general argument, and why this ends the search for new congruences, is in
[research-directions, Path 3](research-directions.md#why-modular-arguments-cannot-work-no-hidden-congruences).
[Results](results/multiset-image-base10.json).

```sh
python3 critique/scripts/multiset_image.py $(python3 -c "from math import gcd; print(*[m for m in range(2,100) if gcd(m,10)==1], 101)")
```

## Sources

- Public data API, snapshots fetched 2026-09-26:
  [bases](https://data.nicenumbers.net/bases?select=*&order=id.asc),
  [chunks](https://data.nicenumbers.net/chunks?select=base_id,range_start,range_end&order=range_end.desc&limit=2000),
  [daily search rate](https://data.nicenumbers.net/cache_search_rate_daily?order=date.asc).
- Public client changelog (v3.3.0 off-by-one fix):
  [CHANGELOG.md](https://github.com/wasabipesto/nice/blob/main/CHANGELOG.md).
- PySAT solver interface:
  [pysathq.github.io](https://pysathq.github.io/docs/html/api/solvers.html).
- Conditional model:
  [research/existence-counting.md](../research/existence-counting.md).
