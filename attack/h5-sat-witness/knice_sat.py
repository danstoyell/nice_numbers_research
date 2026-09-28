#!/usr/bin/env python3
"""H5: time to the FIRST verified witness with a SAT solver on unplanted K-nice instances.

Reuses scripts/direct_cnf.py's validated Circuit (exact interval, Karatsuba products,
Horner digit extraction, occupancy decoder) with the one change multiplicity K needs:
"each digit value occurs at least K times" is a cardinality constraint (sequential
counter from PySAT) instead of a single clause. Since the interval fixes the total
length K*b, "at least K" is "exactly K".

Nothing about the known roots enters the solver input. Each instance is solved several
times under random variable renamings and clause shufflings (the solver has no seed
option in this binding); the first model is decoded to n and re-verified exactly.
Each solve runs in a child process killed at the wall limit.

Usage: python3 knice_sat.py --cases 3:9 3:10 2:14 2:15 --variants 3 --limit 600
"""
import argparse, json, multiprocessing, os, random, resource, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "critique/scripts"))
from direct_cnf import Circuit, TRUE, FALSE, at  # noqa: E402
from twice_nice import intervals_total_length, is_k_nice  # noqa: E402
from pysat.card import CardEnc, EncType  # noqa: E402
from pysat.solvers import Solver, SolverNames  # noqa: E402


def occupancy_k(circuit, digits, base, K):
    width = (base - 1).bit_length()
    leaves = [[] for _ in range(base)]
    for digit in digits:
        nodes = {}
        for value in range(base):
            parent = TRUE
            for depth in range(1, width + 1):
                shift = width - depth
                prefix = value >> shift
                key = (depth, prefix)
                if key not in nodes:
                    bit = at(digit, shift)
                    nodes[key] = circuit.and_(parent, bit if prefix & 1 else -bit)
                parent = nodes[key]
            leaves[value].append(parent)
    extra = []
    for occurrences in leaves:
        bound = K - sum(1 for l in occurrences if l == TRUE)
        lits = [l for l in occurrences if l not in (TRUE, FALSE)]
        if bound <= 0:
            continue
        if bound == 1:
            circuit.clause(lits); continue
        enc = CardEnc.atleast(lits=lits, bound=bound, top_id=circuit.variables, encoding=EncType.seqcounter)
        circuit.variables = max(circuit.variables, enc.nv)
        extra.extend(enc.clauses)
    return extra


def build(base, K):
    (lo, hi, s, c), = intervals_total_length(base, K * base)
    circuit = Circuit(record=True)
    bits = [circuit.new() for _ in range(hi.bit_length())]
    circuit.interval(bits, lo, hi)
    square = circuit.multiply(bits, bits)
    sq = circuit.horner_digits(square, base, s)
    cube = circuit.multiply(square, bits)
    cu = circuit.horner_digits(cube, base, c)
    extra = occupancy_k(circuit, sq + cu, base, K)
    clauses = circuit.recorded_clauses + extra
    return (lo, hi, s, c), bits, circuit.variables, clauses


def permute(clauses, bits, nvars, rng):
    perm = list(range(2, nvars + 1)); rng.shuffle(perm)
    mp = [0, 1] + perm            # variable v -> mp[v]; keep the constant variable 1
    out = [[(mp[l] if l > 0 else -mp[-l]) for l in cl] for cl in clauses]
    rng.shuffle(out)
    return out, [mp[v] for v in bits]


def worker(base, K, variant, solver_name, conn):
    t0 = time.monotonic()
    (lo, hi, s, c), bits, nvars, clauses = build(base, K)
    rng = random.Random(1000 * base + variant)
    if variant:
        clauses, bits = permute(clauses, bits, nvars, rng)
    built = time.monotonic() - t0
    conn.send(("built", {"variables": nvars, "clauses": len(clauses), "build_seconds": built}))
    t1 = time.monotonic(); c0 = time.process_time()
    with Solver(name=solver_name, bootstrap_with=clauses) as solver:
        ok = solver.solve()
        model = set(solver.get_model()) if ok else set()
        stats = solver.accum_stats() or {}
    n = sum(1 << i for i, bit in enumerate(bits) if bit in model) if ok else None
    conn.send(("done", {"sat": ok, "witness": str(n) if n is not None else None,
                        "verified": bool(n is not None and lo <= n <= hi and is_k_nice(n, base, K)),
                        "solve_seconds": time.monotonic() - t1, "cpu_seconds": time.process_time() - c0,
                        "stats": {k: int(v) for k, v in stats.items()}}))


def run(base, K, variant, solver_name, limit):
    ctx = multiprocessing.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=worker, args=(base, K, variant, solver_name, child))
    proc.start()
    row = {"base": base, "K": K, "variant": variant, "solver": solver_name, "limit_seconds": limit}
    if parent.poll(limit):
        kind, info = parent.recv(); row.update(info)
        t = time.monotonic()
        if parent.poll(max(1.0, limit - info.get("build_seconds", 0))):
            kind, info = parent.recv(); row.update(info); row["result"] = "SAT" if info["sat"] else "UNSAT"
        else:
            proc.terminate(); row["result"] = "TIMEOUT"; row["solve_seconds"] = time.monotonic() - t
    else:
        proc.terminate(); row["result"] = "BUILD_TIMEOUT"
    proc.join()
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", nargs="+", default=["3:9", "3:10", "2:14"], help="K:base")
    ap.add_argument("--variants", type=int, default=3)
    ap.add_argument("--limit", type=float, default=600.0)
    ap.add_argument("--solver", default="cadical195" if "cadical195" in dir(SolverNames) else "cadical153")
    ap.add_argument("--output", default=str(ROOT / "attack/h5-sat-witness/results/knice_sat.jsonl"))
    args = ap.parse_args()
    with open(args.output, "a") as out:
        for case in args.cases:
            K, base = map(int, case.split(":"))
            for v in range(args.variants):
                row = run(base, K, v, args.solver, args.limit)
                out.write(json.dumps(row) + "\n"); out.flush()
                print(json.dumps({k: row.get(k) for k in ("base", "K", "variant", "result", "variables", "clauses", "build_seconds", "solve_seconds", "witness", "verified")}), flush=True)


if __name__ == "__main__":
    main()
