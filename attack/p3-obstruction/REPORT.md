# Path 3, obstruction: is the deficiency-2 shortfall an arithmetic obstruction?

2026-09-26/27. Hypothesis: the 13% shortfall of near misses with exactly two missing digits (423 observed, 488 predicted, bases 20–48), together with the deficiency-1 counts, reflects an arithmetic obstruction that could scale into a proof that 69 is the only nice number.

## Verdict: killed

The shortfall is not an obstruction, and nothing here can grow into a nonexistence proof.

1. **It does not persist out of sample.** The pre-registered statistic on bases 49–50 gives **20 deficiency-2 numbers against 18.3 predicted** (ratio 1.10, z = +0.41). That is within 2σ of zero, which is the critique's stop condition for this lead. The model also fits the out-of-sample deficiency-3 and -4 bins to 0.1% (2,168 vs 2,171 and 137,280 vs 137,320).
2. **It has no structure.** I compared the 443 deficiency-2 numbers in bases 20–50 with exact conditional draws from the model on 25 categorical features and 6 residue tests. The deficit sits evenly across every configuration: each major category is at 0.82–0.95 of its expected count. An arithmetic obstruction forbids particular configurations and would concentrate the deficit; this one looks exactly like a Poisson dip in the total. Two features reach p < 0.1, where 2.5 are expected by chance.
3. **It does not grow in any direction a proof would need.**
   - Across bases: 0.88 for 20–33, 0.86 for 34–48, 1.10 for 49–50.
   - Toward exact hits: deficiency 1 has 4 observed against 3.7 expected in bases 20–50, and 4 against 2.4 in bases 10–19. Suppression at deficiency 1 by a factor of 4 or more is excluded (p = 0.014).
   - A nonexistence proof needs about 10⁻²⁰ suppression at base 300. The most this data could support is a constant 0.87.
4. **No modelling detail explains it, and no mechanism was found.** Deeper edges (critique), the digit-sum coupling (critique, and re-derived here by Monte Carlo), and the separate square and cube congruences (new here) each move the prediction by 1% or less.

**What remains open is narrow and does not matter for the goal.** The in-sample dip is about 3σ, or p ≈ 2% after looking across six bins. The public data cannot show it is noise: the out-of-sample test had only 5% power against a real 13% effect, and finishing the detailed search of bases 49 and 50 would bring it to only about 22%. Even if the dip were real, it is a featureless constant factor, which cannot yield a nonexistence proof. Path 3 via this lead should stop.

## 1. New data and the pre-registered test

**What changed since the 2026-09-26 snapshot** ([bases API](https://data.nicenumbers.net/bases?select=*&order=id.asc), fetched 2026-09-26 23:15; SHA-256 f40c40eb… in `results/near_misses.json`):

- **Bases ≤ 48:** unchanged.
- **Base 49:** detailed coverage grew from 5.3118×10¹⁵ to 5.3461×10¹⁵ (+3.4×10¹³, or 0.33% of the base). Only bins with at least 3 missing digits changed (for example, deficiency 3 went from 1,561 to 1,562). The deficiency-2 count stayed at 16.
- **Base 50:** detailed coverage grew from 4.756×10¹⁵ to 4.781×10¹⁵ (6.7% of the base), but the `bases` table still publishes no histogram. I recovered one from the [chunk caches](https://data.nicenumbers.net/chunks?base_id=eq.50): 32 of 100 chunks carry histograms covering 4.73×10¹⁵ candidates, 99% of base 50's detailed total.
- **Bases 52 and up:** no detailed coverage.
- **New field:** the `bases` table now has a `numbers` field. It lists every number with at most 2 missing digits for bases 22–49, and the list matches the histogram bin exactly in every base, so the actual near-miss numbers are public. I verified every one exactly.

So there is little detailed data newer than the snapshot. But bases 49–50 (9.1×10¹⁵ candidates) were never used in the critique's test, which pooled only the complete bases 20–48. They are the out-of-sample set.

**Checked sub-intervals.** The chunk caches give each chunk's histogram and checked count, but not which 10⁹-wide fields inside a partial chunk were checked. They are not a contiguous prefix: chunk 1133 has 38,041 detailed fields, then gaps. The caches also lag the `fields` table (44,015 cached versus 51,754 current fields in chunk 1133), and chunk 1133's histogram covers 1.195×10¹² fewer candidates than its stated count, so I used the histogram sums. The model depends on position only through the top digits, so I bracketed each partial chunk three ways: checked fields spread evenly over the chunk, a prefix, or a suffix.

Model M1 (the critique's exact top-2/bottom-3 model) over the checked chunks, from `scripts/new_data_test.py` → `results/new_data_test.json`:

| Base | Checked | Chunks (full + partial) | Def 2 observed | Def 2 M1 (bracket) | Def 3 obs / M1 | Def 4 obs / M1 |
|---:|---:|---|---:|---:|---:|---:|
| 49 | 5.345×10¹⁵ | 21 + 79 | 16 | 13.18–13.43 | 1,562 / 1,553–1,580 | 97,600 / 97,091–98,694 |
| 50 | 4.732×10¹⁵ | 0 + 32 | 4 | 4.48–4.93 | 606 / 553–605 | 39,680 / 36,235–39,506 |

- **Bracket choice.** For base 49 the deficiency-3 and -4 counts favour the even-spread bracket; for base 50 they favour the prefix bracket (606 vs 605.4, 39,680 vs 39,506). I use those brackets below. In every bracket the deficiency-2 conclusion is the same.
- **Pre-registered statistic.** With the exact digit-sum coupling applied, bases 49–50 give **20 observed vs 18.26 expected, z = +0.41**, Poisson P(X ≤ 20) ≈ 0.7. This is within 2σ, so the stop rule is met.
- **Power.** The test is weak.
  - If a 13.3% suppression were real, P(z < −2) was only 0.047.
  - The Bayes factor for "no suppression" against "ρ = 0.867" is 1.53, mild evidence against the shortfall.
  - Completing the detailed search of bases 49 and 50 gives about 100 expected events and 22% power. 80% power needs about 450 new events. Beyond base 50 only nice-only mode runs, so the public search will not settle it.

## 2. The actual near-miss numbers

**Sources.** Deficiency ≤ 2 numbers came from the public lists for bases 22–49, the critique's exhaustive recomputation for bases 10–20, and the base-50 chunk caches. Every number was re-verified exactly in `scripts/extract_near_misses.py` → `results/near_misses.json`. Counts: 443 at deficiency 2 and 4 at deficiency 1 in bases 20–50; 50 and 4 in bases 10–19.

**Model draws** (`scripts/model_mc.py`) are exact conditional samples, not rejection samples:

- n is uniform over the checked intervals, so the top 2 and bottom 3 digits of both powers are exact;
- the middle digits are uniform, conditioned on exactly b − r distinct values;
- the digit-sum class is imposed by rejection.

The closed-form weights equal the critique's exact occupancy formula. Against brute-force rejection sampling at bases 13 and 15, the sampler matches within Monte Carlo error on type, placement, edge involvement and zero-missing (`scripts/validate_mc.py`). I drew 4,000 deficiency-2 samples per base.

**Two expectations per category** (`scripts/analyze_structure.py`):

- *abs* = M1 count × digit-sum factor × model share. Totals 507.5. obs/abs shows where the rate deficit sits; overall it is 0.873.
- *shape* = the model share at the observed per-base totals, used for the χ² test of the configuration mix.

Selected results for bases 20–50 (all 25 features are in `results/structure_def2.log` and `.json`):

| Feature | Category: observed / abs-expected (ratio) | Shape χ² p |
|---|---|---:|
| Type | two doubled values 421/487.1 (0.86); one tripled value 22/20.4 (1.08) | 0.31 |
| Repeated value's copies | split between powers 408/485.7 (0.84); within cube 296/337.9 (0.88); within square 138/150.6 (0.92) | 0.27 |
| Zone of each repeated copy | square middle 440/522 (0.84); cube middle 798/912 (0.88); square bottom 166/175 (0.95); cube bottom 142/174 (0.82); square top 107/114 (0.94); cube top 97/113 (0.86) | 0.67 |
| Repeated copies in edge positions | 0: 112/135 (0.83); 1: 184/211 (0.87); 2: 115/124 (0.92); ≥3: 32/37.5 (0.85) | 0.82 |
| A repeat adjacent within one power | yes 57/54.1 (1.05); no 386/453 (0.85) | 0.12 |
| 0 missing / b−1 missing / 1 missing | 25/30.4 (0.82) / 19/30.1 (0.63) / 14/22.7 (0.62) | 0.79 / 0.15 / 0.17 |
| Parity of the missing pair | both odd 86/120 (0.72); mixed 246/260 (0.95); both even 111/128 (0.87) | 0.083 |
| Leading digit of n² / n³ | — | 0.68 / 0.46 |
| n mod q, q = 2–9, 11, 13 | smallest p: q = 7 | 0.067–0.81 |
| Rate by b mod q, q = 2–6 | heterogeneity | 0.13–0.69 |

**Exact residue tests** (`scripts/exact_residue_test.py`). The model's exact distribution of n mod b³ given deficiency 2 comes from summing top-configuration weights over all b³ bottom residues. It independently reproduces every M1 expectation to within 0.2%.

- Surprise statistics with a parametric bootstrap:
  - n mod b: p = 0.071 (PIT KS p = 0.71);
  - n mod b²: p = 0.36;
  - n mod b³: p = 0.46.
- n mod (b+1) against uniform: p = 0.49.
- Position in the checked range: p = 0.70.
- The Monte Carlo-estimated residue p-values in `structure_def2.log` (0.013 for n mod b, 0.000 for n mod b²) are an artifact: probabilities estimated from the same finite sample over up to b² categories. The exact test supersedes them.

**A new modelling detail.** Imposing the square's and the cube's digit-sum congruences separately, not just their sum, changes the deficiency-2 expectation by a factor of 0.989 ± 0.023, and leaves the configuration mix unchanged.

**Dispersion.** Per-base deficiency-2 counts have χ² = 26.2 on 23 degrees of freedom against M1 (p = 0.29). There is no overdispersion and no base-specific pattern.

**Deficiency-1 numbers** (`scripts/def1_and_trend.py`), with the positions of the repeated digit counted from the most significant end:

| Base | n | Missing | Repeated | Where |
|---:|---:|---:|---:|---|
| 10 | 59 | 6 | 3 | split: sq[0], cu[3] |
| 15 | 2494 | 10 | 1 | split: sq[5], cu[5] |
| 17 | 6788 | 5 | 13 | split: sq[5], cu[4] |
| 17 | 9278 | 0 | 4 | cube: cu[6], cu[9] |
| 20 | 149652 | 3 | 9 | split: sq[1], cu[4] |
| 24 | 1852215 | 18 | 7 | split: sq[1], cu[0] |
| 40 | 4134931983708 | 27 | 6 | cube: cu[11], cu[19] |
| 45 | 330169542960890 | 43 | 9 | square: sq[6], sq[8] |

Observed over expected (M1 × exact digit-sum coupling), by deficiency:

| Bases | Def 1 | Def 2 | Def 3 | Def 4 |
|---|---|---|---|---|
| 10–19 | 4/2.4 (1.64) | 50/53.2 (0.94) | 476/463 (1.03) | 2,105/2,178 (0.97) |
| 20–48 | 4/3.6 (1.11) | 423/489.2 (0.865, z −2.99) | 33,430/33,641 (0.994) | 1,432,803/1,433,361 (1.000) |
| 49–50 | 0/0.1 | 20/18.3 (1.10, z +0.41) | 2,168/2,171 (0.999) | 137,280/137,320 (1.000) |

## 3. Mechanism, and why none can scale from here

- **Nothing to explain arithmetically.** No configuration is under-represented beyond chance: 2 of 25 features have p < 0.1, against 2.5 expected. The lowest ratios (1 or b−1 missing, 0.62–0.63; both missing values odd, 0.72) have 14–86 events each and were not predicted. After multiplicity none is significant. None has an arithmetic reason beyond what the model already contains: leading digits are exact in M1, and the parity of digit sums is part of the digit-sum class. A proportional, structureless deficit of 64 events out of 507 is what a 3σ fluctuation of the total looks like.
- **No growth with the base or with rarity.**
  - By base range the ratios are 0.88, 0.86 and 1.10.
  - By deficiency the ratio goes from 1.000 (deficiency 4) to 0.994 (3) to 0.87 (2) to 1.09 (1). That is not monotone.
  - A model where suppression grows toward exact hits (ρ₁ ≤ ρ₂ ≤ ρ₃, isotonic maximum likelihood) fits ρ₁ = ρ₂ = 0.875, ρ₃ = 0.994. All of its likelihood gain (2ΔlogL = 9.7) comes from the in-sample deficiency-2 bin that selected the hypothesis. The deficiency-1 data exclude ρ₁ ≤ 0.25 (p = 0.014) but cannot tell 0.87 from 1.
- **A constant factor cannot matter.** Nonexistence needs the pandigital event suppressed by more than 20 orders of magnitude at base 300, while deficiencies 3–4 stay within 0.1% of the model (they do, including out of sample). An obstruction acting only at deficiency 2 but not at deficiency 3 would need a global trigger at "at least b−2 distinct values". Any such trigger would also have to bite at deficiency 1, and there the counts are at or above the model.
- **Multiplicity 1 is not special here.** The only multiplicity-specific arithmetic, the digit-sum target k·b(b−1)/2 mod (b−1), is already in the model and reproduces twice- and thrice-nice counts (95 vs 97). The separate square and cube congruences add nothing (0.989 ± 0.023).

**What would reopen this:** a public detailed search reaching about 450 more deficiency-2 events with a ratio still near 0.87, and a configuration class carrying the deficit. Neither is in prospect.

## Scope, exactly

- **Deficiency-2 lists.** Exhaustive for bases 10–49 in the public intervals, plus the 32 base-50 chunks with histograms (6.7% of base 50). The other 68 base-50 chunks, about 5×10¹³ candidates, have detailed checks but no published histogram and were not used.
- **Verification.** Bases 37–49 rely on public counts. Bases 20–35 were independently recomputed by the critique. I verified every listed number individually.
- **Sub-intervals.** Partial-chunk sub-intervals are bracketed, not exact. The bracket width (0.25 events for base 49, 0.45 for base 50) is under a tenth of the Poisson noise.
- **Model.** M1 uses exact top-2 and bottom-3 digits. Deeper-edge sensitivity is from the critique (under 0.3% at deficiency 2).
- **No new enumeration.** None was needed, since the public lists covered bases up to 49. The machine load was 1 core throughout.
- **Side effect.** One run created `critique/scripts/__pycache__/digit_sum_coupling.cpython-314.pyc`. I deleted it, and the scripts now set `sys.dont_write_bytecode`. The 23:37 timestamp on `tail_validation.cpython-314.pyc` there may also be from my imports; I cannot tell it apart from other agents' runs. Bytecode caches are regenerable and nothing else outside `attack/p3-obstruction/` was touched.

## Files and reproduction

All paths are under `attack/p3-obstruction/`. Run from the project root; each command takes under a minute on one core.

```sh
python3 attack/p3-obstruction/scripts/extract_near_misses.py   # verify public near-miss lists
python3 attack/p3-obstruction/scripts/new_data_test.py          # pre-registered test, bases 49-50
python3 attack/p3-obstruction/scripts/validate_mc.py            # sampler vs brute force
python3 attack/p3-obstruction/scripts/model_mc.py --per-base 4000 --deficiency 2
python3 attack/p3-obstruction/scripts/model_mc.py --per-base 2000 --deficiency 1 --seed 11
python3 attack/p3-obstruction/scripts/analyze_structure.py      # 25 features, b mod q
python3 attack/p3-obstruction/scripts/exact_residue_test.py     # exact n mod b^k, n mod b+1
python3 attack/p3-obstruction/scripts/def1_and_trend.py         # deficiency 1, trend, power
```

- `data/`: API pulls from 2026-09-26: `bases-now.json`, `chunks-{49,50}.json`, `chunks-{49,50}-numbers.json` and `openapi.json`.
- `scripts/common.py`: shared loaders, and the choice of checked intervals.
- `results/`:
  - `near_misses.json`;
  - `new_data_test.json`;
  - `model_mc_def{1,2}.pkl` and `.log`;
  - `structure_def2.{json,log}`;
  - `exact_residue_def2.{json,log}`;
  - `def1_and_trend.{json,log}`.

## Sources

- Public data API (PostgREST), fetched 2026-09-26:
  - [bases](https://data.nicenumbers.net/bases?select=*&order=id.asc);
  - chunks for [base 49](https://data.nicenumbers.net/chunks?base_id=eq.49&order=range_start.asc) and [base 50](https://data.nicenumbers.net/chunks?base_id=eq.50&order=range_start.asc);
  - [fields](https://data.nicenumbers.net/fields?chunk_id=eq.1133&limit=3);
  - [schema](https://data.nicenumbers.net/).
- Upstream client: [wasabipesto/nice](https://github.com/wasabipesto/nice).
- Critique inputs:
  - [experiments.md §2](../../critique/experiments.md) (M1, the deficiency-2 shortfall, edge sensitivity, digit-sum coupling);
  - [research-directions.md, Path 3](../../critique/research-directions.md) (pre-registered test and stop rule);
  - `critique/results/tail-validation.json` and `histogram-recompute.json`.
