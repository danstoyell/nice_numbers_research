#!/bin/bash
# Twice-nice 25 then 26 (resumable from logs). THREADS from $1 (default 5).
cd "$(dirname "$0")"
TH=${1:-5}
for kb in "2 25" "2 26"; do
  set -- $kb
  echo "=== k=$1 b=$2 start $(date) threads=$TH"
  python3 run.py --k "$1" --base "$2" --threads "$TH" --chunks 2000 --json "results/run_k$1_b$2.json" | tail -c 400
  echo "=== k=$1 b=$2 end $(date)"
done
