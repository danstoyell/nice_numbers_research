# Path 1, structure: can a structured family of (n, b) make niceness likely?

2026-09-27. Hypothesis: some structured family of (n, b) raises the chance of niceness over random by a factor like e^(cb), enough that searching the family at bases 60–1000 has real odds, as structured families did for the Hadamard-668 and rank-31 elliptic curve records.

## Verdict: killed

No structured family comes near family size × P(nice) = 1 at any base up to 1000, and no nice number was found. Every member scanned was checked exactly; anything reaching deficiency 0 would have gone through `verify()`.

- **Best family:** n = (a·b^m + r)/d with d² between 0.4b and b. It makes the square repeat-free for free, but the cube stays random.
  - Even granting a repeat-free square to every member, the expected nice count is at most 10^−22.9 at every base from 60 to 1000.
- **Every other family scores worse than random.**
- **Why the √b vs ∛b tension is real:**
  - Structure can force the square's digits distinct.
  - The cube's ~0.6b digits can be made non-random only two ways, and both wreck the square:
    - a local denominator q ≤ b leaves the square too few remainders;
    - a digit rotation produces overlapping linear ramps.
  - While the cube is random, a family needs 10^38 (b=100) to 10^392 (b=1000) square-distinct members, far more than any structured family has.

## 1. What a family would have to achieve (`accounting.py`)

Model: a family has F = b^f members. In each member, R output digits vary like random digits and the rest are structured (assumed distinct). The expected count is E = b^f · R!/b^R. κ = R/f is the exchange rate: random output digits created per free input digit. The generic interval has κ = 5.

| b | log10 E, generic interval | Most random digits a 10^20-member family can leave | Share of digits that must be forced | κ needed | Smallest family with E ≥ 1 at κ = 5 |
|---:|---:|---:|---:|---:|---:|
| 100 | −2.0 | 17 | 83% | ≤ 1.7 | none |
| 150 | 1.6 | 14 | 91% | ≤ 1.5 | 10^64 |
| 300 | 20.0 | 11 | 96% | ≤ 1.4 | 10^127 |
| 1000 | 167.6 | 8 | 99.2% | ≤ 1.2 | 10^407 |

**Measured κ (`kappa.py`).** One free block of h digits inside a structured root, placed at the bottom, top or middle:
- with non-trivial structure, κ = 9.0–9.7 (up to 14 for a middle block at base 200);
- when the "structure" is all zeros (the excluded sparse case), and for the generic interval, κ = 5.

The count follows from the cross terms: R², 2RS, R³, 3R²S and 3RS² each leave a random output region, giving 9h digits.

At κ = 9, E is largest when f → 0 at every base up to 1000. So the only possible survivors are closed-form families with nearly all b output digits forced.

## 2. Closed-form rational families: what can be forced

Take n = N/d with N a sum of a few blocks. Away from block boundaries, square digits are ⌊bρ/d²⌋ along the orbit ρ → bρ mod d², and cube digits likewise mod d³.

- **Sweet spot** (d² ∈ [0.4b, b], ord_{d²}(b) ≥ 0.4b; 405 of 565 admissible bases in 60–1000 have such a d).
  - The square is injective, so it can be repeat-free (1.4–1.9% of members).
  - The cube (d³ > b) matches the random model once the square is repeat-free:

    | b | Cube repeats: measured vs model | Square–cube collisions: measured vs model |
    |---:|---:|---:|
    | 104 | 16.1 vs 15.1 | 18.0 vs 18.9 |
    | 500 | 73.8 vs 74.2 | 87.4 vs 90.3 |

  - Result: E ≤ F · c!/b^c ≤ 10^−22.9 at every sweet base, with F counting every a and every |r| ≤ b² (c = cube length).
- **Rotation denominators** (d | b^j ± 1 for small j, e.g. 41 | b⁵−1 at b = 1000).
  - The square is a near repeat-free linear ramp; the cube is a quadratic ramp and stays random.
  - At b = 1000 with the square repeat-free: cube repeats 147.5 vs model 148.6; collisions 181.4 vs 180.5. The same bound applies.
- **d³ ≤ b.**
  - The cube is injective, but the square has only d² ≤ b^{2/3} remainders, fewer than 0.4b once b > 15.
  - Square repeats: 32.3 vs 6.9 random at b = 100; 68.4 vs 14.0 at b = 200. Dead.
- **Special bases b ∓ 1 = t³ with d = t².** The cube becomes a rotation, but the square has period t. Dead:

  | b | Cube repeats (family / random) | Square repeats (family / random) |
  |---:|---:|---:|
  | 65 | 8.5 / 9.5 | 12.4 / 4.4 |
  | 124 | 16.4 / 18.2 | 26.9 / 8.8 |

- **Cube-linear periodic roots** n = c·R_k(b^j) with (b^j − 1) | c³. This is the one route found where the period argument doesn't bind (j = 2, 3 at b ≤ 1000).
  - Both powers really are piecewise-linear ramps: 4–5 breaks, against 100% for random n.
  - All 18,985 members were tested exhaustively (j = 2, 3, every admissible b ≤ 1000, offsets |e| ≤ 2). None is nice.
  - The median mean deficiency is 2.1× the general-periodic control; the family beats the control only at b ≤ 37.
  - Dead: the up- and down-ramps are overlapping segments of one progression, so they revisit the same digits.
- **Mixed** (square linear runs with cube q ≤ b): the square needs d ≥ 0.4b with d | b−1, and the cube needs d ≤ b^{1/3}. Each block's square and cube regions share one d, so they are incompatible.

**Why a repeat-free square alone cannot help.** With a random cube, E ≥ 1 needs at least b^c/c! square-distinct members:

| b | Members needed (b^c/c!) | Candidates in the interval | Square-distinct candidates in the interval |
|---:|---:|---:|---:|
| 100 | 10^38.1 | 10^39.9 | 10^35.9 |
| 1000 | 10^391.9 | 10^600 | 10^559.5 |

Taking every square-distinct candidate only reproduces the generic count, so forcing the square is an edge-type saving worth about e^(0.09b), not a boost.

## 3. Direct family scans against random (`family_scan.py`)

Deficiency is b minus the number of distinct digits; 3,000 seeded samples per family.
- **A:** single block, d ≤ 200.
- **B:** two blocks, d ≤ 12.
- **C:** d dividing b^j ± 1 for j ≤ 3.

Each cell is mean / min.

| b | A | B | C | Random |
|---:|---:|---:|---:|---:|
| 100 | 36.9 / 24 | 46.2 / 25 | 37.1 / 24 | 36.7 / 25 |
| 200 | 74.1 / 56 | 100.4 / 56 | 76.1 / 56 | 73.5 / 57 |
| 500 | 191.3 / 145 | 293.0 / 170 | 201.0 / 150 | 184.1 / 158 |
| 1000 | 409.5 / 303 | 750.0 / 391 | 401.9 / 310 | 367.8 / 335 |

- Every family's mean is at or above random.
- The longer lower tails come entirely from members whose square is repeat-free (0–2 square repeats) and whose cube is random (`tail_check.py`, `cube_check.py`). They are the square-only saving, not a joint boost.

## 4. Ideas considered without new runs

- **Free choice of base.** A fixed n meets the length condition in at most one base (research/transformations.md). Families polynomial in b are the existing 19M-instance constructions run.
- **Symmetry, as in the Hadamard-668 construction.** This needs a group acting compatibly on n and the output word; carries stop squaring from commuting with any non-trivial digit permutation. Argued, not tested.
- **Mestre–Nagao-style local forcing.** The analogue is congruences, and only the digit-sum class exists (critique).

## What would reopen this

A mechanism that makes most of the cube's 0.6b digits non-random while the square stays distinct, other than q ≤ b (fails on the remainder pool) or a rotation (fails on overlapping ramps). None is known.

## Incomplete or approximate

- The per-base measurement in `sweet_spot.py` was stopped at b = 1000 because its enumeration was slow; `cube_check.py` covers that base instead.
- Every κ value is measured, not proved.
- The E bounds assume the random-digit model for the parts measured to be random.
- One claim is argued without runs: symmetry constructions cannot work.

## Files

All in `attack/p1-structure/`:
- `accounting.py`
- `kappa.py`
- `family_scan.py`
- `split_stats.py`
- `sweet_spot.py`
- `cube_check.py`
- `tail_check.py`
- `periodic_scan.py`
- `results/` (every quoted output, as .txt and .json)

## Sources

Project files only:
- critique/research-directions.md (the 40%/90% targets and the congruence result)
- research/constructions.md (the fixed-denominator theorem)
- research/transformations.md (the one-base-per-n result and growing denominators)
- RESEARCH_LOG.md (the 19M-instance construction run)
