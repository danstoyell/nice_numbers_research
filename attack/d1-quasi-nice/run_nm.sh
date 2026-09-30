#!/bin/bash
# Resumable exhaustive deficiency histograms: run_nm.sh BASE NCHUNKS PAR
set -u
B=$1; N=$2; PAR=${3:-1}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$HERE/results/nm_b$B
mkdir -p "$OUT"
BIN=$HERE/bin/nm12_b$B
[ -x "$BIN" ] || clang -O3 -mcpu=native -DBASE=$B -o "$BIN" "$HERE/nm12.c"
export BIN N OUT
seq 0 $((N-1)) | xargs -P "$PAR" -I{} bash -c '
  f=$OUT/chunk_{}.json
  [ -s "$f" ] && exit 0
  "$BIN" {} $N > "$f.tmp" && mv "$f.tmp" "$f"
'
echo "done nm $B $(ls $OUT/chunk_*.json | wc -l) / $N"
