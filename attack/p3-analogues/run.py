#!/usr/bin/env python3
"""Driver for knice.c: compile per (base, k, J), run with a checkpoint log,
re-verify every hit with exact Python integers, and summarise coverage.

Usage:
  python3 run.py --k 3 --base 16 --threads 5
  python3 run.py --k 2 --base 26 --threads 5 --j 6 --chunks 4000
  python3 run.py --k 2 --base 22 --summary-only      # parse an existing log

The log (logs/k{K}_b{B}_j{J}[_nofilter].log) is the checkpoint: rerunning the
same command resumes, skipping chunks already recorded.
"""
import argparse
import json
import math
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "critique" / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
from twice_nice import intervals_total_length  # noqa: E402  (exact integer roots)


# ------------------------------------------------------------ exact check ---
def digits_le(n, b):
    out = []
    while n:
        n, d = divmod(n, b)
        out.append(d)
    return out or [0]


def is_k_nice(n, b, k):
    """Independent exact check with Python integers."""
    sq, cu = digits_le(n * n, b), digits_le(n ** 3, b)
    if len(sq) + len(cu) != k * b:
        return False
    c = Counter(sq + cu)
    return len(c) == b and all(v == k for v in c.values())


# ------------------------------------------------------------------ setup ---
def interval(b, k):
    ivs = intervals_total_length(b, k * b)
    if not ivs:
        return None
    (lo, hi, s, c), = ivs
    return lo, hi, s, c


def choose_j(b, k, lo, hi, s, tmin):
    """Largest J with at least tmin steps per class (J >= 1, J < s)."""
    j = 1
    while j + 1 < s and (hi - lo + 1) // ((b - 1) * b ** (j + 1)) >= tmin:
        j += 1
    return j


def perm_a(b, j):
    """A multiplier coprime to b, near 0.618 * b^j (scatters chunks over residues)."""
    m = b ** j
    a = max(1, int(m * 0.6180339887)) | 1
    while math.gcd(a, b) != 1 or math.gcd(a, m) != 1:
        a += 1
    return a % m if m > 1 else 1


def binary_for(b, k, s, c, j):
    out = HERE / "bin" / f"knice_b{b}_k{k}_s{s}_c{c}_j{j}"
    src = HERE / "knice.c"
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        out.parent.mkdir(exist_ok=True)
        subprocess.run(["clang", "-O3", "-mcpu=apple-m4", f"-DB={b}", f"-DK={k}", f"-DSL={s}",
                        f"-DCL={c}", f"-DJ={j}", "-o", str(out), str(src), "-lpthread"], check=True)
    return out


# ------------------------------------------------------------------- log ---
def parse_log(path):
    chunks, header = {}, None
    for line in Path(path).read_text().splitlines():
        if line.startswith("# start"):
            header = dict(kv.split("=", 1) for kv in line.split()[2:])
        if not line.startswith("C "):
            continue
        f = line.split()
        c = int(f[1])
        rec = {"rho": int(f[2]), "rho_pass": int(f[3]), "lanes": int(f[4]), "steps": int(f[5]),
               "survivors": int(f[6]), "secs": float(f[7]), "nhits": int(f[8]),
               "hits": [int(x) for x in f[9:]]}
        assert len(rec["hits"]) == rec["nhits"], ("hit list truncated", c)
        chunks.setdefault(c, rec)
    return header, chunks


def summarise(b, k, lo, hi, s, c, j, nchunks, a, log, filters):
    header, chunks = parse_log(log)
    hits = sorted({h for r in chunks.values() for h in r["hits"]})
    for n in hits:
        assert lo <= n <= hi and is_k_nice(n, b, k), ("C reported a non-solution", b, k, n)
    done = sorted(chunks)
    m = b ** j
    rho_total = sum(r["rho"] for r in chunks.values())
    out = {
        "base": b, "k": k, "lo": str(lo), "hi": str(hi), "square_digits": s, "cube_digits": c,
        "count": hi - lo + 1, "J": j, "chunks_total": nchunks, "chunks_done": len(done),
        "perm_a": a, "filters": bool(filters),
        "rho_done": rho_total, "rho_total": m, "complete": len(done) == nchunks and rho_total == m,
        "rho_pass": sum(r["rho_pass"] for r in chunks.values()),
        "lanes": sum(r["lanes"] for r in chunks.values()),
        "lane_steps": sum(r["steps"] for r in chunks.values()),
        "hash_survivors": sum(r["survivors"] for r in chunks.values()),
        "thread_seconds": sum(r["secs"] for r in chunks.values()),
        "observed": len(hits), "solutions": [str(h) for h in hits],
        "python_verified": True,
        "done_chunks": done if len(done) != nchunks else "all",
    }
    from model import m0, m0_partial  # M0 = critique model; partial = covered residues only
    full = m0(b, k)["m0_expected"]
    out["m0_expected_full"] = full
    out["m0_expected_covered"] = full if out["complete"] else m0_partial(b, k, lo, hi, j, nchunks, a, done)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--base", type=int, required=True)
    ap.add_argument("--j", type=int, default=None)
    ap.add_argument("--tmin", type=int, default=20000, help="min steps per class when choosing J")
    ap.add_argument("--chunks", type=int, default=None)
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--filters", type=int, default=1)
    ap.add_argument("--chunk-range", type=int, nargs=2, default=None)
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--json", default=None, help="write summary JSON here")
    args = ap.parse_args()
    b, k = args.base, args.k
    iv = interval(b, k)
    if iv is None:
        print(json.dumps({"base": b, "k": k, "interval": None}))
        return
    lo, hi, s, c = iv
    j = args.j or choose_j(b, k, lo, hi, s, args.tmin)
    m = b ** j
    nchunks = args.chunks or max(1, min(m, 64 if m < 10 ** 5 else 2000))
    a = perm_a(b, j)
    suffix = ("" if args.filters else "_nofilter") + (f"_{args.tag}" if args.tag else "")
    log = HERE / "logs" / f"k{k}_b{b}_j{j}_c{nchunks}{suffix}.log"
    log.parent.mkdir(exist_ok=True)
    if not args.summary_only:
        exe = binary_for(b, k, s, c, j)
        cmd = [str(exe), str(lo), str(hi), str(args.threads), str(nchunks), str(a), str(log),
               str(args.filters)]
        if args.chunk_range:
            cmd += [str(x) for x in args.chunk_range]
        t0 = time.monotonic()
        subprocess.run(cmd, check=True)
        wall = time.monotonic() - t0
    else:
        wall = None
    summ = summarise(b, k, lo, hi, s, c, j, nchunks, a, log, args.filters)
    summ["wall_seconds_last_invocation"] = wall
    summ["log"] = str(log.relative_to(ROOT))
    print(json.dumps(summ))
    if args.json:
        Path(args.json).write_text(json.dumps(summ, indent=1) + "\n")


if __name__ == "__main__":
    main()
