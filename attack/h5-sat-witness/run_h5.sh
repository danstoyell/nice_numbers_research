#!/bin/sh
# H5 campaign: SAT first-witness (2 randomized variants, 600 s wall limit each) and the
# enumerator baseline (start at lo, and 5 random starts) on unplanted K-nice instances.
D=/home/user/nice_numbers_research/attack/h5-sat-witness
cd $D
: > results/first_hit.jsonl
base() { # b K lo hi s c
  for st in lo 1 2 3 4 5; do ./first_hit $1 $2 $3 $4 $5 $6 $st >> results/first_hit.jsonl; done
}
base 9 3 59049 122826 11 16
base 10 3 464159 999999 12 18
base 14 2 1296233 2012353 11 17
base 15 2 4618673 11390624 12 18
base 16 2 16777216 42275935 13 19
base 13 3 226242996 346922420 16 23
python3 knice_sat.py --cases 2:14 2:15 3:13 --variants 2 --limit 600 > results/knice_sat_main.log 2>&1
echo H5_DONE >> results/knice_sat_main.log
