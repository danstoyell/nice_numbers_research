# D5: the overlap join in the public search client — report

## Verdict

- **The join still wins after the client's cross-end filter, so neither D5 stop rule triggers.**
- **Step 3 (model, base 57): the residual gain is well above 2×.**
  - On production work units (fields of 1e14 numbers), the join does 3.1× fewer operations than the CPU client and 4.6–6.3× fewer than the GPU pipeline.
  - Over the whole base-57 interval, which would need a different kind of work unit, it does 17–34× fewer.
- **Step 4 (prototype): the join is correct and faster in practice on CPU.**
  - It matches brute force exactly on 21 cases across bases 20–64.
  - Run side by side with the client's own code on the same production fields, one thread each, it is 7.6× faster at base 57, 6.2× at base 60 and 3.8× at base 64.
  - Memory is about 50 MB per worker.
- **GPU: not measured, because this machine has no GPU.** Section 5 argues it is feasible.
- **What remains:** a GPU prototype, then an issue with the maintainer. Per instructions I opened no issue or PR upstream.
- **Scale of the win:** about 7× at base 57 is worth roughly one base. It improves the odds; it cannot turn the search into a proof. Only a second nice number or a nonexistence proof counts.

## 1. What each client stage certifies, and at what cost (step 1)

I read the client at commit fe1b0b8 (v3.4.5+). The files are [`msd_prefix_filter.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/msd_prefix_filter.rs), [`lsd_filter.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/lsd_filter.rs), [`stride_filter.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/stride_filter.rs), [`residue_filter.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/residue_filter.rs), [`client_process.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/client_process.rs), [`gpu_niceonly.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/gpu_niceonly.rs) and [`client/src/main.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/client/src/main.rs).

Measured rates are for base 57, per n in the candidate interval, from exact sampling with the CPU client's production settings.

| Stage | Output positions certified | Cost |
|---|---|---|
| Digit-sum filter mod b−1 (`residue_filter`) | None. A global constraint: n²+n³ ≡ b(b−1)/2 (mod b−1). Keeps #roots/(b−1) of n (6/56 at base 57) | Zero per candidate: folded into the stride table |
| LSD filter, k = 3 (`lsd_filter`, stride table) | Positions 0–2 of n² and n³: 6 digits, known exactly per residue and checked distinct when the table is built | Zero per candidate. Table: 801,870 residues mod (b−1)·b³ = 10,370,808 (7.7%) |
| Stride filter (CRT walk) | Nothing new: it combines the two filters above | 1 add and an index step per candidate: 5.30e-3 visits per n |
| MSD prefix filter with Hall's condition (`analyze_range`) | For a range: every top position of n² and n³ whose interval of values is narrower than b. Single-value positions are certified exactly; the rest enter a Hall matching check. Mean 16.5 exact top digits and 19.2 constrained positions per stride visit (nice-40: 9.2 and 12.0) | Per range node: four wide endpoint powers, full digit expansion (114 digits at 57), about 19 matching steps. 1.16e-5 analyses per n on CPU; 1.0–2.6e-6 at the GPU range sizes |
| Cross-end residue filter (v3.4.1) | Checks the range's exact top digits (positions ≥ 3) against the residue's 6 low digits | One AND per visit; rejects 88% of visits at 57 (84–87% at GPU range sizes) |
| Full check (seeded with the low digits) | All remaining positions | 6.2e-4 per n; about 4.6 digits extracted before the first repeat (nice-40) |

**How the client compares with the join.**
- The client is an "edge" search whose cross-check is the cross-end AND. Its top side is the MSD leaf, about 10^4 numbers wide, certifying about 16 digits at base 57. Its bottom side is only 3 digits of n, certifying 6 output digits.
- So it visits every stride candidate in a surviving leaf.
- The join makes the bottom side deeper, k = 6–10 digits certifying 12–20 output digits. It reaches those bottom residues by hash lookup on the digits the two sides share, instead of stride iteration.
- Measured per base-57 field, with settings tuned for wall time:
  - the join's top side certifies about 16 digits, the same as the client's leaves;
  - its bottom side certifies 12 digits against the client's 6;
  - the join does 7.2e9 full checks against 1.0e11 (about 14×);
  - it does 4.9e11 O(1) pair checks against 8.3e11 stride visits.

## 2. Testbed comparison (step 2)

**Client side.** `client_count.c` is a C reimplementation of the client's CPU nice-only pipeline with operation counters, generalized to 2- and 3-nice for the testbed.
- It matches the unmodified client library exactly on sample windows at bases 25–64. The comparison counts leaves, numbers in leaves, visits, cross-end rejects, full checks, mean certificate size and hits (`crosscheck.json`, via a Rust harness linked against `nice_common`).
- It ran on the exact testbed: nice bases 25–40, twice-nice 15–22 and thrice-nice 13–14. All known solutions were recovered and re-verified with exact integers:
  - twice-nice 15–22: 1, 1, 1, 4, 4, 5 and 5 solutions (bases 15, 16, 17, 19, 20, 21, 22);
  - thrice-nice: 16/16 at base 13 and 38/38 at base 14;
  - nice bases 25–40: none, as expected.

**Join side.** P1's join (`testbed.json`) did not use the digit-sum filter; the client does. I added it to a copy of the join (`join_ds.c`) by putting the digit-sum class (mod b−1) into the hash key, and reran every P1 configuration. All known solutions were recovered.

**Operations** are counted as follows:
- client: MSD analyses + stride visits + full checks;
- join: top calls + bottom calls + digit-sum lookups + matches + full checks.

| Case | N | Client ops | P1 join ops | Client ÷ P1 join | Join + digit-sum (t,k): ops | Client ÷ join+ds | Full checks, client ÷ join+ds |
|---|---:|---:|---:|---:|---:|---:|---:|
| nice-25 | 6.4e6 | 9.98e5 | 1.21e6 | 0.83× | (3,4): 5.71e5 | 1.75× | 6.6× |
| nice-28 | 3.9e7 | 3.11e6 | 5.58e6 | 0.56× | (5,4): 4.02e6 | 0.77× | 27× |
| nice-29 | 8.3e7 | 3.33e6 | 1.15e7 | 0.29× | (5,4): 4.60e6 | 0.72× | 27× |
| nice-30 | 4.9e8 | 1.58e7 | 5.20e7 | 0.30× | (4,5): 1.14e7 | 1.39× | 22× |
| nice-32 | 2.3e9 | 5.60e7 | 1.89e8 | 0.30× | (5,5): 2.62e7 | 2.14× | 24× |
| nice-33 | 3.3e9 | 2.19e8 | 3.18e8 | 0.69× | (5,5): 7.06e7 | 3.10× | 23× |
| nice-34 | 7.2e9 | 3.35e8 | 6.32e8 | 0.53× | (6,5): 3.18e8 | 1.05× | 115× |
| nice-37 | 2.2e11 | 7.60e9 | 9.13e9 | 0.83× | (6,6): 1.88e9 | 4.05× | 98× |
| nice-38 | 3.2e11 | 5.24e9 | 1.40e10 | 0.38× | (6,6): 1.75e9 | 3.00× | 87× |
| nice-40 | 4.6e12 | 1.08e11 | 1.09e11 | 1.00× | (6,7): 3.67e10 | 2.95× | 311× |
| twice-15 | 6.8e6 | 2.88e6 | 4.65e6 | 0.62× | (4,5): 2.05e6 | 1.41× | 4.6× |
| twice-16 | 2.5e7 | 8.73e6 | 1.37e7 | 0.64× | (6,5): 9.85e6 | 0.89× | 12× |
| twice-17 | 6.0e7 | 2.73e7 | 3.63e7 | 0.75× | (6,5): 2.70e7 | 1.01× | 11× |
| twice-19 | 1.5e9 | 9.12e8 | 8.24e8 | 1.11× | (6,6): 4.15e8 | 2.20× | 9.7× |
| twice-20 | 1.6e10 | 2.09e9 | 6.59e9 | 0.32× | (6,7): 1.48e9 | 1.41× | 20× |
| twice-21 | 6.7e10 | 2.27e10 | 2.19e10 | 1.04× | (8,7): 1.97e10 | 1.15× | 63× |
| twice-22 | 1.7e11 | 3.78e10 | 5.71e10 | 0.66× | (8,7): 3.45e10 | 1.10× | 61× |
| thrice-13 | 1.2e8 | 3.37e7 | 1.45e8 | 0.23× | (7,6): 4.64e7 | 0.73× | 6.5× |
| thrice-14 | 2.1e9 | 5.17e8 | 2.50e9 | 0.21× | (8,7): 6.95e8 | 0.74× | 12× |

**What the testbed shows.**
- Against P1's join as it was run, the client is already equal or better: 0.2–1.1×. P1's 2.7–7× gains were over an idealized edge search, not over this client.
- With the digit-sum filter in both, the join does 0.7–4× fewer operations. The gain grows with the base: about 3–4× at nice bases 37–40, and about 1× for thrice-nice.
- On full checks the join wins everywhere, by 5–311×.

## 3. Model at bases 57–64 and the step-3 decision

**Client.** Exact operation rates come from sampling the reimplemented pipeline on stratified random chunks of each base's interval (`client_sample.json`).
- Configurations:
  - CPU: 1e9 chunks, which is what 1e14 fields give, with the minimum MSD range size of 8,000;
  - GPU: 1e6 chunks with minimum MSD range sizes of 62,500, 250,000 and 500,000.
- Validation: on bases 34, 38 and 40 the sampled estimates are within 0.2–1.5% of the exact full-interval runs.

**Join.** The cost formula counts calls as the testbed does, for a region of S consecutive n (`model_gain.py`).
- Its list-pass and match rates were measured by Monte Carlo with the exact certification rules: 3e7 random n per base (`join_mc.c`, `join_mc.json`).
- Validation: the rates reproduce the measured join+digit-sum totals within 0–2% at nice bases 34, 38 and 40. The uniform-digit analytic rates are within 0.85–1.34×.

**Two settings for the join:**
- **S = N (whole interval).** This is P1's setting and needs work units other than contiguous ranges.
- **S = 1e14.** The client's contiguous-field interface at base 57; the field size comes from the public API. Both lists are rebuilt per field.

| b | Client CPU ops | Client GPU ops (62.5k / 250k / 500k) | Join, whole interval (t,k): ops | Gain CPU / GPU | Join per 1e14 field (t,k): ops | Gain CPU / GPU |
|---:|---:|---|---|---|---|---|
| 57 | 10^17.54 | 10^17.71 / 17.80 / 17.85 | (10,9) 10^16.31 | 16.9 / 24.7–34.1 | (10,6) 10^17.05 | 3.1 / 4.6–6.3 |
| 58 | 10^17.56 | 10^17.74 / 17.82 / 17.88 | (10,9) 10^16.38 | 15.0 / 22.7–31.3 | (10,6) 10^17.12 | 2.7 / 4.2–5.7 |
| 60 | 10^18.36 | 10^18.52 / 18.64 / 18.66 | (9,10) 10^17.23 | 13.4 / 19.7–27.1 | (10,6) 10^18.07 | 2.0 / 2.9–3.9 |
| 62 | 10^19.01 | 10^19.20 / 19.28 / 19.33 | (11,10) 10^17.79 | 16.5 / 25.9–34.8 | (11,5) 10^18.73 | 1.9 / 3.0–4.0 |
| 64 | 10^20.12 | 10^20.31 / 20.40 / 20.46 | (11,10) 10^18.74 | 23.9 / 37.0–52.6 | (12,5) 10^19.68 | 2.7 / 4.2–6.0 |

**Larger work units help.** At base 57 the per-field gain against the CPU client grows with the field size S:
- S = 1e15: 3.6×;
- S = 1e16: 5.1×;
- S = 1e18: 9.0× (`gain_vs_region.json`).

**Decision per the stop rule** ("stop if under about 2× at base 57 in the model"): **do not stop.** The gain at 57 is 3.1× in the least favourable setting (CPU client, 1e14 fields), 4.6–6.3× against the GPU pipeline, and 17–34× over the whole interval.

## 4. Prototype, CPU (step 4)

**Design.** `join-proto/` is written in Rust and linked against the unmodified `nice_common`. It takes a range of n and returns nice numbers, using the client's own `get_is_nice` for full checks.
- **Top list:** t-digit prefixes of n that meet the range. Certification uses 256-bit endpoint powers, positions at or above k, and intervals clipped to the range. It is built once per field to depth t−p, then extended per partition.
- **Bottom list:** residues mod b^k, built depth-first from the low digit and partitioned by p of the shared digits. Only the key values present among that partition's tops are generated.
- **Join:** a hash join on the remaining shared digits plus the digit-sum class, with one 64-bit AND per match.

**Correctness.** 21 exactness cases, bases 20–64, several (t,k,p), windows aligned and unaligned. Six of the windows are ones where the client's MSD filter lets candidates through (`verify_proto.json`).
- Survivor sets and match counts equal a brute-force per-n evaluation of the same certificate, in all 21 cases and all three builds.
- Base 10 returns 69.
- The soundness argument is P1's: a nice n has distinct digits in every subset of positions, so its pair is always matched and always passes.

**Timing.** Client and join were run side by side on the same production 1e14 fields, one thread each, interleaved in three rounds (join, client, join, client …) so machine load hit both alike (`bench_pair.py`).
- Client time comes from the client's own `process_range_niceonly` (stride k = 3, minimum range size 8,000) on 120 random 1e9 chunks of each field.
- Join time comes from 36 random partitions per field plus the per-field top layer.
- The join uses 64-bit division by precomputed reciprocal (Möller and Granlund) and settings tuned for wall time; `tune_proto.jsonl` has the sweep.

| b | (t,k,p) | Fields | Join s per field | Client s per field | Client ÷ join, time (range) | Client ÷ join, ops (range) |
|---:|---|---:|---:|---:|---|---|
| 57 | (9,6,2) | 5 | 1,951 | 14,914 | 7.6× (6.9–8.5) | 1.9× (1.6–2.3) |
| 60 | (9,6,2) | 5 | 831 | 5,142 | 6.2× (5.0–8.0) | 1.5× (1.3–1.8) |
| 64 | (10,6,2) | 5 | 1,531 | 5,792 | 3.8× (2.1–4.7) | 1.6× (1.4–1.8) |

- **Rebuilt with the client's release profile** (lto = true, codegen-units = 1) on 2–3 fields per base, the ratios are unchanged: 6.9–7.0×, 5.2–5.9× and 3.2–4.5× (`bench_pair_lto.jsonl`).
- **Empty fields:** about half the sampled fields are rejected entirely by both methods, in under 1 s each.

**Why the time gain exceeds the operation gain.**
- The join removes the client's expensive operations: about 14× fewer full checks, each tens of ns with 256-bit arithmetic, and no MSD analyses at about µs each.
- What it adds is cheap: matches at about 4 ns each, including the full checks.

**Settings chosen for fewest operations lose in wall time.** With settings like (10,6,2), and before the division speedup, the join was only 0.7–4.1× faster in wall time (`bench_proto.jsonl`), even though it did 2.8–3.3× fewer operations at base 57.
- At those settings, top-prefix certification is about 215–660 ns per call and dominates.
- One fewer top digit cuts top calls 36–57×. Matches only double.

**Per-field cost at base 57, (9,6,2), one core:**
- top prefixes: 2.4e8 calls, about 52 s;
- bottom lists: 1.5e10 calls, about 320 s;
- matches plus full checks: 4.9e11 matches and 7.2e9 full checks, about 2,000 s.

**Memory.** Per partition, about 2.9e6 bottom entries × 16 B ≈ 46 MB, plus about 3e4 tops and a 3,192-bucket offset table. That is about 50 MB per worker thread; no fleet limit is at risk.

**Stop rule** ("stop if memory or GPU constraints make the join slower in practice"): **not triggered on CPU.** GPU is untested; see section 5.

## 5. GPU feasibility (argued, not measured: no GPU on this machine)

The fleet mostly runs the GPU pipeline. There the CPU runs the MSD recursion, and the device walks stride candidates, applies the cross-end AND, compacts survivors and full-checks them ([CHANGELOG v3.4.1](https://github.com/wasabipesto/nice/blob/fe1b0b8/CHANGELOG.md); `common/src/cuda/nice_kernels.cu`).

**Work per 1e14 field at base 57, client at range size 250,000 against join (9,6,2):**

| Where | Client | Join |
|---|---|---|
| Device, O(1) steps | 9.25e11 stride visits | 4.9e11 AND tests (1.9× fewer) |
| Device, full checks | 1.37e11 | 7.2e9 (19× fewer) |
| Host | ≈1.3e8 MSD analyses at ≈µs each, a few hundred core-s (the changelog's figures imply about 320 core-s per 1e14 at this range size) | ≈370 core-s measured (tops 52 s, bottoms 320 s) |

**The CPU side stays in balance.**
- The join's host work is about the same size as the client's MSD work.
- The bottom lists can also move to the device: each level expands entries by b children and filters them, the same expand-filter-compact pattern the client's kernels already use.

**The device work fits GPUs well.**
- Each partition splits into 3,192 buckets (57 key values × 56 digit-sum classes).
- Each bucket holds about 900 bottom entries and is probed by the tops sharing its key.
- So the work is a set of dense tiles: tops × entries, one AND each, with the bucket loaded once into shared memory. That is a regular, coalesced workload.
- Survivors are 1.5% of AND tests and would go to the client's existing compacted full-check kernel.
- Memory per partition is about 50 MB, so dozens of partitions can be in flight.

**Risks.**
- It needs a new descriptor format: partitions, not (offset, length, mask) ranges.
- Top-prefix certification needs 256-bit arithmetic; it is only 2.4e8 calls per field and can stay on the CPU.
- The bottom lists are a fixed cost per field, about 15% of the join's CPU time at 1e14. Fields smaller than about 1e14 would erode the gain, and larger fields help (section 3).

**Expected device-side gain:** between 1.9×, the O(1) steps, and about 10–19×, if full checks dominate the device time as the changelog's compaction note suggests. Until a GPU prototype measures it, this is an argument, not a result.

## 6. Decision and next steps

- **Step 3: continue.** The residual gain at base 57 is 3.1–6.3× per 1e14 field in the model, well above 2×.
- **Step 4: do not stop.** The join is correct on all tests, 3.8–7.6× faster in wall time than the client's own CPU path on production fields at bases 57–64, and small in memory.
- **Next:**
  1. A GPU prototype of the matching stage (bucket tiles, one AND each, then compaction), with the bottom lists on host first.
  2. Then step 5: an issue to the maintainer with the soundness argument, the 21 exactness cases, the testbed table and these timings.
  - Per instructions, nothing was opened or pushed upstream.
- **Impact:**
  - About 7× at base 57 is worth roughly one base: the cost per expected solution rises about 3× per base at bases 57–60.
  - At the fleet's current rate, finishing bases 57–60 would drop from about a century to roughly 15 years, if the device gain matches the CPU gain.
  - It improves the odds only, about 0.1–0.3% for a second nice number this decade. It does not change the nonexistence picture.

## 7. Caveats

- **Shared machine.** Load average was 7–18 on 10 cores. Pairing and interleaving control for it; separate runs differed by up to 1.7×.
- **Sampling error.** Per-field estimates come from 120 of 1e5 client chunks and 36 of 3,249 (57, 60) or 4,096 (64) join partitions, about ±10–20% per field. Across fields the ratios are consistent: 6.9–8.5× at base 57.
- **Parallelism.** Both were timed on one thread. The client parallelizes over chunks; the join parallelizes trivially over partitions.
- **Metric.** Unit operation counts understate the join's wall-time gain, because the operations it removes are the expensive ones. They overstate its gain at settings chosen for fewest operations, where top certification dominates. Both are reported.
- **Generalization.** The 2- and 3-nice testbed runs use my generalization of the client's rules to multiplicity K. The client itself is nice-only.
- **Model scope.** The bases 57–64 model uses exact client sampling and join rates measured by Monte Carlo. The join's per-field model is validated only through the prototype's measured counts, which agree with it.

## 8. Files

All of these are in `attack/d5-client-join/`:
- **Notes:** `STATE.txt` (working notes).
- **Client counting and cross-check:** `client_count.c` (u128 and 256-bit builds), `crosscheck/` and `crosscheck.py` → `crosscheck.json`.
- **Testbed runs:** `run_client_testbed.py` → `client_testbed.json`; `join_ds.c` with `run_join_testbed.py` → `join_ds_testbed.json`; `summarize.py` → `summary_table.md` and `comparison.json`.
- **Bases 57–64 model:** `sample_client.py` → `client_sample.json`; `join_mc.c` with `run_join_mc.py` → `join_mc.json`; `model_gain.py` → `model_gain.json`; `gain_vs_region.json`; `validate_models.py` → `validation.json`.
- **Prototype:** `join-proto/` (Rust); `verify_proto.py` → `verify_proto.json`; `tune_proto.py` → `tune_proto.jsonl`; `bench_proto.py` → `bench_proto.jsonl`; `bench_pair.py` → `bench_pair.jsonl` and `bench_pair_lto.jsonl`.
- **Client clone:** `nice-client/` (commit fe1b0b8).
- **Toolchain:** Rust is in `/private/tmp/nice-rust`.

## Sources

- Public client wasabipesto/nice, commit fe1b0b8: https://github.com/wasabipesto/nice. Source files as linked in section 1, plus `common/src/cuda/nice_kernels.cu` and the [CHANGELOG](https://github.com/wasabipesto/nice/blob/fe1b0b8/CHANGELOG.md): v3.4.0 (Hall / interval digit domains, stride k 2 → 3), v3.4.1 (cross-end residue filter), v3.3.0 and v3.2.15 (soundness fixes).
- Production field sizes, from the public data API, queried 2026-09-27: https://data.nicenumbers.net/fields?base_id=eq.57 (1e14 at base 57; 1e9 at base 40).
- Overlap join, testbed and cost model: `attack/p1-algorithm/REPORT.md`, `overlap.c`, `testbed.json`, `cost_model.py`.
- Candidate intervals and filtered counts: `scripts/verify.py`, `critique/scripts/reachability.py`. The 2- and 3-nice solution lists are in `critique/results/{twice,thrice}-nice.json`.
- N. Möller and T. Granlund, "Improved division by invariant integers", IEEE Transactions on Computers 60(2), 2011, 165–175. https://doi.org/10.1109/TC.2010.143
