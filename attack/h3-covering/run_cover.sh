#!/bin/sh
# Runs cover for every M in [2, Mmax] coprime to b, for the given (b, s, c). One JSON line per M.
# usage: ./run_cover.sh b s c Mmax outfile
b=$1; s=$2; c=$3; Mmax=$4; out=$5
: > "$out"
Ms=$(python3 -c "
from math import gcd
print(' '.join(str(M) for M in range(2, $Mmax+1) if gcd(M,$b)==1))")
./cover $b $s $c $Ms >> "$out"
