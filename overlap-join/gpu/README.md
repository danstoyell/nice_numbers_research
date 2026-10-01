# Overlap join on the GPU (CubeCL 0.10, Apple M4 / Metal)

The device stage of the overlap join, written in CubeCL 0.10 to match the public client's [`cubecl_backend.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/cubecl_backend.rs). The crate depends on the client's `nice_common` at git rev **fe1b0b8**, unmodified. `STATE.txt` is the full working log and `CUDA_NOTE.txt` the CUDA design note. The parent [README](../README.md) gives the idea and the CPU evidence.

## Verdict

- **The join's whole device stage runs in CubeCL 0.10 on an Apple M4 GPU, and it is exact.**
  - The stages are: bottom lists, bucketing, the one-AND join, survivor compaction, a new middle-digit prefilter, and the client's own full check. Top certification can optionally run on the device too.
  - Suites (§3):
    - 21 verify cases: GPU survivor sets equal both the CPU prototype and brute force.
    - 120 real production partitions across all 15 benchmark fields at bases 57, 60 and 64: exact.
    - Base 10 finds 69, and every hit is checked with exact integers.
  - All of this holds on the final build, with tops certified on the host and with tops on the device. The 21 cases were rerun on the build pinned to the git rev: 21/21.
- **One bug was found by the final re-verification, fixed, and re-verified.**
  - The first rerun of the 21 cases failed two base-20 cases (3,696 survivors against 1,666), caused by empty entry slots passing against zero-mask tops.
  - The bug was superset-only: it could add survivors, never lose a nice number. It cannot occur at production settings, and the production partitions were exact before the fix.
  - **The preliminary benchmark (`results/bench_prelim.jsonl`) used that buggy binary. All final numbers below come from the fixed build** (sha256 2a8adc4f…).
- **Speed on the same M4 GPU, per 1e14 production field.** This is the headline comparison, with no sampling on either side:
  - Client: one whole-field run per field, through its own CubeCL niceonly pipeline with fleet defaults.
  - Join: whole fields, mean of 3 interleaved rounds.

| Base | Client (s/field) | Join, host tops (s) | Join, device tops (s) | Client ÷ join, host tops: mean (range, sd) | Client ÷ join, device tops |
|---:|---:|---:|---:|---|---|
| 57 | 420 | 15.4 | 13.7 | **27.2×** (25.6–29.6, sd 1.9) | **30.5×** (29.1–32.7) |
| 60 | 89 | 8.9 | 8.1 | **9.8×** (6.2–13.0, sd 2.4) | **10.9×** (5.8–15.1) |
| 64 | 249 | 14.0 | 13.5 | **17.4×** (14.2–21.9, sd 3.2) | **18.0×** (14.9–22.6) |

- **Against the client at its best pinned floor** (better than the fleet default on this GPU, §2) the ratios are 25.3×, 10.3× and 15.8× with host tops, and 28.4×, 11.4× and 16.3× with device tops.
- **The client is not handicapped on Metal beyond the following** (§2):
  - its own parity tests pass here;
  - the maintainer's own M4 throughput harness gives numbers within 17–18% of the maintainer's recorded M4 figures;
  - the direct-MSL build is no faster than WGSL;
  - the only real handicap found is the controller's floor clamp, which costs it 0–17% and is accounted for in the second set of ratios.
- **Where the gain comes from** (§5, base 57): the join does 2.4× fewer O(1) tests and 330× fewer full checks. Each of its tests is about 55–68× cheaper on the GPU: 4 ps for a register-tiled AND against 0.25 ns for the client's gather-reconstruct-compact stride visit. On 10 CPU cores the same pair is only 7.3× apart. The GPU magnifies the algorithmic gain because the join's work is a dense tile and the client's is a gather.
- **Host cores** (§4.4):
  - With host tops, the join needs about 3–7 host-thread-seconds per device-second, which nearly saturates this 10-core (4 P + 6 E) laptop at bases 57 and 60.
  - With device tops it needs 0.04–0.16 cores and is as fast or faster end to end. That is the variant to use on bigger GPUs.
- **NVIDIA:** untested; nothing here ran on NVIDIA. The operation counts and exactness transfer; the per-operation costs may not. A bounded estimate is in §6, and a CUDA mapping is in `CUDA_NOTE.txt` (§6.2).

## 1. What was built

### 1.1 Layout and conventions (mergeable shape)

`overlap_join_gpu` is a Cargo crate.
- It depends on `nice_common` (git rev fe1b0b8, feature `cubecl`) and pins `cubecl = "=0.10.0"` as the client does.
- Its features `cubecl-cuda` and `cubecl-metal` forward to the client's features of the same name.

The kernels follow the conventions of `cubecl_backend.rs`:
- u32 buffers, with u64 values packed as lo/hi word pairs;
- every division is by a `#[comptime]` constant, with one JIT specialization per base and (t,k,p);
- 256-thread cubes;
- cube-scoped compaction with `plane_exclusive_sum` and `sync_cube`, as the client does on wgpu, which has no plane barrier;
- the split16 or wide digit scan chosen per runtime, mirroring the client's `wide_chunk_for`;
- the client's per-dispatch `flush` (watchdog safety) and `launch_fence` backpressure.

The pieces:
- **Full check:** the client's own `candidate_check`, copied verbatim into `src/client_check.rs` under the client's MIT licence. It is private in nice_common; the only diff is `pub`. A merge would delete the copy.
- **CPU reference:** `src/proto.rs`, a verbatim copy of the CPU prototype (`../cpu/src/lib.rs`) with accessor blocks appended at the end.
- **Kernels:** `src/join_kernels.rs`. **Host side:** `src/join_gpu.rs`. **CLI:** `src/main.rs`. About 4,800 lines in total.

### 1.2 Pipeline per 1e14 field

**Field setup (host, about 20 ms):**
- The top layer at depth t−p: 75k prefixes at base 57.
- The *bpre* list: residues mod b^f0 whose 2·f0 low output digits are distinct, sorted by digit-sum class mod b−1 (134k entries at base 57). It is uploaded once.

**Then all b^p partition values** (3,249 at base 57), 4 partitions per batch:

| Stage | Kernel(s) | Work |
|---|---|---|
| 0. Tops | Host threads (default), or `top_kernel` + `top_scan_kernel` + `top_fill_kernel` with `JOIN_DEVTOPS=1` | Certify each top P = P0·b^p + v, exactly as the CPU prototype's `cert`: endpoint powers, output digits at positions ≥ k that are constant on the block, all distinct. Group each top into the buckets (key digit, class) it probes, one per digit-sum root. The device version does 96-bit endpoint powers in u32 limbs, scans both endpoints' digits in lockstep from the low end with split16 division, and takes ndig from a power table. |
| 1. Bottoms (on device from the start) | `bucket_kernel` | One cube per (class, slot). Extend each bpre entry by v's digits with exact digit-array arithmetic mod b^k in u32. Then step the two key-position output digits through all b key values (+2d0, +3d0² mod b), adding the entry index to the (slot, key, class) list wherever they are new and distinct. |
| 2. Join | `join_kernel_v3` | One cube per non-empty bucket. The bucket's tops (mask, r0 bounds, id) go to threadgroup memory. Each thread holds 4 entries in registers. For every 32 tops, a branch-free AND builds a pass bitmask; only set bits are walked (range test, then staging in shared memory, then flush to the global survivor list with one atomic per flush). |
| 3. Prefilter (new) | `mid_kernel` | Digits 0..k+1 of n² and n³ from n's low k+2 digits, which must be distinct. The top certificate seeds the test when every certified position is proved ≥ k+2. Survivors are compacted. It keeps about 6% at bases 57–64. |
| 4. Full check | `check_kernel` | Rebuild n = P·b^f0 + r0, then the client's `candidate_check`. |

**Soundness of the prefilter.** Each tested digit is a real digit of n² or n³ at a distinct position: both powers have at least k+2 digits throughout the field, and seed digits sit at positions ≥ k+2. So a repeat proves n is not nice. The join itself is sound by the argument in the parent README.

**Development path** (each step re-verified; device seconds per base-57 field):
- v1, tile scan: about 36 s.
- v2, 4 entries per thread: about 31 s.
- v3, bucket lists and the 32-top bitmask: about 18 s.
- v3 plus the prefilter: about 11–12 s.

v1 and v2 remain selectable with `JOIN_KERNEL=1|2`.

**Device memory:** about 0.45–0.5 GB in total:
- survivor list: 256 MiB;
- prefilter list: 64 MiB;
- bucket lists for 4 slots: 116–176 MB.

Every list overflow is checked and fails loudly.

## 2. Baseline: the client's CubeCL niceonly path on this GPU, and scrutiny

**It runs on Metal.**
- `CubeclContext::new_default()` gives "Apple M4 (Metal, wgpu<wgsl>)". The client's `--gpu-backend auto` order for niceonly is cuda → cubecl → vulkan ([client/src/main.rs](https://github.com/wasabipesto/nice/blob/fe1b0b8/client/src/main.rs)), so on a Mac the fleet runs exactly this path.
- Base 10 returns 69.
- The client's own ignored device tests pass on this GPU: `cubecl_niceonly_finds_69_in_base_10`, `cubecl_matches_cpu_niceonly` and `cubecl_cross_filter_survivors_match_the_host_mirror`.

**Configuration: fleet defaults, nothing overridden** ([gpu_niceonly.rs](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/gpu_niceonly.rs)):
- floor steered by the `FloorController`, seed 250k, clamped to [62,500, 500,000];
- 2 fields in flight and 16 batches in flight;
- cross-end filter with cube-scoped compaction (plane-scoped compaction is off on Metal by the maintainer's choice);
- split16 digit scan (the client notes that the wide scan is 4.6× slower on an M4).

It is driven through `begin_niceonly_cubecl` / `finish_niceonly_cubecl`, the same calls the binary makes; only network and claim handling are absent.

**Scrutiny:**

1. **Maintainer's harness.** `pipeline_throughput_fixed_fields`: base 54, 10 × 1e13 fields from the Anvil region (`results/client_m54_harness.txt`).

   | MSD floor | This machine (n/s) | Maintainer's recorded M4 figure (n/s) |
   |---|---:|---:|
   | steered | 6.54e11 | — |
   | pinned 62.5k | 6.53e11 | 7.9e11 at 60k |
   | pinned 250k | 5.15e11 | 6.3e11 at 250k |

   So the client runs **17–18% slower here** than the maintainer's M4 figures, which come from the doc comments in `gpu_niceonly.rs`. Possible causes are a different M4 configuration or this laptop being in use (load average about 3). The join was measured on the same machine in the same interleaved sessions, so the ratio should be unaffected to first order. If the slowdown is specific to the client's memory-bound workload, the ratios could be overstated by up to about 1.2×.
2. **Metal compiler.** The client's experimental `cubecl-metal` feature emits MSL directly instead of going through naga's WGSL.
   - Client at base 57, 2 runs each: 420 and 426 s (MSL) against 416 and 418 s (WGSL).
   - Join: 11.8 s against 11.6 s.
   - Both builds are exact (base 10 → 69, and a production partition matches).
   - **No compiler handicap.**
3. **MSD floor.** At bases 57–64 the steered floor sits at the clamp minimum of 62,500, because the device is the bottleneck. A pinned-floor sweep (`scripts/client_decomp.py`, `results/client_decomp.jsonl`) on one field per base:

   | Base | Pinned floors (s) | Steered (s) | Best |
   |---:|---|---:|---|
   | 57 | 15,625: 356; 31,250: 374; 62,500: 409; 125k: 480; 250k: 538; 500k: 625 | 412 | 15,625 |
   | 60 | 15,625: 206; 31,250: 128; 62,500: 142 | 144 | 31,250 |
   | 64 | 15,625: 316; 62,500: 378 | 380 | 15,625 |

   - In the final interleaved benchmark, the client pinned at those floors is 7% faster at 57 (428 against 460 s, stratified), no faster at 60 (116 against 111), and 9% faster at 64 (268 against 296).
   - The clamp is a deliberate design choice made on base-54 data, but on this M4 it costs the client up to 17% at 57–64.
   - **All headline ratios are therefore also given against the best pinned floor.**
4. **Same coverage, equivalent work.**
   - Both sides cover [S, S+1e14) completely. The client receives it as one field. The join runs all b^p partitions, with tops clipped to the field and per-top r0 bounds.
   - Both are complete exact searches: the client's by construction, the join's by its soundness argument plus the exactness tests in §3. The join's full checks are the client's `candidate_check`.
   - Its per-field survivor counts match the CPU prototype's estimates (8.21e9 against 8.22e9 on 79228699893042801193).
   - Both report 0 hits on every field.
5. **Sampling, and a bias that sampling hid.** The benchmark first estimated the client from 10% stratified samples (100 pieces of 1e11). Against whole-field runs on all 15 fields, that estimate is **biased high by +10% at 57 (−1 to +22%), +24% at 60 (+20 to +28%) and +20% at 64 (+11 to +26%)**. The cause is per-piece pipeline start and drain overhead. **So the headline uses whole-field client runs**, which is what a fleet client actually processes.
   - The preliminary ratios (31.6×, 12.8×, 20.8×) used these biased estimates and the buggy binary; they are superseded.
   - Sampled ratios from the final benchmark are still in `results/report_tables.txt` for reference: 29.9×, 12.1×, 20.7×.

## 3. Correctness (final build; nothing hidden)

| Suite | Tops | Result |
|---|---|---|
| `scripts/verify_gpu.py` → `results/verify_gpu.json` | host | **21/21 PASS.** Bases 10–64, several (t,k,p), aligned and unaligned windows, six where the client's MSD filter lets candidates through. Per case: GPU survivor set = CPU prototype set = brute force; GPU match count = CPU count; prefilter output = an exact u128 host mirror; every n rebuilt on the device = the expected set; hits equal. **Base 10 → [69].** |
| same, git-pinned build → `results/verify_gpu_gitbuild.json` | host | **21/21 PASS**, rerun 2026-09-30 on this folder's `Cargo.toml` (nice_common from GitHub at fe1b0b8). |
| same with `JOIN_DEVTOPS=1` → `results/verify_gpu_devtops.json` | device | **21/21 PASS**, brute force on all 21. Device-certified tops equal the host's top for top: P, mask, r0 bounds and seed flag. |
| `scripts/verify_parts.py` → `results/verify_parts.jsonl` | host | 15 production fields (the benchmark fields), 8 random partitions each: **120 partitions, all exact.** 1.531e8 survivors, 1.136e10 matches, 9.66e6 prefilter survivors. |
| same with `JOIN_DEVTOPS=1` → `results/verify_parts_devtops.jsonl` | device | Same 120 partitions, **all exact**; 2,276,198 device tops equal the host's. |
| Hits | — | Every hit is checked three ways: by `get_is_nice`, by an independent u128 digit-vector test in Rust, and with Python big integers. Benchmark runs also assert the exact check. The only hit anywhere is 69 (base 10). |

**The bug the rerun caught** (fixed in the final build):
- **Symptom:** base 20, (t,k,p) = (2,3,1) gave 3,696 and 3,542 GPU survivors against 1,666 and 1,512 on the CPU.
- **Cause:** `join_kernel_v2/v3` padded empty register slots with an all-ones mask. A top whose certificate is zero, which happens only when t is tiny, let them pass.
- **Fix:** an explicit per-slot validity mask in v3, and an out-of-range r0 sentinel in v2.
- **Scope:** superset-only, so no nice number could be lost. Production tops always carry a nonzero certificate, which is why all production partitions were exact before the fix.
- **Status:** all suites above were rerun on the fixed build.

## 4. Benchmark on the M4 GPU (final build)

### 4.1 Method

- **Fields:** 15 real production fields (5 each at 57, 60, 64) from the public API, bounds [S, S+1e14).
- **Join settings:** the CPU wall-time settings: (t,k,p) = (9,6,2) at 57 and 60, (10,6,2) at 64.
- **Interleaving:** `scripts/bench_final.py` → `results/bench_final.jsonl`, 180 records, 0 errors. Three rounds; in each, every field runs join, join with device tops, client, and client at its pinned floor back to back, with the order rotated by round and field.
- **Join measurements:**
  - *host tops:* whole field, 9 host threads plus the dispatcher, wall time including tops;
  - *device tops:* whole field, the host only launches;
  - *device-only:* all tops are precomputed on 512 random partitions and the device phase is timed alone. The same run with `JOIN_MID=0` gives the original design without the prefilter.
- **Client headline:** one whole-field run per field (`scripts/client_fullfield.py` → `results/client_fullfield.jsonl`).
- **Noise:**
  - join per-field round-to-round standard error: 2.6–4.7%;
  - client stratified standard error across rounds: 3.5–3.8%;
  - repeated client measurements on the same field differ by about 3% (base 57, field 79228699893042801193: whole field 446.6 s, stratified 444 ± 21 s).
  - So a single per-field ratio carries about ±5%. The spread across fields (sd 1.9–3.2×) is real variation between fields.
- **No sampling on either side** for the headline numbers.

### 4.2 Per field (seconds per 1e14 field)

| b | Field start | Client, whole field | Join, host tops (±se, 3 rounds) | Join, device tops | Join, device only | Client ÷ join | Client ÷ join, device tops |
|---:|---|---:|---:|---:|---:|---:|---:|
| 57 | 43926999893042801193 | 358.6 | 13.9 ± 0.6 | 12.1 ± 0.4 | 11.7 | 25.8× | 29.7× |
| 57 | 64061199893042801193 | 509.3 | 17.2 ± 0.6 | 15.6 ± 0.8 | 13.5 | 29.6× | 32.7× |
| 57 | 65042299893042801193 | 367.0 | 14.3 ± 0.3 | 12.6 ± 0.2 | 11.5 | 25.6× | 29.1× |
| 57 | 70427299893042801193 | 419.8 | 16.1 ± 0.6 | 13.8 ± 0.2 | 12.1 | 26.1× | 30.5× |
| 57 | 79228699893042801193 | 446.6 | 15.4 ± 0.9 | 14.6 ± 0.7 | 13.0 | 29.0× | 30.6× |
| 60 | 1244055012114824200908 | 96.9 | 9.6 ± 0.4 | 8.9 ± 0.3 | 8.0 | 10.0× | 10.9× |
| 60 | 1801504012114824200908 | 131.1 | 10.1 ± 0.2 | 8.7 ± 0.2 | 8.2 | 13.0× | 15.1× |
| 60 | 1901287712114824200908 | 98.0 | 9.3 ± 1.2 | 7.7 ± 0.2 | 8.1 | 10.5× | 12.8× |
| 60 | 793163612114824200908 | 43.0 | 6.9 ± 0.2 | 7.4 ± 0.3 | 7.8 | 6.2× | 5.8× |
| 60 | 860689812114824200908 | 77.9 | 8.4 ± 0.1 | 8.0 ± 0.2 | 8.1 | 9.3× | 9.7× |
| 64 | 39399613562957161709568 | 251.1 | 14.3 ± 0.3 | 13.5 ± 0.3 | 13.1 | 17.6× | 18.6× |
| 64 | 41242006262957161709568 | 370.5 | 16.9 ± 0.4 | 16.4 ± 0.5 | 15.2 | 21.9× | 22.6× |
| 64 | 57785162662957161709568 | 167.5 | 11.5 ± 0.3 | 11.2 ± 0.4 | 11.2 | 14.6× | 14.9× |
| 64 | 65552385962957161709568 | 164.9 | 11.6 ± 0.3 | 11.1 ± 0.3 | 11.6 | 14.2× | 14.9× |
| 64 | 68936001062957161709568 | 288.7 | 15.6 ± 0.4 | 15.4 ± 0.5 | 14.1 | 18.5× | 18.7× |

### 4.3 Per base (means over 5 fields; ratio = mean of per-field ratios, with range)

| b | Client, whole field | Join, host tops | Join, device tops | Join device only / without prefilter | Ratio, host tops | Ratio, device tops | Ratio vs client at best pinned floor (host / device tops) |
|---:|---:|---:|---:|---:|---|---|---|
| 57 | 420 | 15.4 | 13.7 | 12.4 / 19.6 | 27.2× (25.6–29.6) | 30.5× (29.1–32.7) | 25.3× / 28.4× |
| 60 | 89 | 8.9 | 8.1 | 8.1 / 9.5 | 9.8× (6.2–13.0) | 10.9× (5.8–15.1) | 10.3× / 11.4× |
| 64 | 249 | 14.0 | 13.5 | 13.1 / 17.6 | 17.4× (14.2–21.9) | 18.0× (14.9–22.6) | 15.8× / 16.3× |

- **Why base 60 is lowest.** The client's MSD filter is strongest there: 3.4e11 stride visits per field against 1.16e12 at base 57. The join, meanwhile, pays a fixed cost per field: about 2–3 s of bottoms over 3,600 partitions, plus top certification. That fixed cost dominates its 8 s.
- **Without the prefilter** (the join exactly as in the CPU prototype), device-only time against the whole-field client gives about 21× at 57, 9.4× at 60 and 14× at 64.

### 4.4 Host cores needed to keep the GPU fed

**Join with host tops:**
- Host-thread time per field for top certification is 74, 57 and 42 thread-s at 57, 60 and 64. Process CPU during the pipelined run is 96, 64 and 53 CPU-s.
- Against 12.4, 8.1 and 13.1 s of device time, that is **about 6, 7 and 3 host threads busy per device**. Counted as process CPU, it is 7.8, 8.0 and 4.1 cores.
- On this laptop (10 cores = 4 P + 6 E) that is near saturation: whole-field wall exceeds device-only time by 24% at 57, 10% at 60 and 7% at 64.

**Join with device tops:**
- 0.6–1.3 CPU-s per field, i.e. **0.04–0.16 cores**.
- Device time rises because certification moves onto the device, but the end-to-end wall is lower at 57 (13.7 against 15.4 s) and about equal at 60 and 64.
- This is the right default for GPU hosts.

**Client:**
- Fleet default: 594, 423 and 279 CPU-s per whole field, i.e. 1.4, 4.9 and 1.2 cores. It is device-bound.
- At the best pinned floor: 2,430, 1,022 and 1,033 CPU-s per field, i.e. 5.7, 8.8 and 3.9 cores.

### 4.5 CPU-only context (same fields, this machine, 10 threads)

`scripts/cpu_context.py` → `results/cpu_context.jsonl` measures:
- the client's `process_range_niceonly` (stride k=3, MSD floor 8,000) on 200 random 1e9 chunks;
- the CPU prototype join on 40 random partitions, one per thread.

The 1-thread pair is `../evidence/cpu_bench_pair.jsonl` on the same fields.

| b | Client, 1 thread | Join, 1 thread | Client, 10 threads | Join, 10 threads | CPU ratio, 10 threads | GPU ÷ 10-thread CPU: client | GPU ÷ 10-thread CPU: join |
|---:|---:|---:|---:|---:|---|---:|---:|
| 57 | 14,914 | 1,951 | 1,729 | 236 | 7.3× (6.3–8.1) | 4.1× | 15.3× |
| 60 | 5,142 | 831 | 598 | 123 | 4.9× (2.8–5.7) | 6.7× | 14.1× |
| 64 | 5,792 | 1,531 | 742 | 257 | 2.9× (2.2–3.4) | 3.0× | 18.2× |

The client's GPU path is only 3–7× faster than its own 10-core CPU path on this machine; the join's is 14–18× faster.

## 5. Where the gain comes from (base 57, field 79228699893042801193)

**Client device cost.**
- Counts per field come from a validated counting reimplementation of the client (`client_count256`, 20,000 sampled 1e6 chunks per floor).
- Device time across six pinned floors fits a·(stride visits) + c·(full checks) to within 4%, with **a = 0.251 ns per visit and c = 0.728 ns per full check.**
- At the fleet floor: 1.16e12 visits cost about 293 s and 1.70e11 full checks about 124 s, a model of 416 s against 409 s measured.
- At 60 and 64 the two counts are collinear across floors; only the all-in cost is stable, at 0.41 and 0.34 ns per visit.

**Join device cost** (`scripts/stage_probe.py`, final binary, two repeats, `results/stage_probe_final.txt` plus earlier runs):

| Work | Count per field | Device cost each | Seconds per field |
|---|---:|---:|---:|
| Bottoms (extension + bucketing) | 3,249 partitions × 134k | — | 2.1–3.3 |
| AND tests | 4.89e11 | 3.7–4.5 ps | 1.8–2.2 |
| Survivor walk + staging | 8.21e9 | 0.32–0.37 ns | 2.6–3.3 |
| Middle-digit prefilter | 8.21e9 | 0.40–0.41 ns | 3.3–3.4 |
| Full checks (client's `candidate_check`) | 5.2e8 | about 1.1–2.2 ns | 0.6–1.2 |
| **Total** | | | **11.0–12.4** |

**The three factors:**
1. **Fewer operations.**
   - O(1) tests: 1.16e12 visits against 4.89e11 ANDs, 2.4× fewer.
   - Full checks: 1.70e11 against 8.21e9 survivors before the prefilter (21×), and against 5.2e8 after it (**330×**).
   - The cause is the deeper bottom side: 12 certified low output digits, 16 with the prefilter, against the client's 6.
2. **Cheaper operations: about 55–68× per O(1) test.**
   - *Client visit:*
     - rebuilds each candidate (u32 division by a constant, a residue gather, and u64 add and compare, which Apple GPUs emulate);
     - does a random 8-byte gather of the low-digit mask from a 6.4 MB table (801,870 residues);
     - runs cube-scoped compaction, with a plane scan and two barriers per 256 candidates.
   - *Join AND:* four entry masks sit in registers, the top's mask is a broadcast read from threadgroup memory, and 32 tops go through each branch-free step. There is no per-test memory traffic, no reconstruction and no barrier.
3. **Net.** The GPU magnifies the CPU ratio (7.3× on 10 cores) to 27×: the join's tile gains about 15× from CPU to GPU, the client's walk about 4×. The prefilter contributes a factor of 1.6 at 57 (12.4 against 19.6 s device), 1.2 at 60 and 1.3 at 64.

## 6. What transfers to NVIDIA, and what doesn't

Nothing here ran on NVIDIA. Everything CUDA-specific is **untested**.

**Transfers:**
- **Operation counts:** ANDs, survivors, prefilter survivors, full checks and top calls. They are properties of the algorithm and the field.
- **Exactness evidence:** the same CubeCL source compiles for every runtime.
- **Structure:** dense tiles against a gather-and-compact walk.

**May not transfer:**
- **The client's per-visit cost.** It is a random gather from a 6.4 MB table plus u64 arithmetic.
  - NVIDIA L2 caches are 40 MB on the A100 ([NVIDIA A100 whitepaper](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf)) and 72 MB on the RTX 4090 ([Chips and Cheese](https://chipsandcheese.com/p/microbenchmarking-nvidias-rtx-4090)), so the gather is likely relatively cheaper there.
  - **The 55–68× per-test cost ratio, which carries most of the GPU gain, is the number most likely to shrink on NVIDIA.**
- **Full-check cost.** On CUDA the wide digit scan applies: 5 digits per chunk at base 57 against 2 in split16, with nvcc strength-reducing the division. That makes full checks relatively cheaper, which helps the client (330× more full checks) more than the join.
  - Bound: at base 57, full checks are about 30% of the client's M4 device time.
  - If full checks were free and visits and ANDs scaled alike, the ratio would fall from about 27× to about 20×.
  - If the client's visit also became, say, 3× cheaper relative to an AND, roughly 7–10× would remain. That is an illustration, not a measurement.
- **The floor clamp** may not handicap the client on NVIDIA: the maintainer measured optima at 100k–500k on many-core NVIDIA hosts.
- **Host balance.** The maintainer's base-54 figures put a 9070 XT at about 10× this M4. A device that fast would need about 60 host cores for host-side tops. **On big GPUs the device-tops path is required.** Its device cost, about 1.5 s per field on the M4, then matters.

### 6.1 Route (a), no new code

Build with `--features cubecl-cuda` and construct the client with `CubeclContext::new_cuda(i)`, as the client does. `JoinDevice<R: Runtime>` is runtime-generic, and the wide scan is picked automatically. This should compile unchanged; it is untested.

### 6.2 Route (b), the CUDA design note (untested; full text in `CUDA_NOTE.txt`)

Hand-written CUDA kernels in [`nice_kernels.cu`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/cuda/nice_kernels.cu), driven like [`client_process_cuda.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/client_process_cuda.rs) through NVRTC with per-base `-D` defines.

**New defines:** JOIN, F0, PP, K, K2, KEY_LEVEL, NB, EPT, S2, S3 and PRE_MOD = b^K2 (≤ 2^48).

**Kernels:**
- **`join_top_kernel`:** the existing `mul_limbs`, plus a lockstep two-endpoint variant of `scan_digits` (= `cert_power`), with b^i in `__constant__` memory.
- **Scan and fill:** `cub::BlockScan`.
- **`join_bucket_kernel`:** as `bucket_kernel`.
- **`join_match_kernel`:** the AND tile with EPT registers per thread and a 32-top bitmask walked with `__ffs`. Survivors feed the existing COMPACT machinery (`__ballot_sync`/`__popc` per-warp queue), drained through `prefilter_low_digits()` with PRE_DIGITS = K2, seeded with the top certificate, and then through `check_is_nice()`. This fuses stages 2–4 with no global survivor list; wgpu needs that list only because WGSL has no plane barrier.

**Host:**
- a `JoinSink` beside `CudaNiceonlySink` on the same stream, with the same before/after event pair per batch, so device-busy time is measured (wgpu cannot do this);
- a partition-value work list replaces the MSD workers and the `FloorController`;
- bpre is cached per (base, f0), like `NiceonlyPlan`'s residue table.

**Descriptor change:** the work unit becomes (field, partition value) instead of (offset, len, mask) ranges.

**First things to measure:**
- the full-check to AND cost ratio (about 300× on the M4);
- the client visit to join AND cost ratio (about 55–68× on the M4).

## 7. Caveats

- **One machine.** Apple M4, 10-core GPU, 10 CPU cores (4 P + 6 E), 16 GB unified memory. It is a laptop in use, on AC power; load average was about 3 before runs and up to about 9 during them. Interleaving controls for drift.
- **The client runs about 17–18% slower here than the maintainer's recorded M4 figures** (§2.1). The cause is unknown; the effect on the ratio is at most about 1.2× if it is client-specific.
- **No device timestamps.** "Device only" is the wall time of a device phase with all host work precomputed. CubeCL on wgpu/Metal exposes no per-dispatch timestamps, and the client reports `device_busy_secs: None` there too.
- **Join settings are not GPU-tuned.** (t,k,p) are the CPU wall-time settings, the batch is 4 partitions, and 4 entries are held per thread. The bottoms and fixed costs at base 60 suggest larger t or p could help.
- **Device-kernel scope.** At most one key digit (o−p ≤ 1), base ≤ 64, b^f0 < 2^32, and n < 2^96 for device tops. All production settings meet these, and every limit is checked.
- **A wgpu quirk.** `client.flush()` blocks while launch fences are polled; this showed up as host "dispatch" time. Device throughput is unaffected; this was checked by disabling fences.
- **10-thread CPU context is sampled.** 200 chunks for the client and 40 partitions for the join, so expect about ±10%.

## 8. How to build and run

```sh
cd overlap-join/gpu && cargo build --release        # add --features cubecl-metal (MSL) or cubecl-cuda (untested)
B=target/release/overlap_join_gpu
$B verify 10 47 100 2 1 0                           # base 10 -> 69, GPU = CPU = brute force
JOIN_GPU=$B python3 scripts/verify_gpu.py           # 21 cases;  JOIN_DEVTOPS=1 VERIFY_OUT=verify_gpu_devtops.json for device tops
JOIN_GPU=$B python3 scripts/verify_parts.py         # 120 production partitions (VERIFY_OUT=..., JOIN_DEVTOPS=1 likewise)
$B field-full 57 79228699893042801193 79228799893042801193 9 6 2 9 4    # one whole field, 9 host threads, 4 partitions/batch
JOIN_DEVTOPS=1 $B field-full 57 79228699893042801193 79228799893042801193 9 6 2 9 4
$B client-range 57 79228699893042801193 79228799893042801193          # the client's own CubeCL pipeline, one whole field
python3 scripts/bench_final.py; python3 scripts/client_fullfield.py; python3 scripts/report_tables.py
```

Some scripts default to the binary paths used during development; set `JOIN_GPU` (and the other path variables named at the top of each script) to your build.

**Environment knobs:**
- `JOIN_DEVTOPS=1`: device tops.
- `JOIN_MID=0..`: prefilter depth (default 2).
- `JOIN_EPT`: entries per thread (default 4).
- `JOIN_KERNEL=1|2|3`: kernel generation.
- `JOIN_PROFILE=1`: synced per-stage timing.
- `JOIN_STAGES` / `JOIN_EXP`: benchmark-only stage cut-offs.
- The client's own knobs work unchanged: `NICE_GPU_MSD_FLOOR`, `NICE_CUBECL_WIDE`, and so on.

## 9. Files

**Source** (`src/`):
- `join_kernels.rs`: all device kernels.
- `join_gpu.rs`: host side, batching and pipelines.
- `main.rs`: CLI modes `verify`, `verify-parts`, `field`, `field-full`, `client-range`, `client-strat`, `client-sample`, `cpu-client` and `cpu-join`.
- `client_check.rs`: verbatim copy of the client's `candidate_check` (MIT, © wasabipesto).
- `proto.rs`: verbatim copy of the CPU prototype plus accessors.

**Scripts:** `verify_gpu.py`, `verify_parts.py`, `bench_final.py`, `client_fullfield.py`, `client_decomp.py`, `cpu_context.py`, `stage_probe.py`, `report_tables.py` and `summarize_bench.py`. `bench_gpu.py` is the preliminary benchmark.

**Results:**

| Area | Files |
|---|---|
| Verification | `verify_gpu.json`, `verify_gpu_gitbuild.json`, `verify_gpu_devtops.json`, `verify_parts.jsonl`, `verify_parts_devtops.jsonl` |
| Final benchmark | `bench_final.jsonl` |
| Client whole fields | `client_fullfield.jsonl` (15 whole-field client runs) |
| Floor sweep and op counts | `client_decomp.jsonl` |
| Maintainer harness | `client_m54_harness.txt` |
| CPU context | `cpu_context.jsonl` |
| Stage probe | `stage_probe_final.txt` |
| Tables | `report_tables.txt` and `report_tables.json` |
| Superseded runs | `bench_prelim.jsonl` (preliminary, **buggy binary**); `prev_build/` (verification runs from before the fix) |

**Other:** `CUDA_NOTE.txt` (CUDA design note), `STATE.txt` (working log), `logs/`.

## Sources

- **wasabipesto/nice at fe1b0b8** ([repository](https://github.com/wasabipesto/nice), MIT licence):
  - [`common/src/cubecl_backend.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/cubecl_backend.rs): `candidate_check`, `niceonly_kernel`, `wide_chunk_for` with its M4 note, the plane-compaction defaults, and the device tests used here.
  - [`common/src/gpu_niceonly.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/gpu_niceonly.rs): `FloorController`, `MSD_FLOOR_MIN` = 62,500 and `MSD_FLOOR_MAX`, the M4 throughput figures quoted in its docs, and `pipeline_throughput_fixed_fields`.
  - [`client/src/main.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/client/src/main.rs): backend order.
  - [`common/src/cuda/nice_kernels.cu`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/cuda/nice_kernels.cu) and [`common/src/client_process_cuda.rs`](https://github.com/wasabipesto/nice/blob/fe1b0b8/common/src/client_process_cuda.rs).
  - [`CHANGELOG.md`](https://github.com/wasabipesto/nice/blob/fe1b0b8/CHANGELOG.md).
- CubeCL 0.10.0 ([tracel-ai/cubecl](https://github.com/tracel-ai/cubecl)): the wgpu stream flush and submission regulator behaviour, read in `cubecl-wgpu-0.10.0/src/compute/stream.rs`.
- NVIDIA L2 cache sizes: A100 40 MB ([NVIDIA A100 Tensor Core GPU Architecture whitepaper](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf)); RTX 4090 72 MB ([Chips and Cheese, "Microbenchmarking Nvidia's RTX 4090"](https://chipsandcheese.com/p/microbenchmarking-nvidias-rtx-4090)).
