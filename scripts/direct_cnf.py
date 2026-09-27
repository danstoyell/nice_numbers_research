#!/usr/bin/env python3
"""Stream an exact nice-number Boolean circuit to CNF without Z3 ASTs.

Use --validate for exhaustive small arithmetic/decoder checks.
Use --base B --output results/direct-cnf-B.json for a monitored export.
The resulting JSON can be passed to sat_backend.py --reuse-export.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

TRUE, FALSE = 1, -1


class Circuit:
    def __init__(self, path=None, record=False):
        self.variables = 1
        self.clauses = 0
        self.handle = open(path, "w", buffering=1 << 20) if path else None
        self.gates = [] if record else None
        self.recorded_clauses = [] if record else None
        self.clause([TRUE])

    def new(self):
        self.variables += 1
        return self.variables

    def clause(self, literals):
        # Unit literal 1 defines our constant. Elsewhere simplify constants.
        if self.clauses == 0 and literals == [TRUE]:
            clause = [TRUE]
        else:
            if TRUE in literals:
                return
            clause = list(dict.fromkeys(x for x in literals if x != FALSE))
            if any(-x in clause for x in clause):
                return
        self.clauses += 1
        if self.handle:
            self.handle.write(" ".join(map(str, clause))+" 0\n")
        if self.recorded_clauses is not None:
            self.recorded_clauses.append(clause)

    def record(self, op, output, *args):
        if self.gates is not None:
            self.gates.append((op, output, args))

    def and_(self, a, b):
        if FALSE in (a, b) or a == -b:
            return FALSE
        if a == TRUE or a == b:
            return b
        if b == TRUE:
            return a
        out = self.new()
        self.clause([-out, a]); self.clause([-out, b]); self.clause([out, -a, -b])
        self.record("and", out, a, b)
        return out

    def xor(self, a, b):
        if a == b:
            return FALSE
        if a == -b:
            return TRUE
        if a == FALSE:
            return b
        if b == FALSE:
            return a
        if a == TRUE:
            return -b
        if b == TRUE:
            return -a
        out = self.new()
        self.clause([-a, -b, -out]); self.clause([a, b, -out])
        self.clause([a, -b, out]); self.clause([-a, b, out])
        self.record("xor", out, a, b)
        return out

    def majority(self, a, b, c):
        if a == b or a == c:
            return a
        if b == c:
            return b
        if a == -b:
            return c
        if a == -c:
            return b
        if b == -c:
            return a
        if a == FALSE:
            return self.and_(b, c)
        if b == FALSE:
            return self.and_(a, c)
        if c == FALSE:
            return self.and_(a, b)
        if a == TRUE:
            return -self.and_(-b, -c)
        if b == TRUE:
            return -self.and_(-a, -c)
        if c == TRUE:
            return -self.and_(-a, -b)
        out = self.new()
        for x, y in [(a, b), (a, c), (b, c)]:
            self.clause([-x, -y, out]); self.clause([x, y, -out])
        self.record("majority", out, a, b, c)
        return out

    def mux(self, selector, yes, no):
        if yes == no:
            return yes
        if selector == TRUE:
            return yes
        if selector == FALSE:
            return no
        # no XOR (selector AND (yes XOR no))
        return self.xor(no, self.and_(selector, self.xor(yes, no)))

    def full_add(self, a, b, carry):
        return self.xor(self.xor(a, b), carry), self.majority(a, b, carry)

    def add(self, a, b, width=None):
        width = width if width is not None else max(len(a), len(b))+1
        result, carry = [], FALSE
        for i in range(width):
            digit, carry = self.full_add(at(a, i), at(b, i), carry)
            result.append(digit)
        return trim(result)

    def subtract(self, a, b, width=None):
        width = width if width is not None else max(len(a), len(b))
        result, borrow = [], FALSE
        for i in range(width):
            ai, bi = at(a, i), at(b, i)
            result.append(self.xor(self.xor(ai, bi), borrow))
            borrow = self.majority(-ai, bi, borrow)
        return trim(result), borrow

    def leaf_product(self, a, b):
        if not a or not b:
            return []
        width = len(a)+len(b)
        columns = [[] for _ in range(width)]
        if a == b:
            for i, ai in enumerate(a):
                columns[2*i].append(ai)
                for j in range(i+1, len(a)):
                    term = self.and_(ai, a[j])
                    if term != FALSE:
                        columns[i+j+1].append(term)
        else:
            for i, ai in enumerate(a):
                for j, bj in enumerate(b):
                    term = self.and_(ai, bj)
                    if term != FALSE:
                        columns[i+j].append(term)
        for i in range(width):
            while len(columns[i]) > 2:
                a0, a1, a2 = [columns[i].pop() for _ in range(3)]
                digit, carry = self.full_add(a0, a1, a2)
                columns[i].append(digit)
                if carry != FALSE and i+1 < width:
                    columns[i+1].append(carry)
        first = [c[0] if c else FALSE for c in columns]
        second = [c[1] if len(c) > 1 else FALSE for c in columns]
        return self.add(first, second, width)

    def multiply(self, a, b, leaf_bits=16):
        a, b = trim(a), trim(b)
        if not a or not b:
            return []
        wanted = len(a)+len(b)
        if max(len(a), len(b)) <= leaf_bits:
            return self.leaf_product(a, b)
        if max(len(a), len(b)) >= 2*min(len(a), len(b)):
            if len(a) < len(b):
                a, b = b, a
            split = len(a)//2
            low = self.multiply(a[:split], b, leaf_bits)
            high = self.multiply(a[split:], b, leaf_bits)
            return self.add(low, [FALSE]*split+high, wanted)
        width = max(len(a), len(b))
        split = width//2
        al, ah, bl, bh = a[:split], a[split:], b[:split], b[split:]
        low = self.multiply(al, bl, leaf_bits)
        high = self.multiply(ah, bh, leaf_bits)
        sa, sb = self.add(al, ah), self.add(bl, bh)
        middle = self.multiply(sa, sb, leaf_bits)
        middle, _ = self.subtract(middle, low)
        middle, _ = self.subtract(middle, high)
        result = self.add(low, [FALSE]*split+middle, wanted)
        return self.add(result, [FALSE]*(2*split)+high, wanted)

    def interval(self, bits, lower, upper):
        for bound, is_upper in [(lower, False), (upper, True)]:
            prefix = TRUE
            for i in reversed(range(len(bits))):
                one = bool(bound >> i & 1)
                if is_upper and not one:
                    self.clause([-prefix, -bits[i]])
                if not is_upper and one:
                    self.clause([-prefix, bits[i]])
                prefix = self.and_(prefix, bits[i] if one else -bits[i])

    def divmod_constant(self, bits, base):
        width = (base-1).bit_length()
        if base & (base-1) == 0:
            return trim(bits[width:]), fit(bits[:width], width)
        remainder = [FALSE]*width
        quotient = []
        constant = constant_bits(base, width+1)
        for bit in reversed(bits):
            shifted = [bit]+remainder
            difference, borrow = self.subtract(shifted, constant, width+1)
            quotient.append(-borrow)
            remainder = [self.mux(-borrow, at(difference, i), shifted[i])
                         for i in range(width)]
        return trim(list(reversed(quotient))), remainder

    def base_digits(self, bits, base, length):
        result = []
        for _ in range(length):
            bits, digit = self.divmod_constant(bits, base)
            result.append(digit)
        for remaining in bits:
            self.clause([-remaining])
        self.clause(result[-1])
        return result

    def multiply_constant(self, bits, constant):
        result = []
        for shift in range(constant.bit_length()):
            if constant >> shift & 1:
                result = self.add(result, [FALSE]*shift+bits)
        return result

    def pack_digits(self, digits, base):
        """Exact Horner value of bounded digits, least-significant digit first."""
        accumulator = []
        maximum = 0
        for digit in reversed(digits):
            accumulator = self.add(self.multiply_constant(accumulator, base), digit)
            maximum = maximum*base+base-1
            width = maximum.bit_length()
            for excess in accumulator[width:]:
                self.clause([-excess])
            accumulator = fit(accumulator, width)
        return trim(accumulator)

    def horner_digits(self, bits, base, length):
        width = (base-1).bit_length()
        digits = [[self.new() for _ in range(width)] for _ in range(length)]
        for digit in digits:
            self.interval(digit, 0, base-1)
        self.clause(digits[-1])
        packed = self.pack_digits(digits, base)
        for i in range(max(len(bits), len(packed))):
            a, b = at(bits, i), at(packed, i)
            self.clause([-a, b]); self.clause([a, -b])
        return digits

    def occupancy(self, digits, base):
        width = (base-1).bit_length()
        leaves = [[] for _ in range(base)]
        for digit in digits:
            nodes = {}
            for value in range(base):
                parent = TRUE
                for depth in range(1, width+1):
                    shift = width-depth
                    prefix = value >> shift
                    key = depth, prefix
                    if key not in nodes:
                        bit = at(digit, shift)
                        nodes[key] = self.and_(parent, bit if prefix & 1 else -bit)
                    parent = nodes[key]
                leaves[value].append(parent)
        for occurrences in leaves:
            self.clause(occurrences)

    def close(self):
        if self.handle:
            self.handle.close()


def at(bits, index):
    return bits[index] if index < len(bits) else FALSE


def fit(bits, width):
    return bits[:width]+[FALSE]*max(0, width-len(bits))


def trim(bits):
    end = len(bits)
    while end and bits[end-1] == FALSE:
        end -= 1
    return bits[:end]


def constant_bits(value, width):
    return [TRUE if value >> i & 1 else FALSE for i in range(width)]


def evaluate(circuit, inputs):
    values = [False]*(circuit.variables+1)
    values[1] = True
    for literal, value in inputs.items():
        values[literal] = bool(value)
    def truth(literal):
        return values[literal] if literal > 0 else not values[-literal]
    for op, out, args in circuit.gates:
        a = truth(args[0]); b = truth(args[1])
        values[out] = (a and b if op == "and" else a != b if op == "xor"
                       else sum([a, b, truth(args[2])]) >= 2)
    valid = all(any(truth(lit) for lit in clause) for clause in circuit.recorded_clauses)
    return truth, valid


def validate():
    import itertools
    import random
    started = time.monotonic()
    gate_checks = 0
    for operation, arity in [("and", 2), ("xor", 2), ("majority", 3)]:
        circuit = Circuit(record=True)
        inputs = [circuit.new() for _ in range(arity)]
        output = (circuit.and_(*inputs) if operation == "and" else
                  circuit.xor(*inputs) if operation == "xor" else circuit.majority(*inputs))
        for bits in itertools.product([False, True], repeat=arity+1):
            assignment = {TRUE: True, **dict(zip(inputs+[output], bits))}
            def truth(lit):
                return assignment[lit] if lit > 0 else not assignment[-lit]
            valid = all(any(truth(lit) for lit in clause) for clause in circuit.recorded_clauses)
            expected = (all(bits[:-1]) if operation == "and" else
                        bits[0] != bits[1] if operation == "xor" else sum(bits[:-1]) >= 2)
            assert valid == (bits[-1] == expected)
            gate_checks += 1
    product_checks = 0
    for aw, bw in [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6),
                   (1, 3), (2, 5), (3, 6)]:
        circuit = Circuit(record=True)
        a = [circuit.new() for _ in range(aw)]
        b = [circuit.new() for _ in range(bw)]
        product = circuit.multiply(a, b, leaf_bits=3)
        for av in range(1 << aw):
            for bv in range(1 << bw):
                inputs = {bit: av >> i & 1 for i, bit in enumerate(a)}
                inputs.update({bit: bv >> i & 1 for i, bit in enumerate(b)})
                truth, valid = evaluate(circuit, inputs)
                answer = sum(1 << i for i, bit in enumerate(product) if truth(bit))
                assert valid and answer == av*bv, (aw, bw, av, bv, answer)
                product_checks += 1
    square_checks = 0
    for width in range(1, 9):
        circuit = Circuit(record=True)
        bits = [circuit.new() for _ in range(width)]
        square = circuit.multiply(bits, bits, leaf_bits=3)
        for value in range(1 << width):
            truth, valid = evaluate(circuit, {bit: value >> i & 1 for i, bit in enumerate(bits)})
            answer = sum(1 << i for i, bit in enumerate(square) if truth(bit))
            assert valid and answer == value*value, (width, value, answer)
            square_checks += 1
    random_checks = 0
    rng = random.Random(20260925)
    for aw, bw in [(16, 16), (17, 17), (31, 32), (64, 65), (179, 179)]:
        circuit = Circuit(record=True)
        a = [circuit.new() for _ in range(aw)]
        b = [circuit.new() for _ in range(bw)]
        product = circuit.multiply(a, b, leaf_bits=16)
        for _ in range(10):
            av, bv = rng.getrandbits(aw), rng.getrandbits(bw)
            inputs = {bit: av >> i & 1 for i, bit in enumerate(a)}
            inputs.update({bit: bv >> i & 1 for i, bit in enumerate(b)})
            truth, valid = evaluate(circuit, inputs)
            answer = sum(1 << i for i, bit in enumerate(product) if truth(bit))
            assert valid and answer == av*bv, (aw, bw, av, bv, answer)
            random_checks += 1
    division_checks = 0
    for base in [2, 3, 5, 8, 10, 13]:
        circuit = Circuit(record=True)
        bits = [circuit.new() for _ in range(8)]
        quotient, remainder = circuit.divmod_constant(bits, base)
        for value in range(256):
            truth, valid = evaluate(circuit, {bit: value >> i & 1 for i, bit in enumerate(bits)})
            q = sum(1 << i for i, bit in enumerate(quotient) if truth(bit))
            r = sum(1 << i for i, bit in enumerate(remainder) if truth(bit))
            assert valid and (q, r) == divmod(value, base), (base, value, q, r)
            division_checks += 1
    decoder_checks = 0
    for base in [2, 3, 4]:
        for values in itertools.product(range(base), repeat=base):
            circuit = Circuit(record=True)
            ds = [constant_bits(v, (base-1).bit_length()) for v in values]
            circuit.occupancy(ds, base)
            _, valid = evaluate(circuit, {})
            assert valid == (sorted(values) == list(range(base)))
            decoder_checks += 1
    packing_checks = 0
    for base, length in [(2, 4), (3, 3), (4, 3), (5, 3), (10, 2)]:
        circuit = Circuit(record=True)
        ds = [[circuit.new() for _ in range((base-1).bit_length())] for _ in range(length)]
        for digit in ds:
            circuit.interval(digit, 0, base-1)
        packed = circuit.pack_digits(ds, base)
        for values in itertools.product(range(base), repeat=length):
            inputs = {bit: value >> i & 1 for digit, value in zip(ds, values)
                      for i, bit in enumerate(digit)}
            truth, valid = evaluate(circuit, inputs)
            answer = sum(1 << i for i, bit in enumerate(packed) if truth(bit))
            assert valid and answer == sum(v*base**i for i, v in enumerate(values))
            packing_checks += 1
    circuit = Circuit(record=True)
    bits = [circuit.new() for _ in range(5)]
    circuit.interval(bits, 3, 21)
    for value in range(32):
        _, valid = evaluate(circuit, {bit: value >> i & 1 for i, bit in enumerate(bits)})
        assert valid == (3 <= value <= 21)
    return {"status": "passed", "gate_truth_table_assignments": gate_checks,
            "product_assignments": product_checks, "large_random_products": random_checks,
            "square_assignments": square_checks, "division_assignments": division_checks,
            "decoder_assignments": decoder_checks, "horner_packing_assignments": packing_checks,
            "interval_assignments": 32,
            "seconds": time.monotonic()-started}


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True)+"\n")


def export(args):
    from constraint_search import bounds
    started = time.monotonic()
    lengths = bounds(args.base)
    assert lengths is not None
    square_length, cube_length, lower, upper = lengths
    assert lower <= upper
    body = Path(args.cnf+".body")
    circuit = Circuit(body)
    nbits = [circuit.new() for _ in range(upper.bit_length())]
    circuit.interval(nbits, lower, upper)
    square = circuit.multiply(nbits, nbits, args.leaf_bits)
    make_digits = circuit.horner_digits if args.digit_encoding == "horner" else circuit.base_digits
    sq = make_digits(square, args.base, square_length)
    write_json(args.worker_result, {"status": "square_built", "variables": circuit.variables,
                                    "clauses": circuit.clauses})
    cube = circuit.multiply(square, nbits, args.leaf_bits)
    cu = make_digits(cube, args.base, cube_length)
    arithmetic_variables, arithmetic_clauses = circuit.variables, circuit.clauses
    write_json(args.worker_result, {"status": "arithmetic_built", "variables": circuit.variables,
                                    "clauses": circuit.clauses})
    circuit.occupancy(sq+cu, args.base)
    circuit.close()
    with open(args.cnf, "w") as target:
        target.write(f"p cnf {circuit.variables} {circuit.clauses}\n")
        with body.open() as source:
            shutil.copyfileobj(source, target, length=1 << 20)
    body.unlink()
    info = {"status": "exported", "variables": circuit.variables, "clauses": circuit.clauses,
            "arithmetic_variables": arithmetic_variables, "arithmetic_clauses": arithmetic_clauses,
            "n_bit_variables": dict(enumerate(nbits)), "elapsed_seconds": time.monotonic()-started,
            "cnf_bytes": Path(args.cnf).stat().st_size, "lower": str(lower), "upper": str(upper),
            "square_length": square_length, "cube_length": cube_length,
            "n_width": len(nbits), "square_width": len(square), "cube_width": len(cube),
            "leaf_bits": args.leaf_bits, "residue_filter": False}
    info["digit_encoding"] = args.digit_encoding
    write_json(args.worker_result, info)


def monitored_export(args):
    work = Path(args.work_dir or f"/private/tmp/nice-direct-{args.base}-{os.getpid()}")
    work.mkdir(parents=True, exist_ok=True)
    worker_result = work/"export.json"
    cnf = work/"instance.cnf"
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--base", str(args.base),
               "--leaf-bits", str(args.leaf_bits), "--cnf", str(cnf),
               "--digit-encoding", args.digit_encoding,
               "--worker-result", str(worker_result)]
    started = time.monotonic()
    peak_rss = 0
    stop_reason = None
    with (work/"export.log").open("w") as logfile:
        process = subprocess.Popen(command, stdout=logfile, stderr=subprocess.STDOUT)
        while process.poll() is None:
            try:
                rss = subprocess.run(["ps", "-o", "rss=", "-p", str(process.pid)],
                                     capture_output=True, text=True).stdout.strip()
            except OSError:
                process.terminate(); process.wait(timeout=2)
                raise
            if rss:
                peak_rss = max(peak_rss, int(rss))
                if int(rss) > args.rss_mb*1024:
                    stop_reason = "rss_limit"
            if time.monotonic()-started > args.timeout:
                stop_reason = "wall_timeout"
            if stop_reason:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
                break
            time.sleep(0.25)
    info = json.loads(worker_result.read_text()) if worker_result.exists() else {}
    info |= {"worker_exit_code": process.returncode, "observed_peak_rss_mb": peak_rss/1024,
             "wall_seconds": time.monotonic()-started, "rss_limit_mb": args.rss_mb,
             "wall_limit_seconds": args.timeout}
    if stop_reason:
        info["last_completed_status"] = info.get("status")
        info["status"], info["reason"] = "unknown", stop_reason
    elif process.returncode:
        info["status"] = "worker_error"
        info["log_tail"] = (work/"export.log").read_text()[-3000:]
    result = {"base": args.base, "encoding": "direct_streamed_karatsuba",
              "distinct": "occupancy", "digit_encoding": args.digit_encoding,
              "cnf_path": str(cnf), "export": info}
    write_json(args.output, result)
    print(json.dumps({k:v for k,v in result.items() if k != "export"} | {
        "export_status": info.get("status"), "variables": info.get("variables"),
        "clauses": info.get("clauses"), "observed_peak_rss_mb": peak_rss/1024}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--base", type=int)
    parser.add_argument("--leaf-bits", type=int, default=16)
    parser.add_argument("--digit-encoding", choices=["division", "horner"], default="division")
    parser.add_argument("--output")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--rss-mb", type=float, default=1536)
    parser.add_argument("--work-dir")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--cnf")
    parser.add_argument("--worker-result")
    args = parser.parse_args()
    if args.leaf_bits < 3:
        parser.error("--leaf-bits must be at least3")
    if args.validate:
        result = validate()
        if args.output:
            write_json(args.output, result)
        print(json.dumps(result), flush=True)
    elif args.worker:
        export(args)
    elif args.base and args.output:
        monitored_export(args)
    else:
        parser.error("Use --validate or both --base and --output")


if __name__ == "__main__":
    main()
