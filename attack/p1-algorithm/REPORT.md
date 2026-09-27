# Path 1 (algorithm): certifying middle digits for many candidates at once

## Verdict

**The 40% edge limit is not a real limit, but the hypothesis still fails: nothing reaches 90%, and base ~120 stays out of reach.**

- **What works.** An *overlap join* beats the edge rate, and the gain grows with the base. It uses a list of top prefixes and a list of bottom residues that share some digits of n, matched on those shared digits.
  - On the testbed it finds every known solution: 16/16 thrice-nice in base 13, 38/38 in base 14, and all 24 twice-nice numbers through base 22. It also finds none in nice bases 24–40, as expected.
  - It does 9–534× fewer full checks than the best edge enumerator, and 1.2–7× fewer total operations.
- **Why it can't reach 90%.** It is capped at 80% of output digits. The middle third of n³ (positions L to 2L−1, where L is the number of digits of n) needs more than L input digits from either end. So neither leading-digit (real) nor trailing-digit (b-adic) certification can reach any of it.
  - Even at that cap, with free lists and ideal joins, the cost is about e^{0.52b}, roughly 10^{24–25} checks per solution at bases 118–120.
  - At realistic list sizes the model gives 10^{41.0} per solution at base 118 (10^{39.2} with colour coding, which is modelled but not implemented), against 10^{43.3} for edges.
  - At the frontier (bases 57–64) the gain is 3–25×, worth about 1–3 bases. That is an incremental speedup, which doesn't count.
- **Kill criterion.** It is formally not met, because a mechanism does beat the edge rate. But the target (about 90% certified, making base ~120 feasible) is not reachable by this mechanism or any other tried here. The difficulty now sits in n³'s middle fifth, which holds 52% of the difficulty exponent at the cap. Nothing examined here touches it.

## 1. The mechanism: an overlap join

- **Top list T.** All prefixes P of t digits of n. On the prefix interval, the top ~t−1 digits of both n² and n³ are fixed; keep P if those digits are compatible (each value used at most K times).
- **Bottom list B.** All residues R = n mod b^k. These fix the bottom k digits of n² and n³; keep R if compatible.
- **The step edges don't take.** Edge search uses t + k ≤ L, so each input digit serves one side only. That is where 2L of 5L output digits, or 40%, comes from.
  - Taking t + k = L + o (o > 0) makes the lists share o digits of n.
  - A hash join on those o digits builds each n exactly once, from its unique pair (P, R).
  - Each shared input digit then certifies four output digits instead of two. The certified total is 2(t−1) + 2k, up to about 4L (80%).
  - The top list's certification is capped at position k, so no output position is counted by both lists.
- **Soundness and completeness.** A k-nice n uses no value more than K times in any subset of its output positions. So P ∈ T, R ∈ B, the pair shares its key, and the O(1) cross-check of certified counts passes. Hence every solution is found.
- **Cost.** |T| + |B| + matches, where matches (pairs with equal keys) ≈ N·P_T·P_B.
  - P_T and P_B are the probabilities that the top and bottom certified digits are each internally compatible. N is the interval size.
  - Pairs that pass the cross-check are "survivors" (≈ N·P_joint) and get the full check.
  - The measured counts match this model to within a factor of 0.6–1.7 on every testbed base.

## 2. Why 80% is a hard ceiling for any certificate built from the two ends

- Digit p of n³ can be read from the bottom only with n mod b^{p+1}, which is p+1 digits of n.
- From the top it needs n to relative precision b^{p−3L}, which is 3L−p leading digits of n.
- For L ≤ p < 2L, both exceed L, so n must be known completely.
- A prefix interval, a residue class, or any join of the two therefore certifies none of those L digits.
- The same argument shows all of n² is reachable (from one side or the other), so only n³'s middle third is out of reach.
- With M ≈ b/5 digits uncertified, the cost per solution is at least b^M/M! ≈ e^{0.522b}.
- Exponents, as the natural log of cost per solution per unit of base:

| Method | Exponent (limit) | Fitted slope, bases 300–400 |
|---|---:|---:|
| Edges | 0.906 | 0.90 |
| Overlap join, within-list compatibility only | 0.813 | 0.83 |
| Overlap join with colour coding (model only) | approaches 0.52 very slowly | 0.75 |
| Ceiling | 0.522 | 0.52 |

## 3. Testbed

- Every hit was re-verified with exact Python integers, independently of the C code, and compared against the complete lists in `critique/results/*-nice.json`.
- **Metrics:**
  - *Full checks* are candidates n whose n² and n³ are actually expanded.
  - *Total operations* is the sum of top-prefix steps, bottom-residue steps, trie visits or matches, and full checks.
  - Wall time is not the metric. Other agents pushed the load average to 20–30 on 10 cores, which distorted timings.
  - Where both methods ran with full checks at low load, the join was faster in wall time:

| Case | Edge | Join |
|---|---:|---:|
| thrice-13 | 4.7 s | 2.2 s |
| thrice-14 | 66.8 s | 18.1 s |
| twice-19 | 21.5 s | 8.4 s |

- Edge splits are the model-optimal t + k = L, walked with joint pruning. The edge "leaves" are exact counts; for the largest bases they were counted without being fully checked.

| Case | N | Solutions found / known | Edge (t,k): full checks | Join (t,k,o) | Matches (O(1) each) | Join full checks | Full-check ratio | Total-ops ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nice-25 | 6.4e6 | 0/0 | (2,3): 1.44e6 | (4,4,3) | 7.7e5 | 5.6e4 | 26× | 3.3× |
| nice-30 | 4.9e8 | 0/0 | (3,3): 7.00e7 | (4,5,3) | 4.2e7 | 2.7e6 | 26× | 3.7× |
| nice-34 | 7.2e9 | 0/0 | (4,3): 6.49e8 | (5,6,4) | 2.8e8 | 4.6e6 | 140× | 2.7× |
| nice-37 | 2.2e11 | 0/0 | (4,4): 1.53e10 | (6,6,4) | 8.2e9 | 1.2e8 | 125× | 4.7× |
| nice-40 | 4.6e12 | 0/0 | (4,4): 2.79e11 | (6,7,5) | 8.3e10 | 5.2e8 | 534× | 7.0× |
| twice-15 | 6.8e6 | 1/1 | (3,3): 3.94e6 | (5,5,4) | 3.2e6 | 4.2e5 | 9× | 2.0× |
| twice-19 | 1.5e9 | 4/4 | (4,4): 7.14e8 | (6,6,4) | 7.0e8 | 8.1e7 | 9× | 2.1× |
| twice-20 | 1.6e10 | 4/4 | (4,4): 6.94e9 | (6,7,5) | 5.4e9 | 3.6e8 | 20× | 2.5× |
| twice-21 | 6.7e10 | 5/5 | (5,4): 2.49e10 | (8,7,6) | 1.8e10 | 4.2e8 | 59× | 2.7× |
| twice-22 | 1.7e11 | 5/5 | (5,4): 6.39e10 | (8,7,6) | 4.8e10 | 1.1e9 | 57× | 2.6× |
| thrice-13 | 1.2e8 | 16/16 | (4,4): 8.38e7 | (7,7,6) | 7.4e7 | 7.0e6 | 12× | 1.3× |
| thrice-14 | 2.1e9 | 38/38 | (5,4): 1.36e9 | (7,8,6) | 1.2e9 | 1.3e8 | 11× | 1.2× |

- **Gain against base.** For nice numbers, total operations improve from about 3× at bases 25–34 to 4.6× at 37–38 and 7.0× at 40. For twice-nice they go from 2.0× to 2.7×.
- **Thrice-nice is the weak case.** Thrice-nice stays flat at about 1.2×, because a limit of 3 per value barely constrains the digits at b ≤ 14.
- **Remaining bottleneck.** The O(1) matches, not the full checks, now dominate the cost. The join only screens each list internally; distinctness *across* the two lists is checked after matching.
- **Base 14 target.** Thrice-14 fully examines 1.3e8 candidates, against 2.1e9 in the interval (16× fewer). It still performs 1.2e9 O(1) matches.

## 4. Extrapolation

This is the validated model for nice numbers, in the same conditional random-digit model as `critique/scripts/reachability.py`. Values are log10 of checks per expected solution; the certified digit counts for the overlap columns are in `cost_model.txt`.

| b | Edge | Overlap join | + colour coding | 80% ceiling |
|---:|---:|---:|---:|---:|
| 57 | 19.7 | 19.2 | 18.5 | 10.0 |
| 60 | 21.1 | 20.4 | 19.9 | 12.2 |
| 64 | 22.5 | 21.7 | 21.1 | 12.6 |
| 100 | 36.5 | 34.7 | 33.2 | 21.0 |
| 118 | 43.3 | 41.0 | 39.2 | 23.9 |
| 120 | 44.3 | 41.9 | 40.1 | 25.4 |

- **Why finite bases fall short of the ceiling:**
  - Lists cost about N·b^{−(L−t)}·P, and they must stay no larger than the match count. That forces L − t ≥ log_b(1/P_B), which is 2–7 digits at bases 60–120.
  - At the optimum, each key has about one entry per side. So cross-list distinctness can only enter through colour coding: random value partitions, with an overhead of about ((b−g)/(b−s))^g per trial. Here g is the number of certified digits on one side and s is the size of the random value set.

## 5. Other mechanisms tried

| Mechanism | Result |
|---|---|
| Lattice windows (Coppersmith-style progressions and boxes) | Certifying w middle digits needs a box of about b^w points, so w ≤ f free input digits: a rate of 1 per digit. Combined with edges this gives 2(L−f) + f < 2L. It loses to edges, and after an overlap join no free digits remain. |
| Additive split n = A·b^{2m} + B·b^m + C | For fixed C, the windows [2m,3m) of n² and n³ are u(A) + v(B) mod b^m. That turns out to be the bottom edge extended into A, and exploiting it with a trie on A's low digits is exactly the overlap join. |
| Meet-in-the-middle with n = H·b^j + L | The cross terms 2HL, 3H²L and 3HL² give no equality key. Confirmed dead. |
| Dynamic programming over carries with multiset fingerprints | The middle coefficients of the digit convolution involve all input digits, so there is no bounded state. The p2 line lemma (digit i is affine in the new digit) is the bottom-edge extension and doesn't reach n³'s middle third. |
| Representation techniques (Howgrave-Graham–Joux, Becker–Coron–Joux) | For fixed (t,k), each n has exactly one pair (P,R). There is no additive slack for multiple representations to exploit. |
| Relations with base b±1 | Only the digit-sum congruence mod b−1 survives, which is already known. |
| Colour-coded disjointness join | Model only, not implemented. It adds 0.5–2 orders of magnitude at bases 57–120 and cannot pass the 80% ceiling. For K ≥ 2, guessing how each value's multiplicity splits between the lists makes the overhead worse. |

## 6. Caveats

- Wall-clock ratios are unreliable because of load from other agents; operation counts are the headline metric.
- The C code uses 128-bit arithmetic, which limits nice-number tests to b ≤ 40.
- Colour coding and all figures for bases above 40 come from the model. The model agrees with the testbed to within a factor of 0.6–1.7.
- The 80% ceiling argument covers certificates built from prefix intervals and residue classes, and joins of them. It is not a lower bound for all possible algorithms.

## 7. Files

All in `attack/p1-algorithm/`:
- `overlap.c`: exact enumerator with two modes. `edge` is the edge baseline (bottom list × top trie, joint pruning). `join` is the overlap hash join, partitioned by p shared digits, with work counters.
- `run_testbed.py`: picks configurations with the model, runs the enumerator on 2 threads, re-verifies every hit exactly, and asserts the result equals the known lists. Output goes to `testbed.json`, with logs in `twice2122.log`.
- `summarize.py`: prints the table in section 3.
- `knice_model.py`: list-size model for the k-nice testbed.
- `cost_model.py`: nice-number model for edge, overlap, colour coding and the ceiling. Output is in `cost_model.txt` and `cost_model.json`.

Reproduce with:
- `clang -O3 -o overlap overlap.c -lpthread`
- `python3 run_testbed.py {nice|twice|thrice} LO HI [n_configs]`
- `python3 cost_model.py`

## Sources

- Public search client (leading-digit, trailing-digit, stride and cross-end filters): https://github.com/wasabipesto/nice
- Critique and cost conventions: `critique/research-directions.md`, `critique/scripts/reachability.py`.
- N. Howgrave-Graham and A. Joux, "New generic algorithms for hard knapsacks", EUROCRYPT 2010.
- A. Becker, J.-S. Coron and A. Joux, "Improved generic algorithms for hard knapsacks", EUROCRYPT 2011.
- N. Alon, R. Yuster and U. Zwick, "Color-coding", J. ACM 42 (1995): https://doi.org/10.1145/210332.210337
- D. Coppersmith, "Small solutions to polynomial equations, and low exponent RSA vulnerabilities", J. Cryptology 10 (1997).
