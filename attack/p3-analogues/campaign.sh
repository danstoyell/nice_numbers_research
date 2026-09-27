#!/bin/bash
# Priority-ordered production runs (5 threads). Resumable: each run.py call
# resumes from its log. Summaries go to results/run_k{K}_b{B}.json.
cd "$(dirname "$0")"
for kb in "2 24" "3 18" "2 25" "2 26"; do
  set -- $kb
  echo "=== k=$1 b=$2 start $(date)"
  python3 run.py --k "$1" --base "$2" --threads 5 --chunks 2000 --json "results/run_k$1_b$2.json" | tail -c 600
  echo "=== k=$1 b=$2 end $(date)"
done
