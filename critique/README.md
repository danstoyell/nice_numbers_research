# Critique of the nice-number research

An independent review, written 2026-09-26, of the work in `RESEARCH_LOG.md`,
`research/`, `scripts/`, and `results/`, with new experiments to test its
premises. Nothing else in the project was modified.

Success means a true solution and nothing less: a second nice number (found,
or proved to exist) or a proof that 69 in base 10 is the only one.

## Bottom line

1. **The mathematics is sound; the strategy is not.** Proofs I rechecked are
   correct, and validation and reproducibility are exemplary. But nearly all
   effort went into activities that could not move either goal: excluding
   families of negligible size (repdigits, stretches, affine outputs), and SAT
   solving at bases where SAT is hopeless.
2. **Uniqueness is almost certainly false, so a nonexistence proof is not a
   realistic goal.** The project's own random-digit model predicts more than
   10²⁰ nice numbers in base 300, and it survives every test available:
   - the public near-miss histograms (about 8×10¹⁵ candidates) match it to
     within 1% at 3–6 missing digits;
   - "twice-nice" and "thrice-nice" numbers, same-algebra analogues with
     reachable solutions, occur at the predicted rate (<!-- ANALOGUE_SHORT -->336 exact hits against 361 predicted<!-- /ANALOGUE_SHORT -->).
   Modular arguments provably cannot help: the only congruence pandigitality
   implies is the digit-sum one.
3. **A second nice number almost certainly exists, but it is out of reach.** The
   odds pass 50% only by base ~118; reaching that needs about 10⁴³ idealized
   checks, or about 10²⁹ years at the public network's current rate. The
   reachable chance over bases 57–64 is about 0.1–0.3%.
4. **SAT cannot change this.** On bases whose answer is known, the project's
   CNF costs over a millisecond per candidate, 10⁴–10⁵ times slower than plain
   enumeration, and its times are erratic (base 22 timed out while base 24
   finished). Even extrapolating its fitted sub-linear growth, base 57 alone
   would take about 10⁷ core-years, against a few hundred for an edge-pruned
   enumerator.
5. **The public search is further along than the research notes acknowledge,
   and its data check out.** Its client already implements the
   "both ends" search the notes treat as open. Its histograms for bases 10–35
   match an independent recomputation exactly. Its stored intervals omit one
   valid candidate in 26 bases; all 26 are now checked, and none is nice.
6. **Every route to a true solution now needs a new idea.** The directions
   document is limited to those routes:
   - a search method that forces about 90% of output digits distinct before
     per-candidate work (today's best is 40%);
   - a new technique for proving existence;
   - a nonexistence proof, which all evidence so far contradicts (two cheap
     tests would settle whether it deserves any effort);
   - the frontier lottery, at 0.1–0.2% this decade.

## What would change these conclusions

Either of these would reopen the uniqueness question and justify real
investment in looking for an obstruction:

- the deficiency-2 shortfall persisting on new data (bases 49–50) and growing
  toward exact hits;
- twice-nice counts at bases 24–26, or thrice-nice counts beyond base 16,
  falling systematically below the model as events get rarer. So far the
  rarest events tested (twice-nice, bases 20–22) are on or above prediction.

The reachability conclusion would change only with a search method that
forces well over 40% of the output digits distinct before paying
per-candidate costs; about 90% is needed for base ~120 to be feasible.
[research-directions.md](research-directions.md) says how to test each
(Paths 1 and 3).

## What to read

| File | Contents |
|---|---|
| [critique.md](critique.md) | The critique: verdict, weaknesses, missed prior art, track-by-track table, corrections, and what was checked |
| [research-directions.md](research-directions.md) | The only four routes to a true solution: a middle-digit search breakthrough, an existence proof, a nonexistence proof, and the frontier lottery. Each comes with what it needs, honest odds, and a stopping rule, plus a list of what cannot produce a solution |
| [experiments.md](experiments.md) | Six supporting experiments with methods, results, and reproduction commands |

## New results produced by this review

- **Twice- and thrice-nice numbers exist at the predicted rate.** Here n² and
  n³ together use every digit exactly twice (or three times). Example:
  6534² = 42693156 and 6534³ = 278957081304. <!-- ANALOGUE_SENTENCE -->24 twice-nice numbers through base 22 against 20.7 predicted, and 312 thrice-nice numbers through base 16 against 339.9 predicted<!-- /ANALOGUE_SENTENCE -->
- **The random-digit model passes a large-sample tail test** once the leading
  and trailing digits are modelled exactly. There is one unexplained ~3σ
  shortfall, at exactly two missing digits.
- **Independent recomputation** of the public histograms for bases 10–35
  (5.8×10¹⁰ candidates) matches every bin.
- **A public coverage gap**: 26 omitted endpoint candidates. All checked;
  none is nice.
- **No hidden congruences.** For moduli coprime to b, pandigital splits
  realize exactly the digit-sum class. Checked exhaustively in base 10 for
  M ≤ 99, with the general argument sketched.
- **SAT scaling measured** on bases 12–<!-- SAT_MAX_BASE -->24<!-- /SAT_MAX_BASE -->. The measurement also
  showed that PySAT's CaDiCaL binding silently ignores `interrupt()`-based
  time limits.

## Layout and reproduction

- `scripts/`:
  - `reachability.py`: expected counts, cumulative odds, and costs;
  - `tail_validation.py`, `tail_sensitivity.py`, `digit_sum_coupling.py`,
    `near_miss_placement.py`, `model_calibration.py`: the heuristic test;
  - `histogram.c` with `recompute_histograms.py`: the independent enumerator;
  - `twice_nice.py`: the k-nice analogues (`--mult 2` or `--mult 3`);
  - `sat_scaling.py`: SAT timing;
  - `multiset_image.py`: the congruence check.
- `results/`: JSON outputs, plus dated snapshots of the public API data
  (`public-bases-2026-09-26.json`, `public-search-rate-2026-09-26.json`).

Each experiment's commands are listed in [experiments.md](experiments.md).
The C enumerator needs only `clang`; the SAT script needs PySAT, which the
research notes install at `/private/tmp/nice-pysat`.
