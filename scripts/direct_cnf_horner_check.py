#!/usr/bin/env python3
"""Compare complete small-base Horner-CNF solution sets against brute force."""
import json
import time
from pysat.solvers import Solver
from direct_cnf import Circuit
from verify import candidate_intervals, verify


def main():
    rows = []
    started = time.monotonic()
    for base in [2, 4, 5, 8, 9, 10, 12, 13, 14]:
        intervals = candidate_intervals(base)
        assert len(intervals) == 1
        interval = intervals[0]
        lo, hi = interval["lo"], interval["hi"]
        expected = [n for n in range(lo, hi+1) if verify(n, base)["nice"]]
        circuit = Circuit(record=True)
        bits = [circuit.new() for _ in range(hi.bit_length())]
        circuit.interval(bits, lo, hi)
        square = circuit.multiply(bits, bits)
        sq = circuit.horner_digits(square, base, interval["square_digits"])
        cube = circuit.multiply(square, bits)
        cu = circuit.horner_digits(cube, base, interval["cube_digits"])
        circuit.occupancy(sq+cu, base)
        actual = []
        with Solver(name="cadical300", bootstrap_with=circuit.recorded_clauses) as solver:
            while True:
                solver.conf_budget(500000)
                result = solver.solve_limited()
                assert result is not None, (base, "conflict budget exhausted")
                if result is False:
                    break
                model = set(solver.get_model())
                n = sum(1 << i for i, bit in enumerate(bits) if bit in model)
                assert verify(n, base)["nice"], (base, n)
                actual.append(n)
                solver.add_clause([-bit if n >> i & 1 else bit for i, bit in enumerate(bits)])
        assert sorted(actual) == expected, (base, expected, actual)
        rows.append({"base": base, "candidates_checked_by_brute_force": hi-lo+1,
                     "complete_solutions": actual, "variables": circuit.variables,
                     "clauses": circuit.clauses, "status": "matched"})
    print(json.dumps({"status": "passed", "seconds": time.monotonic()-started,
                      "complete_solution_set_checks": rows}, indent=2))


if __name__ == "__main__":
    main()
