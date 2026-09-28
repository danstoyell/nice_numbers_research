#!/bin/sh
# Other word lengths and larger moduli (the part of campaign.sh after the main bases).
cd /home/user/nice_numbers_research/attack/h3-covering
for s in 2 3 5 6 7 8; do c=$((10 - s)); ./run_cover.sh 10 $s $c 1000 results/cover_b10_s$s.jsonl; done
for s in 3 4 6 7 8 9; do c=$((12 - s)); ./run_cover.sh 12 $s $c 400 results/cover_b12_s$s.jsonl; done
./run_cover.sh 12 5 7 1728 results/cover_b12_s5_big.jsonl
echo EXTRA_DONE
