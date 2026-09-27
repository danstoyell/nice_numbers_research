#!/usr/bin/env python3
"""Export exact nice-number CNF and run a dedicated SAT solver in isolation.

PYTHONPATH=/private/tmp/nice-z3:/private/tmp/nice-pysat python3 scripts/sat_backend.py \
  --base 10 --output results/sat-backend-base10.json

Workers are monitored for elapsed time and resident memory. CNF stays in /tmp.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True)+"\n")


def append_occupancy(path, base, bit_vars, original_variables, original_clauses):
    """Shared binary decoders; each value must occur in one output digit."""
    width = (base-1).bit_length()
    next_variable = original_variables
    added_clauses = 0
    leaves = [[] for _ in range(base)]
    extra = Path(str(path)+".occupancy")
    with extra.open("w") as handle:
        def emit(clause):
            nonlocal added_clauses
            handle.write(" ".join(map(str, clause))+" 0\n")
            added_clauses += 1
        for digit in range(base):
            nodes = {}
            for value in range(base):
                parent = None
                for depth in range(1, width+1):
                    shift = width-depth
                    prefix = value >> shift
                    key = depth, prefix
                    if key not in nodes:
                        bit = bit_vars[digit, shift]
                        literal = bit if prefix & 1 else -bit
                        if parent is None:
                            nodes[key] = literal
                        else:
                            next_variable += 1
                            nodes[key] = next_variable
                            emit([-next_variable, parent])
                            emit([-next_variable, literal])
                            emit([next_variable, -parent, -literal])
                    parent = nodes[key]
                leaves[value].append(parent)
        for occurrences in leaves:
            emit(occurrences)
    rewritten = Path(str(path)+".new")
    with rewritten.open("w") as output:
        output.write(f"p cnf {next_variable} {original_clauses+added_clauses}\n")
        with open(path) as source:
            for line in source:
                if not line.startswith("p cnf"):
                    output.write(line)
        with extra.open() as source:
            shutil.copyfileobj(source, output)
    rewritten.replace(path)
    extra.unlink()
    return next_variable, original_clauses+added_clauses


def export_cnf(args):
    import z3
    from constraint_search import model
    started = time.monotonic()
    solver, n, config = model(args.base, args.encoding, args.seed, 1000,
                            residue_filter=True,
                            distinct_encoding="pairwise" if args.distinct == "occupancy" else args.distinct)
    if solver is None:
        write_json(args.worker_result, {"status": "excluded", "config": config})
        return
    if args.distinct == "occupancy":
        config["distinct_encoding"] = "occupancy_decoder"
    goal = z3.Goal()
    if args.distinct == "occupancy":
        assertions = list(solver.assertions())
        width = (args.base-1).bit_length()
        ds = ([z3.BitVec(f"s{i}", width) for i in range(config["square_length"])]+
              [z3.BitVec(f"c{i}", width) for i in range(config["cube_length"])])
        names = {str(d) for d in ds}
        def is_output_distinct(a):
            return (z3.is_distinct(a) and a.num_args() == args.base and
                    {str(c) for c in a.children()} == names)
        assert sum(is_output_distinct(a) for a in assertions) == 1
        goal.add(*[a for a in assertions if not is_output_distinct(a)])
        for j, digit in enumerate(ds):
            for i in range(width):
                goal.add(z3.Bool(f"DBIT_{j}_{i}") == (z3.Extract(i, i, digit) == 1))
    else:
        goal.add(*solver.assertions())
    for i in range(n.size()):
        goal.add(z3.Bool(f"NBIT_{i}") == (z3.Extract(i, i, n) == 1))
    write_json(args.worker_result, {"status": "built", "config": config,
                                  "build_seconds": time.monotonic()-started})
    cnf = z3.Then(z3.With("simplify", blast_distinct=True),
                  "bit-blast", "tseitin-cnf")(goal)[0]
    # Otherwise DIMACS can silently abstract residual BV equalities as free
    # Boolean atoms. A satisfiable abstraction would not solve our problem.
    assert z3.Probe("is-propositional")(cnf) == 1
    clause_count = len(cnf)
    write_json(args.worker_result, {"status": "bit_blasted", "config": config,
                                  "clauses": clause_count,
                                  "elapsed_seconds": time.monotonic()-started})
    Path(args.cnf).write_text(cnf.dimacs())
    nbits = {}
    dbits = {}
    variables = None
    with open(args.cnf) as handle:
        for line in handle:
            if line.startswith("p cnf"):
                _, _, variables, stated_clauses = line.split()
                variables = int(variables)
                assert int(stated_clauses) == clause_count
            elif line.startswith("c "):
                parts = line.split()
                if len(parts) == 3 and parts[2].startswith("NBIT_"):
                    nbits[int(parts[2][5:])] = int(parts[1])
                elif len(parts) == 3 and parts[2].startswith("DBIT_"):
                    _, digit, bit = parts[2].split("_")
                    dbits[int(digit), int(bit)] = int(parts[1])
    assert len(nbits) == n.size(), (len(nbits), n.size())
    arithmetic_variables, arithmetic_clauses = variables, clause_count
    if args.distinct == "occupancy":
        assert len(dbits) == args.base*(args.base-1).bit_length()
        variables, clause_count = append_occupancy(args.cnf, args.base, dbits,
                                                   variables, clause_count)
    info = {"status": "exported", "config": config, "clauses": clause_count,
            "variables": variables, "n_bit_variables": nbits,
            "cnf_bytes": Path(args.cnf).stat().st_size,
            "arithmetic_variables": arithmetic_variables,
            "arithmetic_clauses": arithmetic_clauses,
            "elapsed_seconds": time.monotonic()-started}
    write_json(args.worker_result, info)


def solve_cnf(args):
    import pysat
    from pysat.solvers import Solver
    from constraint_search import digits
    metadata = json.loads(Path(args.export_result).read_text())
    started = time.monotonic()
    with Solver(name=args.backend, use_timer=True) as solver:
        if args.backend.startswith("cadical"):
            solver.configure({"seed": args.seed})
        with open(args.cnf) as handle:
            for line in handle:
                if line[0] not in "cp\n":
                    clause = list(map(int, line.split()))
                    assert clause[-1] == 0
                    solver.add_clause(clause[:-1])
        info = {"status": "loaded", "backend": args.backend,
                "backend_seed": args.seed if args.backend.startswith("cadical") else "default",
                "python_sat_version": pysat.__version__,
                "load_seconds": time.monotonic()-started,
                "loaded_variables": solver.nof_vars(),
                "loaded_clauses": solver.nof_clauses() if args.backend.startswith("cadical") else None,
                "conflict_budget": args.conflicts}
        write_json(args.worker_result, info)
        solver.conf_budget(args.conflicts)
        before = time.monotonic()
        answer = solver.solve_limited()
        info |= {"status": "sat" if answer is True else
                           "unsat" if answer is False else "unknown",
                 "solve_seconds": time.monotonic()-before,
                 "statistics": solver.accum_stats() if args.backend.startswith("cadical") else None}
        if answer is None:
            info["reason"] = "conflict_budget"
        if answer is True:
            assignments = set(solver.get_model())
            n = sum(1 << int(i) for i, literal in metadata["n_bit_variables"].items()
                    if literal in assignments)
            sq, cu = digits(n*n, args.base), digits(n*n*n, args.base)
            valid = sorted(sq+cu) == list(range(args.base))
            info |= {"n": str(n), "square_digits": sq, "cube_digits": cu,
                     "independently_valid": valid}
            assert valid, info
        write_json(args.worker_result, info)


def controlled_worker(args, phase):
    work = Path(args.work_dir)
    result_path = work / f"{phase}.json"
    log_path = work / f"{phase}.log"
    command = [sys.executable, str(Path(__file__).resolve()),
               "--phase", phase, "--base", str(args.base),
               "--encoding", args.encoding, "--distinct", args.distinct,
               "--seed", str(args.seed), "--backend", args.backend,
               "--conflicts", str(args.conflicts), "--cnf", args.cnf,
               "--worker-result", str(result_path),
               "--export-result", str(work / "export.json")]
    timeout = args.export_timeout if phase == "export" else args.solve_timeout
    started = time.monotonic()
    peak_rss = 0
    stop_reason = None
    with open(log_path, "w") as logfile:
        worker = subprocess.Popen(command, stdout=logfile, stderr=subprocess.STDOUT)
        while worker.poll() is None:
            if time.monotonic()-started > timeout:
                stop_reason = "wall_timeout"
            try:
                rss = subprocess.run(["ps", "-o", "rss=", "-p", str(worker.pid)],
                                     capture_output=True, text=True).stdout.strip()
            except OSError as error:
                worker.terminate()
                worker.wait(timeout=2)
                raise RuntimeError("Memory monitoring requires permission to run ps") from error
            if rss:
                peak_rss = max(peak_rss, int(rss))
                if int(rss) > args.rss_mb*1024:
                    stop_reason = "rss_limit"
            if stop_reason:
                worker.terminate()
                try:
                    worker.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait()
                break
            time.sleep(0.25)
    record = json.loads(result_path.read_text()) if result_path.exists() else {}
    record |= {"worker_exit_code": worker.returncode,
               "wall_seconds": time.monotonic()-started,
               "observed_peak_rss_mb": peak_rss/1024,
               "wall_limit_seconds": timeout, "rss_limit_mb": args.rss_mb}
    if stop_reason:
        record["last_completed_status"] = record.get("status")
        record["status"] = "unknown"
        record["reason"] = stop_reason
    elif worker.returncode:
        record["status"] = "worker_error"
        record["log_tail"] = log_path.read_text()[-2000:]
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=int, required=True)
    parser.add_argument("--encoding", choices=["bv", "karatsuba"], default="karatsuba")
    parser.add_argument("--distinct", choices=["pairwise", "sort", "occupancy"], default="pairwise")
    parser.add_argument("--backend", choices=["cadical300", "kissat404"], default="cadical300")
    parser.add_argument("--seed", type=int, default=20260924)
    parser.add_argument("--conflicts", type=int, default=100000)
    parser.add_argument("--export-timeout", type=float, default=60)
    parser.add_argument("--solve-timeout", type=float, default=60)
    parser.add_argument("--rss-mb", type=float, default=1536)
    parser.add_argument("--work-dir")
    parser.add_argument("--output")
    parser.add_argument("--phase", choices=["run", "export", "solve"], default="run")
    parser.add_argument("--cnf")
    parser.add_argument("--worker-result")
    parser.add_argument("--export-result")
    parser.add_argument("--reuse-export", help="Prior top-level result JSON with a completed CNF export")
    args = parser.parse_args()
    if args.phase == "export":
        export_cnf(args)
    elif args.phase == "solve":
        solve_cnf(args)
    else:
        if not args.output:
            parser.error("--output is required")
        args.work_dir = args.work_dir or f"/private/tmp/nice-sat-{args.base}-{args.backend}-{os.getpid()}"
        Path(args.work_dir).mkdir(parents=True, exist_ok=True)
        args.cnf = str(Path(args.work_dir)/"instance.cnf")
        record = {"base": args.base, "seed": args.seed, "encoding": args.encoding,
                  "distinct": args.distinct, "backend": args.backend,
                  "cnf_path": args.cnf}
        if args.reuse_export:
            prior = json.loads(Path(args.reuse_export).read_text())
            assert prior["base"] == args.base and prior["export"]["status"] == "exported"
            args.cnf = prior["cnf_path"]
            record["cnf_path"] = args.cnf
            record["export"] = prior["export"] | {"reused_from": args.reuse_export}
            write_json(Path(args.work_dir)/"export.json", record["export"])
        else:
            record["export"] = controlled_worker(args, "export")
        write_json(args.output, record)
        print(json.dumps({"base": args.base, "phase": "export",
                          "status": record["export"]["status"],
                          "clauses": record["export"].get("clauses")}), flush=True)
        if record["export"]["status"] == "exported":
            record["solve"] = controlled_worker(args, "solve")
            write_json(args.output, record)
            print(json.dumps({"base": args.base, "phase": "solve",
                              "status": record["solve"]["status"],
                              "n": record["solve"].get("n")}), flush=True)


if __name__ == "__main__":
    main()
