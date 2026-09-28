# H1: can the possible values of middle digits reject whole batches?

2026-09-28. Hypothesis H1 of [NEXT_HYPOTHESES.md](../NEXT_HYPOTHESES.md): among
batches of roots with a fixed prefix and suffix and two or more free root
digits that survive the existing end checks, a substantial fraction fail a
joint capacity (Hall) test that uses the *domains* of the cube's unresolved
middle digits, and the rejection persists as the batch grows.

## Verdict: killed

The oracle test was run exactly on the whole k-nice testbed (nice bases 25
and 30; twice-nice 15, 17, 19; thrice-nice 13, 14; 23 configurations, about
5.4×10⁹ roots, every root enumerated).

- **With two or three free root digits, the middle-third domains are the whole
  alphabet.** In every one of the 15 such configurations, the mean domain size
  of a cube position in [L, 2L) is 1.000·b, at least 99.9% of those positions
  admit every digit, and adding them to the Hall test rejects **exactly zero**
  additional batches.
- **With one free digit (a batch of b roots) they are 64% of the alphabet**
  (0.637–0.647·b in all eight configurations, the value 1 − 1/e ≈ 0.632 of b
  random draws), and the additional rejection is 0 to 1,365 batches out of
  10⁵–10⁸ surviving ones: at most 9×10⁻⁶ of the roots, against the 10%
  threshold the hypothesis set for itself.
- **Soundness held throughout.** No batch containing any of the 60 known
  witnesses (1 + 1 + 4 twice-nice, 16 + 38 thrice-nice) was rejected by any
  variant.
- **The reason is arithmetic, not statistical.** For a batch that varies a
  block of f root digits above position k, the cube's digits in [k, 2k) are
  digits of an arithmetic progression in the block value (§4), and every digit
  in the middle third moves through a pseudo-random sequence as the block
  varies. A batch of J roots therefore leaves each middle position with about
  b(1 − (1 − 1/b)^J) possible values: 0.63b for J = b, all of b for J ≥ b².
  Domains are informative only when the batch is too small to save any work,
  and the joint set of tuples a batch actually realizes is the enumeration
  itself.

The hypothesis's own continue/stop rule ("at least 10% additional root-weighted
rejection, persisting from two to three free digits") is missed by more than
three orders of magnitude at one free digit and by everything at two or three.
Do not build the cheap-superset version: exact domains already carry no
information.

## 1. What was computed

`domains.c` takes a base b, multiplicity K, the exact interval [lo, hi], the
lengths s, c, the root length L, and a split (t, k). A batch is

    n = P·b^(L−t) + m·b^k + R,   m = 0, …, b^f − 1  (f = L − t − k),

intersected with [lo, hi]. For each batch:

1. **Certified positions.** The bottom k digits of n² and n³ (from R), and the
   top digits of n² and n³ that are constant over [n_min, n_max] (the interval
   test the public client's leading-digit filter uses).
2. **Existing end check.** Reject if any value occurs more than K times among
   the certified digits.
3. **Oracle domains.** Enumerate every root of a surviving batch and record,
   for each unresolved position, the exact set of values it takes.
4. **Hall test with capacities K − (certified count).** Variant *no middle*
   uses every unresolved position except the cube's positions [L, 2L);
   variant *with middle* uses all of them. The difference is the contribution
   of the middle third. (Matching by augmenting paths; positions are the left
   side, digit values with capacities the right side.)
5. **Soundness.** Every root is also checked exactly for K-niceness; a batch
   containing a witness must never be rejected, and the program aborts if one
   is.

Reproduce (`THR` threads; about 40 minutes on 3 cores):

```sh
clang -O3 -march=native -o domains domains.c -lpthread
THR=3 ./run_cases.sh          # writes results/domains.jsonl
python3 summarize.py          # the tables below
```

## 2. Results

<!-- TABLES -->
| Case | f | (t, k) | Batches | End-check rejected | Surviving | Hall rejected, no middle | Hall rejected, with middle | Extra batches | Extra, root-weighted | Middle domain / b | Hits | Sound |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| nice-25 | 1 | (2, 2) | 257,500 | 153,412 | 104,088 | 8,286 | 8,286 | 0 | 0.0e+00 | 0.637 | 0 | yes |
| nice-25 | 2 | (2, 1) | 10,300 | 4,072 | 6,228 | 194 | 194 | 0 | 0.0e+00 | 1.000 | 0 | yes |
| nice-25 | 2 | (1, 2) | 10,625 | 4,377 | 6,248 | 149 | 149 | 0 | 0.0e+00 | 1.000 | 0 | yes |
| nice-25 | 3 | (1, 1) | 425 | 109 | 316 | 0 | 0 | 0 | 0.0e+00 | 1.000 | 0 | yes |
| nice-30 | 1 | (3, 2) | 16,479,900 | 11,928,947 | 4,550,953 | 550,792 | 550,795 | 3 | 1.8e-07 | 0.638 | 0 | yes |
| nice-30 | 1 | (2, 3) | 16,497,000 | 12,048,730 | 4,448,270 | 515,401 | 516,371 | 970 | 5.9e-05 | 0.640 | 0 | yes |
| nice-30 | 2 | (2, 2) | 549,900 | 303,901 | 245,999 | 16,314 | 16,314 | 0 | 0.0e+00 | 1.000 | 0 | yes |
| nice-30 | 3 | (2, 1) | 18,330 | 7,411 | 10,919 | 223 | 223 | 0 | 0.0e+00 | 1.000 | 0 | yes |
| twice-15 | 1 | (3, 2) | 451,575 | 121,689 | 329,886 | 9,458 | 9,468 | 10 | 1.3e-05 | 0.645 | 1 | yes |
| twice-15 | 2 | (2, 2) | 30,150 | 4,564 | 25,586 | 261 | 261 | 0 | 0.0e+00 | 1.000 | 1 | yes |
| twice-15 | 3 | (2, 1) | 2,010 | 74 | 1,936 | 131 | 131 | 0 | 0.0e+00 | 1.000 | 1 | yes |
| twice-17 | 1 | (3, 3) | 3,537,360 | 1,238,390 | 2,298,970 | 22,831 | 22,874 | 43 | 6.2e-06 | 0.640 | 1 | yes |
| twice-17 | 2 | (3, 2) | 208,080 | 46,931 | 161,149 | 372 | 372 | 0 | 0.0e+00 | 1.000 | 1 | yes |
| twice-17 | 3 | (2, 2) | 12,427 | 1,904 | 10,523 | 3 | 3 | 0 | 0.0e+00 | 1.000 | 1 | yes |
| twice-19 | 1 | (4, 3) | 79,536,964 | 30,409,880 | 49,127,084 | 517,845 | 518,354 | 509 | 6.4e-06 | 0.644 | 4 | yes |
| twice-19 | 2 | (3, 3) | 4,190,849 | 1,054,313 | 3,136,536 | 8,470 | 8,470 | 0 | 0.0e+00 | 1.000 | 4 | yes |
| twice-19 | 3 | (3, 2) | 220,571 | 33,521 | 187,050 | 133 | 133 | 0 | 0.0e+00 | 1.000 | 4 | yes |
| thrice-13 | 1 | (4, 3) | 9,284,522 | 2,023,695 | 7,260,827 | 30,314 | 30,368 | 54 | 5.8e-06 | 0.647 | 16 | yes |
| thrice-13 | 2 | (3, 3) | 716,222 | 107,830 | 608,392 | 198 | 198 | 0 | 0.0e+00 | 1.000 | 16 | yes |
| thrice-13 | 3 | (3, 2) | 55,094 | 6,025 | 49,069 | 3 | 3 | 0 | 0.0e+00 | 1.000 | 16 | yes |
| thrice-14 | 1 | (4, 4) | 148,669,920 | 37,886,234 | 110,783,686 | 1,207,578 | 1,208,943 | 1,365 | 9.0e-06 | 0.643 | 38 | yes |
| thrice-14 | 2 | (4, 3) | 10,619,280 | 1,945,384 | 8,673,896 | 45,838 | 45,838 | 0 | 0.0e+00 | 1.000 | 38 | yes |
| thrice-14 | 3 | (3, 3) | 760,088 | 102,806 | 657,282 | 2,114 | 2,114 | 0 | 0.0e+00 | 1.000 | 38 | yes |

Domain-size distribution of the cube's middle-third positions in surviving batches (fraction of positions with domain size = b, i.e. the whole alphabet):

| Case | f | Batch size b^f | Positions | Mean domain / b | Share with full alphabet | Smallest domain seen |
|---|---:|---:|---:|---:|---:|---:|
| nice-25 | 1 | 25 | 520,440 | 0.637 | 0.0000 | 2 |
| nice-25 | 2 | 625 | 31,140 | 1.000 | 0.9999 | 24 |
| nice-25 | 2 | 625 | 31,240 | 1.000 | 1.0000 | 25 |
| nice-25 | 3 | 15,625 | 1,580 | 1.000 | 1.0000 | 25 |
| nice-30 | 1 | 30 | 27,305,718 | 0.638 | 0.0000 | 2 |
| nice-30 | 1 | 30 | 26,689,620 | 0.640 | 0.0003 | 1 |
| nice-30 | 2 | 900 | 1,475,994 | 1.000 | 1.0000 | 30 |
| nice-30 | 3 | 27,000 | 65,514 | 1.000 | 1.0000 | 30 |
| twice-15 | 1 | 15 | 1,979,316 | 0.645 | 0.0001 | 1 |
| twice-15 | 2 | 225 | 153,516 | 1.000 | 1.0000 | 12 |
| twice-15 | 3 | 3,375 | 11,616 | 1.000 | 1.0000 | 15 |
| twice-17 | 1 | 17 | 16,092,790 | 0.640 | 0.0001 | 1 |
| twice-17 | 2 | 289 | 1,128,043 | 1.000 | 0.9999 | 13 |
| twice-17 | 3 | 4,913 | 73,661 | 1.000 | 1.0000 | 17 |
| twice-19 | 1 | 19 | 393,016,672 | 0.644 | 0.0000 | 1 |
| twice-19 | 2 | 361 | 25,092,288 | 1.000 | 0.9999 | 11 |
| twice-19 | 3 | 6,859 | 1,496,400 | 1.000 | 1.0000 | 19 |
| thrice-13 | 1 | 13 | 58,086,616 | 0.647 | 0.0002 | 1 |
| thrice-13 | 2 | 169 | 4,867,136 | 1.000 | 0.9991 | 7 |
| thrice-13 | 3 | 2,197 | 392,552 | 1.000 | 1.0000 | 13 |
| thrice-14 | 1 | 14 | 997,053,174 | 0.643 | 0.0002 | 1 |
| thrice-14 | 2 | 196 | 78,065,064 | 1.000 | 0.9997 | 4 |
| thrice-14 | 3 | 2,744 | 5,915,538 | 1.000 | 1.0000 | 14 |
<!-- /TABLES -->

Notes on the columns:

- *Hall rejected, no middle* counts batches that the existing end check passes
  but a Hall test on the **edge-adjacent** unresolved positions rejects. Those
  positions sit just above the certified bottom digits and just below the
  certified top digits; their domains are small for the same reason edge
  filters work (a digit adjacent to a certified run is affine in one free
  digit, or differs only by a carry). This is a mild strengthening of the end
  check (about 8–12% of surviving batches at one free digit for nice-25 and
  nice-30, 0.4% for thrice-13), and it is edge information, not middle
  information.
- *Extra batches* is the number rejected only when the middle third is added.

## 3. Why the middle third cannot help at any useful batch size

Write n = A + M·b^k with the free block M < b^f above position k and A fixed
(prefix and suffix). Then

    n³ = A³ + 3A²M·b^k + 3AM²·b^(2k) + M³·b^(3k).

For positions p with k ≤ p < 2k only the first two terms matter modulo b^(p+1),
so the digits of n³ in [k, 2k) are the digits of ⌊A³/b^k⌋ + 3A²·M reduced
modulo b^k: an arithmetic progression in M with the pseudo-random difference
3A² mod b^k. Digit q of an arithmetic progression with a "random" difference
visits values like a rotation of the circle of length b; J steps hit about
b(1 − (1 − 1/b)^J) of them. Higher positions add the M² and M³ terms and are
no more constrained. The measured domain means, 0.637–0.647·b at J = b and
1.000·b at J ≥ b², match this.

So the domains shrink only for batches of fewer than b roots, where the
batch is already the size of one digit's worth of enumeration, and even there
Hall's condition cannot fail: about L uncertified middle positions with
domains of 0.6b values each have a union that is the whole alphabet. The
exact per-position domains are therefore a relaxation that never binds. The
only object with information is the set of tuples a batch realizes, and
listing it is exactly the enumeration the hypothesis hoped to avoid.

## 4. Relation to the earlier 80% ceiling

The algorithm report argued that no *fixed-value* certificate from the two
ends reaches the cube's middle third. This test covers the set-valued
relaxation the review said that argument left open, for exact domains, and
finds it empty. Cheap supersets (interval arithmetic, residues) can only be
larger than the exact domains, so they cannot do better.

## Files

- `domains.c`: the oracle (enumeration, certification, domains, Hall test,
  soundness check); `run_cases.sh`: the 23 configurations;
  `results/domains.jsonl`: one JSON line each, with domain-size histograms.
- `summarize.py`: the tables above.
