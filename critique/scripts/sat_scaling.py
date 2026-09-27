#!/usr/bin/env python3
"""Time the project's exact Horner CNF on small bases whose answer is known.

The research tracks ran SAT only at bases 128-512 (no answer known, UNKNOWN at
every budget) and at bases <= 14 (no per-base timing). This measures how
solve time grows with the base where brute force has already settled the
answer, so the two methods can be compared on equal terms.

Reuses scripts/direct_cnf.py's validated Circuit unchanged. Every admissible
base (not 1 mod 5, not 3 mod 4) from 12 upward is attempted in order until
two consecutive bases hit the wall-clock limit. Each base runs in a child
process that is killed at the limit; CPU time is recorded so that any
contention from other jobs would be visible.

Usage:
  PYTHONPATH=/private/tmp/nice-pysat python3 critique/scripts/sat_scaling.py \
      --limit 900 --output critique/results/sat-scaling.json
"""
import argparse
import json
import multiprocessing
import platform
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from pysat.solvers import Solver  # noqa: E402
from direct_cnf import Circuit  # noqa: E402
from verify import candidate_intervals, verify  # noqa: E402


def filtered_count(base, lo, hi):
    """Candidates passing the digit-sum and distinct-last-digit filters."""
    m = base - 1
    target = base * (base - 1) // 2 % m
    sums = [s for s in range(m) if (s * s * (s + 1)) % m == target]
    lasts = [r for r in range(base) if (r * r) % base != (r ** 3) % base]
    modulus = base * m
    total = 0
    for r in lasts:
        for s in sums:
            # CRT: x = r mod b, x = s mod (b-1)
            x = r + base * ((s - r) % m)
            x %= modulus
            first = lo + (x - lo) % modulus
            if first <= hi:
                total += (hi - first) // modulus + 1
    return total


def build(base):
    interval, = candidate_intervals(base)
    lo, hi = interval["lo"], interval["hi"]
    circuit = Circuit(record=True)
    bits = [circuit.new() for _ in range(hi.bit_length())]
    circuit.interval(bits, lo, hi)
    square = circuit.multiply(bits, bits)
    sq = circuit.horner_digits(square, base, interval["square_digits"])
    cube = circuit.multiply(square, bits)
    cu = circuit.horner_digits(cube, base, interval["cube_digits"])
    circuit.occupancy(sq + cu, base)
    return interval, bits, circuit


def worker(base, solver_name, conn):
    """Build and solve in a child process; the parent enforces the wall limit
    (PySAT's CaDiCaL 1.9.5 binding does not implement interrupt()). A Pipe is
    used because Queue's feeder thread cannot flush while the solver holds
    the GIL."""
    interval, bits, circuit = build(base)
    row = {"base": base, "solver": solver_name, "lo": interval["lo"],
           "hi": interval["hi"], "interval_count": interval["count"],
           "filtered_count": filtered_count(base, interval["lo"], interval["hi"]),
           "input_bits": len(bits), "variables": circuit.variables,
           "clauses": circuit.clauses}
    conn.send(("built", row))
    solutions = []
    started, cpu_started = time.monotonic(), time.process_time()
    with Solver(name=solver_name, bootstrap_with=circuit.recorded_clauses) as solver:
        while solver.solve():
            model = set(solver.get_model())
            n = sum(1 << i for i, bit in enumerate(bits) if bit in model)
            assert verify(n, base)["nice"], (base, n)
            solutions.append(n)
            solver.add_clause([-bit if n >> i & 1 else bit
                               for i, bit in enumerate(bits)])
        stats = solver.accum_stats() or {}
    row.update({"result": "UNSAT" if not solutions else "ALL_SOLUTIONS_FOUND",
                "seconds": time.monotonic() - started,
                "cpu_seconds": time.process_time() - cpu_started,
                "solutions": solutions,
                "stats": {k: int(v) for k, v in stats.items()}})
    conn.send(("done", row))


def solve(base, solver_name, limit):
    ctx = multiprocessing.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=worker, args=(base, solver_name, child))
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    proc.start()
    kind, row = parent.recv()        # circuit built; solving starts now
    assert kind == "built"
    started = time.monotonic()
    if parent.poll(limit):
        kind, row = parent.recv()
    else:
        proc.terminate()
        row["result"] = "TIMEOUT"
        row["seconds"] = time.monotonic() - started
    proc.join()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    row["child_cpu_seconds_total"] = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)
    row["limit_seconds"] = limit
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=float, default=900.0, help="seconds per base")
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--max-base", type=int, default=60)
    ap.add_argument("--bases", type=int, nargs="*", help="explicit base list")
    ap.add_argument("--output", default=str(ROOT / "critique/results/sat-scaling.json"))
    args = ap.parse_args()
    bases = args.bases or [10] + [b for b in range(12, args.max_base + 1)
                                  if b % 5 != 1 and b % 4 != 3]
    report = {"purpose": "SAT solve time versus base where the answer is known",
              "encoding": "scripts/direct_cnf.py Circuit, Horner digits, occupancy",
              "solver": args.solver, "limit_seconds": args.limit,
              "machine": platform.platform(), "python": platform.python_version(),
              "rows": []}
    consecutive_timeouts = 0
    for base in bases:
        row = solve(base, args.solver, args.limit)
        report["rows"].append(row)
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: row[k] for k in ("base", "result", "seconds",
                                               "interval_count", "filtered_count",
                                               "variables", "clauses")}), flush=True)
        consecutive_timeouts = consecutive_timeouts + 1 if row["result"] == "TIMEOUT" else 0
        if consecutive_timeouts >= 2:
            break


if __name__ == "__main__":
    main()
