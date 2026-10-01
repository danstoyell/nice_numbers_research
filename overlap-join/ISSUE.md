**Title:** Proposal: an "overlap join" niceonly search, 10–27× faster than the CubeCL path on an M4 GPU and 3.6–7.6× on CPU (prototype + evidence)

---

> **Disclosure:** this proposal and its code were produced largely by AI agents (Anthropic's Claude), directed by me. Every correctness claim rests on exact checks against this repository's own code at `fe1b0b8`, and every one can be rerun from the linked folder.

Hi! I've been working on the nice-number problem and ended up with a different way to organise the niceonly search inside a field. It keeps the client's soundness guarantee. In head-to-head tests on real production fields it was faster than the client's own code, on CPU and on GPU through your CubeCL backend. I wanted to share it before going further.

**Full write-up, code and data:** https://github.com/danstoyell/nice_numbers_research/tree/main/overlap-join

![How much faster the overlap join is than the client](https://raw.githubusercontent.com/danstoyell/nice_numbers_research/main/overlap-join/evidence/speedup.png)

### The idea

The client certifies top digits with the MSD recursion and bottom digits with the k = 3 stride table, then walks every stride candidate in each surviving range and applies the cross-end AND. The overlap join makes both ends deep enough to overlap.
- It builds a list of t-digit prefixes of n whose certified top digits are distinct, and a list of residues n mod b^k (k = 6) whose low digits are distinct.
- The two lists share t + k − L digits of n. It hash-joins them on those shared digits plus the digit-sum class mod b−1, instead of iterating candidates.
- Each matched pair costs one 64-bit AND of the two certified-digit masks. Survivors go to your `get_is_nice` / `candidate_check`.
- Soundness is the same argument as your filters: a nice n has distinct digits on every subset of positions, so its (prefix, residue) pair is always matched and always passes.

### Results

Client time ÷ join time on the same 1e14 production fields: the mean over 5 fields per base, with the range in brackets.

| Base | CPU, 1 thread | CPU, 10 threads | GPU, Apple M4 (CubeCL/Metal) |
|---:|---:|---:|---:|
| 57 | 7.6× (6.9–8.5) | 7.3× (6.3–8.1) | **27.2×** (25.6–29.6): 420 s → 15.4 s per field |
| 60 | 6.2× (5.0–8.0) | 4.9× (2.8–5.7) | **9.8×** (6.2–13.0): 89 s → 8.9 s |
| 64 | 3.6× (2.1–4.7) | 2.9× (2.2–3.4) | **17.4×** (14.2–21.9): 249 s → 14.0 s |

- **The client side is your own code**, linked from `nice_common` at `fe1b0b8`: `process_range_niceonly` on CPU, and `begin`/`finish_niceonly_cubecl` with fleet defaults on GPU, one whole-field run per field.
- **The join on GPU** is a CubeCL 0.10 implementation following `cubecl_backend.rs` conventions, with your `candidate_check` for the final check.
- **Against your best pinned MSD floor** the GPU ratios are 25.3×, 10.3× and 15.8×. With the join's top certification also on the device they are slightly higher, and it then needs about 0.1 host core.
- **Where the gain comes from** (base 57 on GPU):
  - about 330× fewer full checks;
  - 2.4× fewer O(1) steps;
  - each step is a register-tiled AND (about 4 ps on the M4), where a stride visit (about 0.25 ns) rebuilds the candidate, gathers from the 6.4 MB low-digit table and compacts.

### Checks on fairness and correctness

- **The baseline is your code running normally.** Your device tests pass on this GPU and it finds 69 in base 10.
  - Your `pipeline_throughput_fixed_fields` harness runs within 17–18% of the M4 figures in your doc comments.
  - The direct-MSL build is no faster than WGSL.
  - The headline uses whole-field client runs, because a 10% stratified sample overstated client time by 10–24% (per-piece start-up overhead).
- **Exactness.** GPU survivors = CPU prototype = brute force on 21 windows across bases 20–64, including windows where the MSD filter lets candidates through. GPU = CPU on 120 real production partitions at bases 57, 60 and 64. Base 10 returns 69.
- **A bug the checks caught.** Re-verification found one GPU kernel bug: padding slots against an all-zero top certificate. It was superset-only, so no hit could be lost, and it never triggered at production settings. It was fixed and everything was rerun.
- **Known solutions.** Over the complete intervals of every base where the answer is known (your rules generalised to "each digit exactly K times"), the join recovers every known twice-nice (bases 15–22) and thrice-nice (bases 13–14) solution, and reports nothing at nice bases 25–40.

### Limitations

- **One machine.** Everything ran on one Apple M4 laptop. **Nothing has run on NVIDIA.**
  - The operation counts transfer, but the per-step cost ratio, which carries most of the GPU gain, may well shrink: the 6.4 MB gather fits NVIDIA's larger L2, and CUDA's wide digit scan makes full checks cheaper.
  - The write-up bounds this (roughly 7–20× at base 57 under pessimistic assumptions) and includes an untested CUDA design note for `nice_kernels.cu`.
- **Small bases.** Below about base 35 the current pipeline is as fast or faster; this is for the frontier.
- **Prior art.** The join itself is known: Geißer et al., arXiv:2112.00444, §6. The contribution here is applying it to this search, the GPU kernel, and the measurements against this client.

### What I'm asking

- Is this something you'd want in the client, behind a flag first?
- If so, which shape would you prefer: a sibling of `process_range_niceonly`, a CubeCL kernel alongside the niceonly kernels, or both?
- Would anyone with an NVIDIA card be willing to run the GPU benchmark? `--features cubecl-cuda` should work unchanged, but it is untested.

I'm happy to adapt the code to your conventions and open a PR with the exactness suites and the known-solution testbed as tests. The client has had filter soundness bugs before, and this work caught one of its own the same way, so I'd want those in CI before any default switch.

Thanks for running this project!
