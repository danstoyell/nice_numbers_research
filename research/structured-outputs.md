# Affine permutations of the complete output word

2026-09-25. This is a finite exclusion of one output family, not a
restriction on arbitrary nice numbers.

Instead of choosing the root, arrange the entire output alphabet as

`w_j = (a*j+c) mod b`, `0<=j<b`, `gcd(a,b)=1`.

Split this permutation after the required square length `s`, obtaining
integers `A` and `C`. Reject a zero at either block's leading position.
For a solution we need `A=n²`, `C=n³`, hence `A³=C²`.
Every rotation is included, so putting the cube block first gives the
same family. Negative steps, including reversal, are also included.

The implementation screens the necessary equality modulo `2^64`.
Any survivor is reconstructed with full integers and checked by integer
square root, exact cubing, and the independent nice-number verifier.
Modular failure is an exact rejection; modular success alone would not
establish a solution.

The scan through base 500 tested **13,349,176** words with legal leading
digits. None passed the modular screen. Bases already excluded by the
length or digit-sum parity conditions were omitted. Thus this family
contains no nice number in any base through 500. It does not even contain
the known decimal example; this is a narrow construction experiment.

```sh
python3 scripts/structured_outputs.py --max-base 500 \
  --output results/structured-outputs.json
```

[Raw results](../results/structured-outputs.json) record every considered
base and its count. The rotation recurrence was compared with direct
integer evaluation in 2,906 cases. Runtime was about 6.6 seconds.

There is also a simple necessary condition within this family. The last
square and cube digits differ by `a*s mod b`, so

`gcd(n²(n-1),b) = gcd(s,b)`.

In an even base, coprimality makes `a` odd and the full word alternates
parity. Since a square and cube of the same root have equal parity,
their last positions must be an even distance apart: `s` must be even.
Thus the even bases congruent to 2 or 3 modulo 5 are excluded from this
family in all sizes. This condition concerns affine output order only.

No all-base obstruction for the remaining affine cases was established.
Increasing this scan without a new structural argument has low priority.
