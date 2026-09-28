#!/bin/sh
# H1 oracle campaign on the k-nice testbed. Arguments to domains: b K lo hi s c L t k threads
cd /home/user/nice_numbers_research/attack/h1-domains
THR=${THR:-3}
out=results/domains.jsonl
: > $out
run() { echo "# $*" >> $out; /home/user/nice_numbers_research/attack/h1-domains/domains "$@" $THR >> $out 2>> results/errors.log; }
# nice numbers (K=1), known: no solutions in these bases
run 25 1 3339797 9765624 10 15 5 2 2
run 25 1 3339797 9765624 10 15 5 2 1
run 25 1 3339797 9765624 10 15 5 1 2
run 25 1 3339797 9765624 10 15 5 1 1
# twice-nice (K=2): base 15 (1 hit), 17 (1 hit), 19 (4 hits)
run 15 2 4618673 11390624 12 18 6 3 2
run 15 2 4618673 11390624 12 18 6 2 2
run 15 2 4618673 11390624 12 18 6 2 1
run 17 2 99521747 159585272 14 20 7 3 3
run 17 2 99521747 159585272 14 20 7 3 2
run 17 2 99521747 159585272 14 20 7 2 2
# thrice-nice (K=3): base 13 (16 hits)
run 13 3 226242996 346922420 16 23 8 4 3
run 13 3 226242996 346922420 16 23 8 3 3
run 13 3 226242996 346922420 16 23 8 3 2
# nice base 30 (K=1), 4.9e8 roots
run 30 1 234613921 728999999 12 18 6 3 2
run 30 1 234613921 728999999 12 18 6 2 3
run 30 1 234613921 728999999 12 18 6 2 2
run 30 1 234613921 728999999 12 18 6 2 1
# twice-nice base 19 (4 hits), 1.5e9 roots
run 19 2 2385208823 3896296578 15 23 8 4 3
run 19 2 2385208823 3896296578 15 23 8 3 3
run 19 2 2385208823 3896296578 15 23 8 3 2
# thrice-nice base 14 (38 hits), 2.1e9 roots
run 14 3 1475789056 3556861576 17 25 9 4 4
run 14 3 1475789056 3556861576 17 25 9 4 3
run 14 3 1475789056 3556861576 17 25 9 3 3
echo CASES_DONE >> $out
