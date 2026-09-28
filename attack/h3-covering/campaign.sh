#!/bin/sh
# Main campaign: nice-number lengths (s,c) for admissible bases; s=round(2b/5) where no interval exists.
set -e
cd "$(dirname "$0")"
./run_cover.sh 10 4 6 1000 results/cover_b10_s4.jsonl
./run_cover.sh 12 5 7 400 results/cover_b12_s5.jsonl
./run_cover.sh 13 5 8 400 results/cover_b13_s5.jsonl
./run_cover.sh 14 6 8 400 results/cover_b14_s6.jsonl
./run_cover.sh 15 6 9 300 results/cover_b15_s6.jsonl
./run_cover.sh 11 4 7 300 results/cover_b11_s4.jsonl
./run_cover.sh 16 6 10 256 results/cover_b16_s6.jsonl
./run_cover.sh 17 7 10 289 results/cover_b17_s7.jsonl
./run_cover.sh 18 7 11 324 results/cover_b18_s7.jsonl
# other splits, to see the dependence on word length (b = 10 and 12)
for s in 2 3 5 6 7 8; do c=$((10 - s)); ./run_cover.sh 10 $s $c 1000 results/cover_b10_s$s.jsonl; done
for s in 3 4 6 7 8 9; do c=$((12 - s)); ./run_cover.sh 12 $s $c 400 results/cover_b12_s$s.jsonl; done
./run_cover.sh 12 5 7 1728 results/cover_b12_s5_big.jsonl
echo CAMPAIGN_DONE
