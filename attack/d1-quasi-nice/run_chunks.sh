#!/bin/bash
# Resumable chunked run: run_chunks.sh BASE T J AP NCHUNKS PAR
# Each chunk writes results/b$BASE_t$T_j$J_ap$AP/chunk_$i.json atomically; finished chunks are skipped.
set -u
B=$1; T=$2; J=$3; AP=$4; N=$5; PAR=${6:-3}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$HERE/results/b${B}_t${T}_j${J}_ap${AP}
mkdir -p "$OUT"
BIN=$HERE/bin/qn12_b$B
[ -x "$BIN" ] || clang -O3 -mcpu=native -DBASE=$B -DHSPLIT=6 -o "$BIN" "$HERE/qn12.c"
export BIN T J AP N OUT
seq 0 $((N-1)) | xargs -P "$PAR" -I{} bash -c '
  f=$OUT/chunk_{}.json
  [ -s "$f" ] && exit 0
  "$BIN" $T $J $AP {} $N > "$f.tmp" && mv "$f.tmp" "$f"
'
echo "done $B $(ls $OUT/chunk_*.json | wc -l) / $N"
