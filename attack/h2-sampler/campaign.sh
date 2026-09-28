#!/bin/sh
# H2 campaign. args: b K lo hi s c L P p0 runs seed mode budget thin max_stall
D=/home/user/nice_numbers_research/attack/h2-sampler
out=$D/results/smc.jsonl; : > $out
run() { # case-name b K lo hi s c L budget
  name=$1; shift; b=$1; K=$2; lo=$3; hi=$4; s=$5; c=$6; L=$7; budget=$8
  for mode in 9 0 1 2; do
    for thin in 5 20; do
      [ $mode = 9 ] && [ $thin = 20 ] && continue
      echo "# case=$name mode=$mode thin=$thin" >> $out
      $D/smc $b $K $lo $hi $s $c $L 2000 0.2 5 $((mode*1000+thin)) $mode $budget $thin 40 >> $out
    done
  done
}
run thrice10 10 3 464159 999999 12 18 6 2000000
run twice15 15 2 4618673 11390624 12 18 6 20000000
run thrice13 13 3 226242996 346922420 16 23 8 30000000
run twice17 17 2 99521747 159585272 14 20 7 30000000
run thrice14 14 3 1475789056 3556861576 17 25 9 60000000
echo H2_DONE >> $out
