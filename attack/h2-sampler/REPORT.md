# H2: does progressive conditioning reach the rare event without collapsing?

2026-09-28. Hypothesis H2 of [NEXT_HYPOTHESES.md](../NEXT_HYPOTHESES.md): a
population sampler that keeps roots passing a moderately hard test, refreshes
them with reversible digit proposals, and then tightens the test retains
diversity as middle-digit constraints are added, and its cost per verified
witness grows more slowly than the best enumerator's on the analogue testbed.

## Verdict: killed

A subset-simulation sampler (sequential Monte Carlo with Metropolis
rejuvenation under a hard threshold) was calibrated and run against a
uniform-sampling control with the **same score function and the same
evaluation budget** on five unplanted cases: thrice-nice bases 10, 13 and 14
and twice-nice bases 15 and 17 (10, 16, 38, 1 and 1 witnesses).

- **It does not beat uniform sampling, and it gets worse as the base grows.**
  Measured as distinct witnesses per run at equal budget, the best sampler
  variant reaches 0.76–0.84 of the uniform expectation at the two smallest
  cases and at most 0.45 at thrice-13; at thrice-14 (2×10⁹ roots) the six
  variants found 3 witnesses in 30 runs where uniform sampling found 7 in
  5 runs. The one apparent win, 4 witnesses in 5 runs on twice-17 against 2.0
  expected for uniform (the control itself scored 1), is Poisson noise on a
  single-witness case and is not repeated by any other variant there. The
  control matches its analytic expectation in every case.
- **Diversity collapses exactly as the hypothesis feared.** At the last level
  reached, the surviving seeds descend from 27–250 of the 2,000 level-0
  ancestors; acceptance of proposals is 0.3–3.5%; and not a single one of the
  nearly ten thousand episodes reached the final threshold (all excess digits
  removed) by conditioning: every witness found came from a chain stumbling on
  it, i.e. from luck of the same kind uniform sampling has.
- **Top-digit-only proposals, which preserve the bottom output digits, are the
  worst variant** (0 witnesses at thrice-13 with thinning 20 and at thrice-14
  in every run). Preserving edge digits does not help because the score is
  dominated by the digits every proposal re-randomizes.
- **Why.** Changing digit i of n adds 2nδ·b^i to n² and 3n²δ·b^i to n³, so
  every output digit above position i changes pseudo-randomly; even the top
  digit of n re-randomizes about 40% of the output digits. The score
  landscape is a golf course with the b-adic locality that edge methods
  already exploit and nothing else. A hard-threshold chain therefore moves at
  the rate at which fresh random strings pass the threshold, which is what
  uniform sampling pays anyway, plus the cost of the rejected proposals.

The hypothesis's stop rule ("stop if the population becomes copies of a few
ancestors, proposals almost never move, or the apparent gain disappears after
charging for rejuvenation") is met on all three counts.

## 1. Method

`smc.c` implements, for base b and multiplicity K on the exact interval:

- **Score.** φ(n) = Σ_a max(0, count_a(n² ∥ n³) − K); φ = 0 iff n is K-nice.
- **Levels.** A population of P = 2,000 roots starts uniform. Each level sets
  the threshold τ to the 20% quantile of φ, keeps the seeds with φ ≤ τ, and
  regenerates 2,000 members by running a Metropolis chain from each seed with
  the hard indicator φ ≤ τ (a rejected proposal repeats the state), keeping
  every `thin`-th state (thin = 5 or 20). An episode ends when τ = 0 or when
  τ has not decreased for 40 levels; a fresh population then starts a new
  episode, until the evaluation budget is spent.
- **Proposals.** Mode 0 changes one digit of n at a uniformly random position;
  mode 1 changes one of the top two digits only; mode 2 mixes both. A
  proposal outside the interval is rejected.
- **Control.** Mode 9 draws uniform roots with the same budget and the same
  φ.
- **Bookkeeping.** Every root that ever scores 0 is recorded and re-verified;
  each level records the threshold, the number of seeds, the number of
  distinct level-0 ancestors among the seeds, and the acceptance rate.

Budgets per run: 2×10⁶ (thrice-10), 2×10⁷ (twice-15), 3×10⁷ (thrice-13,
twice-17), 6×10⁷ (thrice-14) evaluations; 5 runs per configuration; 3 modes ×
2 thinnings + control per case. The whole campaign is about 4×10⁹ score
evaluations, 20 minutes on one core.

An earlier version stopped a run at the first stall instead of restarting
(`results/smc_stallstop.jsonl`); it spent only 5–25% of its budget and found
correspondingly fewer witnesses. The restart version is the fair comparison.

Reproduce:

```sh
clang -O3 -march=native -o smc smc.c
./campaign.sh            # writes results/smc.jsonl
python3 summarize.py     # the table below
```

## 2. Results

Distinct witnesses per run at equal budget. "Expected for uniform" is
H·(1 − (1 − 1/N)^B) for H witnesses among N roots and budget B; the control
row checks it.

<!-- TABLES -->
| Case | Roots N | Witnesses H | Method | thin | Runs | Budget per run | Distinct witnesses per run, observed | Expected for uniform | Observed / expected | Runs with a witness | Episodes per run | Episodes reaching φ = 0 | Final-level seeds' distinct ancestors (of 2000) | Final acceptance |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| thrice10 | 535,841 | 10 | uniform random (control) | — | 5 | 2e+06 | 9.80 | 9.76 | 1.00 | 5/5 | — | — | — | — |
| thrice10 | 535,841 | 10 | SMC, any digit | 5 | 5 | 2e+06 | 7.40 | 9.76 | 0.76 | 5/5 | 6 | 0/29 | 172 | 0.0286 |
| thrice10 | 535,841 | 10 | SMC, any digit | 20 | 5 | 2e+06 | 6.60 | 9.76 | 0.68 | 5/5 | 2 | 0/10 | 242 | 0.0346 |
| thrice10 | 535,841 | 10 | SMC, top two digits | 5 | 5 | 2e+06 | 1.20 | 9.76 | 0.12 | 4/5 | 7 | 0/35 | 82 | 0.0157 |
| thrice10 | 535,841 | 10 | SMC, top two digits | 20 | 5 | 2e+06 | 1.60 | 9.76 | 0.16 | 5/5 | 2 | 0/10 | 79 | 0.0093 |
| thrice10 | 535,841 | 10 | SMC, mixed | 5 | 5 | 2e+06 | 6.40 | 9.76 | 0.66 | 5/5 | 6 | 0/30 | 154 | 0.0281 |
| thrice10 | 535,841 | 10 | SMC, mixed | 20 | 5 | 2e+06 | 5.80 | 9.76 | 0.59 | 5/5 | 2 | 0/10 | 247 | 0.0319 |
| twice15 | 6,771,952 | 1 | uniform random (control) | — | 5 | 2e+07 | 1.00 | 0.95 | 1.06 | 5/5 | — | — | — | — |
| twice15 | 6,771,952 | 1 | SMC, any digit | 5 | 5 | 2e+07 | 0.20 | 0.95 | 0.21 | 1/5 | 51 | 0/254 | 155 | 0.0183 |
| twice15 | 6,771,952 | 1 | SMC, any digit | 20 | 5 | 2e+07 | 0.60 | 0.95 | 0.63 | 3/5 | 13 | 0/65 | 214 | 0.0204 |
| twice15 | 6,771,952 | 1 | SMC, top two digits | 5 | 5 | 2e+07 | 0.40 | 0.95 | 0.42 | 2/5 | 59 | 0/295 | 103 | 0.0164 |
| twice15 | 6,771,952 | 1 | SMC, top two digits | 20 | 5 | 2e+07 | 0.40 | 0.95 | 0.42 | 2/5 | 15 | 0/75 | 162 | 0.0183 |
| twice15 | 6,771,952 | 1 | SMC, mixed | 5 | 5 | 2e+07 | 0.80 | 0.95 | 0.84 | 4/5 | 55 | 0/275 | 131 | 0.0173 |
| twice15 | 6,771,952 | 1 | SMC, mixed | 20 | 5 | 2e+07 | 0.60 | 0.95 | 0.63 | 3/5 | 14 | 0/70 | 212 | 0.0192 |
| twice17 | 60,063,526 | 1 | uniform random (control) | — | 5 | 3e+07 | 0.20 | 0.39 | 0.51 | 1/5 | — | — | — | — |
| twice17 | 60,063,526 | 1 | SMC, any digit | 5 | 5 | 3e+07 | 0.80 | 0.39 | 2.03 | 4/5 | 79 | 0/396 | 102 | 0.0112 |
| twice17 | 60,063,526 | 1 | SMC, any digit | 20 | 5 | 3e+07 | 0.60 | 0.39 | 1.53 | 3/5 | 19 | 0/97 | 198 | 0.0173 |
| twice17 | 60,063,526 | 1 | SMC, top two digits | 5 | 5 | 3e+07 | 0.00 | 0.39 | 0.00 | 0/5 | 145 | 0/725 | 54 | 0.0060 |
| twice17 | 60,063,526 | 1 | SMC, top two digits | 20 | 5 | 3e+07 | 0.00 | 0.39 | 0.00 | 0/5 | 37 | 0/183 | 95 | 0.0123 |
| twice17 | 60,063,526 | 1 | SMC, mixed | 5 | 5 | 3e+07 | 0.00 | 0.39 | 0.00 | 0/5 | 102 | 0/511 | 102 | 0.0141 |
| twice17 | 60,063,526 | 1 | SMC, mixed | 20 | 5 | 3e+07 | 0.60 | 0.39 | 1.53 | 3/5 | 25 | 0/123 | 129 | 0.0079 |
| thrice13 | 120,679,425 | 16 | uniform random (control) | — | 5 | 3e+07 | 4.20 | 3.52 | 1.19 | 5/5 | — | — | — | — |
| thrice13 | 120,679,425 | 16 | SMC, any digit | 5 | 5 | 3e+07 | 1.60 | 3.52 | 0.45 | 5/5 | 81 | 0/407 | 95 | 0.0112 |
| thrice13 | 120,679,425 | 16 | SMC, any digit | 20 | 5 | 3e+07 | 1.00 | 3.52 | 0.28 | 3/5 | 21 | 0/104 | 163 | 0.0133 |
| thrice13 | 120,679,425 | 16 | SMC, top two digits | 5 | 5 | 3e+07 | 0.40 | 3.52 | 0.11 | 2/5 | 177 | 0/883 | 51 | 0.0073 |
| thrice13 | 120,679,425 | 16 | SMC, top two digits | 20 | 5 | 3e+07 | 0.00 | 3.52 | 0.00 | 0/5 | 45 | 0/226 | 48 | 0.0059 |
| thrice13 | 120,679,425 | 16 | SMC, mixed | 5 | 5 | 3e+07 | 1.00 | 3.52 | 0.28 | 3/5 | 110 | 0/548 | 99 | 0.0111 |
| thrice13 | 120,679,425 | 16 | SMC, mixed | 20 | 5 | 3e+07 | 1.60 | 3.52 | 0.45 | 4/5 | 28 | 0/140 | 170 | 0.0107 |
| thrice14 | 2,081,072,521 | 38 | uniform random (control) | — | 5 | 6e+07 | 1.40 | 1.08 | 1.30 | 4/5 | — | — | — | — |
| thrice14 | 2,081,072,521 | 38 | SMC, any digit | 5 | 5 | 6e+07 | 0.20 | 1.08 | 0.19 | 1/5 | 155 | 0/775 | 80 | 0.0075 |
| thrice14 | 2,081,072,521 | 38 | SMC, any digit | 20 | 5 | 6e+07 | 0.00 | 1.08 | 0.00 | 0/5 | 40 | 0/200 | 131 | 0.0070 |
| thrice14 | 2,081,072,521 | 38 | SMC, top two digits | 5 | 5 | 6e+07 | 0.00 | 1.08 | 0.00 | 0/5 | 332 | 0/1662 | 27 | 0.0032 |
| thrice14 | 2,081,072,521 | 38 | SMC, top two digits | 20 | 5 | 6e+07 | 0.00 | 1.08 | 0.00 | 0/5 | 84 | 0/420 | 37 | 0.0048 |
| thrice14 | 2,081,072,521 | 38 | SMC, mixed | 5 | 5 | 6e+07 | 0.40 | 1.08 | 0.37 | 2/5 | 206 | 0/1032 | 50 | 0.0053 |
| thrice14 | 2,081,072,521 | 38 | SMC, mixed | 20 | 5 | 6e+07 | 0.00 | 1.08 | 0.00 | 0/5 | 54 | 0/269 | 115 | 0.0061 |
<!-- /TABLES -->

## 3. What a positive result would have needed

The sampler could only win if conditioning on φ ≤ τ concentrated the
population on roots whose *unseen* digits are more likely to be good, i.e. if
the score were correlated along the proposal moves. The measured acceptance
rates say how correlated it is: at the last levels 0.3–3.5% of proposals keep
φ ≤ τ, against a base rate for a fresh uniform root of roughly the level
probability itself. That small gain is the edge locality (a proposal at
position i keeps the bottom output digits below i), and it is paid for by the
rejected proposals and by the loss of diversity. Nothing in the middle digits
correlates, which is the same wall the algorithm report and the H1 test hit.
Transfer to K = 1, where collisions are forbidden outright, could only be
worse.

## Files

- `smc.c`: sampler and control; `campaign.sh`: the runs;
  `results/smc.jsonl`: one JSON line per run with per-level statistics of the
  first episode and every witness found; `results/smc_stallstop.jsonl`: the
  earlier stop-at-stall version.
- `summarize.py`: the table above.
