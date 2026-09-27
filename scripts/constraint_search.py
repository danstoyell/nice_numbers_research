#!/usr/bin/env python3
"""Bounded Z3 experiments for the square/cube pandigital problem.

Install locally, e.g. python3 -m pip install --target /private/tmp/nice-z3 z3-solver
and run with PYTHONPATH=/private/tmp/nice-z3. All arithmetic is exact.
"""
import argparse
import json
import random
import time


def floor_root(n, exponent):
    lo, hi = 0, 1 << ((n.bit_length() + exponent - 1) // exponent)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid ** exponent <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


def bounds(base):
    if base < 2 or base % 5 == 1:
        return None
    k, case = divmod(base - 2, 5)
    square_len = 2 * k + 1 + (case >= 2)
    cube_len = 3 * k + 1 + (case >= 1) + (case >= 3)
    def ceil_root(n, e):
        return floor_root(n - 1, e) + 1
    lower = max(ceil_root(base ** (square_len - 1), 2),
                ceil_root(base ** (cube_len - 1), 3))
    upper = min(floor_root(base ** square_len - 1, 2),
                floor_root(base ** cube_len - 1, 3))
    return square_len, cube_len, lower, upper


def digits(n, base):
    answer = []
    while n:
        n, d = divmod(n, base)
        answer.append(d)
    return list(reversed(answer or [0]))


def karatsuba_product(left, right, leaf_bits=16):
    """Exact unsigned BV product, with a fully explicit Karatsuba circuit."""
    import z3
    cache = {}
    # Retain input ASTs: get_id() values may be reused after an AST is freed.
    kept_inputs = []
    def fit(x, width):
        return (z3.ZeroExt(width-x.size(), x) if x.size() <= width
                else z3.Extract(width-1, 0, x))
    def product(a, b):
        a, b = z3.simplify(a), z3.simplify(b)
        wanted = a.size()+b.size()
        key = tuple(sorted((a.get_id(), b.get_id())))
        if key in cache:
            return cache[key]
        kept_inputs.append((a, b))
        if (z3.is_bv_value(a) and a.as_long() == 0 or
                z3.is_bv_value(b) and b.as_long() == 0):
            answer = z3.BitVecVal(0, wanted)
        elif max(a.size(), b.size()) <= leaf_bits:
            answer = fit(a, wanted)*fit(b, wanted)
        elif max(a.size(), b.size()) >= 2*min(a.size(), b.size()):
            if a.size() < b.size():
                a, b = b, a
            split = a.size()//2
            low = z3.Extract(split-1, 0, a)
            high = z3.Extract(a.size()-1, split, a)
            answer = fit(product(low, b), wanted)+(fit(product(high, b), wanted) << split)
        else:
            width = max(a.size(), b.size())
            a, b = fit(a, width), fit(b, width)
            split = width//2
            hi_width = width-split
            al, bl = z3.Extract(split-1, 0, a), z3.Extract(split-1, 0, b)
            ah = z3.Extract(width-1, split, a)
            bh = z3.Extract(width-1, split, b)
            z0, z2 = product(al, bl), product(ah, bh)
            sa = fit(al, hi_width+1)+fit(ah, hi_width+1)
            sb = fit(bl, hi_width+1)+fit(bh, hi_width+1)
            cross_width = 2*(hi_width+1)
            cross = product(sa, sb)-fit(z0, cross_width)-fit(z2, cross_width)
            answer = (fit(z0, 2*width) + (fit(cross, 2*width) << split)
                      + (fit(z2, 2*width) << (2*split)))
            answer = fit(answer, wanted)
        cache[key] = answer
        return answer
    return product(left, right)


def sorted_digit_constraints(ds, base):
    """Bitonic network: output digits must sort to the exact range 0..b-1."""
    import z3
    size = 1 << (len(ds)-1).bit_length()
    width = ds[0].size()
    items = list(ds)
    if size > len(ds):
        assert base < 1 << width
        items += [z3.BitVecVal(base, width)] * (size-len(ds))
    span = 2
    while span <= size:
        gap = span//2
        while gap:
            for i in range(size):
                j = i ^ gap
                if j > i:
                    a, b = items[i], items[j]
                    ascending = i & span == 0
                    condition = z3.ULE(a, b)
                    small, large = z3.If(condition, a, b), z3.If(condition, b, a)
                    items[i], items[j] = (small, large) if ascending else (large, small)
            gap //= 2
        span *= 2
    return [d == min(i, base) for i, d in enumerate(items)]


def model(base, encoding, seed, timeout_ms, pin_n_digits=0, residue_filter=True,
          sat_search="cdcl", memory_mb=1024, distinct_encoding="pairwise",
          leaf_bits=16):
    import z3
    limits = bounds(base)
    if limits is None:
        return None, None, {"result": "excluded_digit_count"}
    sq_len, cu_len, lower, upper = limits
    info = {"base": base, "encoding": encoding, "seed": seed,
            "timeout_ms": timeout_ms, "square_length": sq_len,
            "cube_length": cu_len, "lower": str(lower), "upper": str(upper),
            "pin_n_digits": pin_n_digits, "z3_version": z3.get_version_string()}
    info |= {"residue_filter": residue_filter, "sat_search": sat_search,
             "memory_limit_mb": memory_mb, "distinct_encoding": distinct_encoding,
             "karatsuba_leaf_bits": leaf_bits if encoding == "karatsuba" else None}
    if lower > upper:
        return None, None, info | {"result": "empty_length_interval"}
    solver = z3.Solver()
    solver.set(timeout=timeout_ms, random_seed=seed)
    solver.set(max_memory=memory_mb)
    z3.set_param("sat.local_search", sat_search == "local")
    permitted = [r for r in range(base - 1)
                 if (r*r + r*r*r - base*(base-1)//2) % (base-1) == 0]
    info["digit_sum_residue_count"] = len(permitted)
    if encoding == "int":
        n = z3.Int("n")
        sq = [z3.Int(f"s{i}") for i in range(sq_len)]
        cu = [z3.Int(f"c{i}") for i in range(cu_len)]
        all_digits = sq + cu
        solver.add(n >= lower, n <= upper)
        solver.add([z3.And(d >= 0, d < base) for d in all_digits])
        solver.add(sq[-1] != 0, cu[-1] != 0, z3.Distinct(all_digits))
        solver.add(z3.Sum([d * base**i for i, d in enumerate(sq)]) == n*n)
        solver.add(z3.Sum([d * base**i for i, d in enumerate(cu)]) == n*n*n)
        if residue_filter:
            solver.add(z3.Or([n % (base-1) == r for r in permitted]))
        if pin_n_digits:
            modulus = base ** pin_n_digits
            residue = random.Random(seed).randrange(lower, upper+1) % modulus
            solver.add(n % modulus == residue)
            info["pinned_n_residue"] = str(residue)
    elif encoding == "carry":
        n_len = len(digits(upper, base))
        nd = [z3.Int(f"a{i}") for i in range(n_len)]
        sq = [z3.Int(f"s{i}") for i in range(sq_len)]
        cu = [z3.Int(f"c{i}") for i in range(cu_len)]
        sc = [z3.Int(f"u{i}") for i in range(sq_len+1)]
        cc = [z3.Int(f"v{i}") for i in range(cu_len+1)]
        n = z3.Sum([d*base**i for i,d in enumerate(nd)])
        solver.add(n >= lower, n <= upper)
        solver.add([z3.And(d >= 0, d < base) for d in nd+sq+cu])
        solver.add([z3.And(c >= 0, c <= n_len*(base-1)) for c in sc+cc])
        solver.add(nd[-1] != 0, sq[-1] != 0, cu[-1] != 0,
                   z3.Distinct(sq+cu))
        solver.add(sc[0] == 0, sc[-1] == 0, cc[0] == 0, cc[-1] == 0)
        for k in range(sq_len):
            terms = [(1 if i == k-i else 2)*nd[i]*nd[k-i]
                     for i in range(n_len) if i <= k-i < n_len]
            solver.add(z3.Sum(terms)+sc[k] == sq[k]+base*sc[k+1])
        for k in range(cu_len):
            terms = [nd[i]*sq[k-i] for i in range(n_len)
                     if 0 <= k-i < sq_len]
            solver.add(z3.Sum(terms)+cc[k] == cu[k]+base*cc[k+1])
        if residue_filter:
            residue = z3.Sum(nd) % (base-1)
            solver.add(z3.Or([residue == r for r in permitted]))
        info["carry_count"] = len(sc)+len(cc)
        info["carry_maximum"] = n_len*(base-1)
        if pin_n_digits:
            modulus = base ** pin_n_digits
            residue = random.Random(seed).randrange(lower, upper+1) % modulus
            solver.add(n % modulus == residue)
            info["pinned_n_residue"] = str(residue)
    elif encoding in ["bv", "karatsuba"]:
        nw = max(1, upper.bit_length())
        sw = (base**sq_len - 1).bit_length()
        cw = (base**cu_len - 1).bit_length()
        dw = (base-1).bit_length()
        n = z3.BitVec("n", nw)
        sq = [z3.BitVec(f"s{i}", dw) for i in range(sq_len)]
        cu = [z3.BitVec(f"c{i}", dw) for i in range(cu_len)]
        all_digits = sq + cu
        solver.add(z3.UGE(n, lower), z3.ULE(n, upper))
        if base < 1 << dw:
            solver.add([z3.ULT(d, base) for d in all_digits])
        solver.add(sq[-1] != 0, cu[-1] != 0)
        if distinct_encoding == "sort":
            solver.add(sorted_digit_constraints(all_digits, base))
        else:
            solver.add(z3.Distinct(all_digits))
        if encoding == "karatsuba":
            def fit(x, width):
                return (z3.ZeroExt(width-x.size(), x) if x.size() <= width
                        else z3.Extract(width-1, 0, x))
            square = fit(karatsuba_product(n, n, leaf_bits), sw)
            cube = fit(karatsuba_product(square, n, leaf_bits), cw)
        else:
            square = z3.ZeroExt(sw-nw, n) * z3.ZeroExt(sw-nw, n)
            cube = z3.ZeroExt(cw-sw, square) * z3.ZeroExt(cw-nw, n)
        def weighted(ds, width):
            if base & (base-1) == 0:
                return z3.Concat(*reversed(ds)) if len(ds) > 1 else ds[0]
            return sum(z3.ZeroExt(width-dw, d) * base**i
                       for i, d in enumerate(ds))
        solver.add(weighted(sq, sw) == square)
        solver.add(weighted(cu, cw) == cube)
        # n <= upper makes both multiplications exact at these widths.
        info["bit_widths"] = {"n": nw, "square": sw, "cube": cw, "digit": dw}
        if residue_filter:
            if base & (base-1) == 0:
                # For b=2^w, reduce the sum of n's w-bit chunks modulo b-1.
                # This avoids a division of the full n bit-vector by b-1.
                chunks = [z3.Extract(min(i+dw-1, nw-1), i, n)
                          for i in range(0, nw, dw)]
                sum_width = (len(chunks)*(base-1)).bit_length()
                digit_sum = sum(z3.ZeroExt(sum_width-d.size(), d) for d in chunks)
                residue = z3.URem(digit_sum, base-1)
            else:
                residue = z3.URem(n, base-1)
            solver.add(z3.Or([residue == r for r in permitted]))
        if pin_n_digits:
            modulus = base ** pin_n_digits
            residue = random.Random(seed).randrange(lower, upper+1) % modulus
            solver.add(z3.URem(n, modulus) == residue)
            info["pinned_n_residue"] = str(residue)
    else:
        raise ValueError(encoding)
    return solver, n, info


def solve_one(base, encoding, seed, timeout_ms, pin_n_digits=0, residue_filter=True,
              sat_search="cdcl", memory_mb=1024, distinct_encoding="pairwise",
              leaf_bits=16):
    started = time.monotonic()
    solver, n, info = model(base, encoding, seed, timeout_ms, pin_n_digits,
                            residue_filter, sat_search, memory_mb,
                            distinct_encoding, leaf_bits)
    info["build_seconds"] = time.monotonic() - started
    if solver is None:
        return info
    before = time.monotonic()
    status = solver.check()
    info["solve_seconds"] = time.monotonic() - before
    info["result"] = str(status)
    if str(status) == "unknown":
        info["reason"] = solver.reason_unknown()
    if str(status) == "sat":
        candidate = solver.model().eval(n).as_long()
        sq, cu = digits(candidate**2, base), digits(candidate**3, base)
        info |= {"n": str(candidate), "square_digits": sq, "cube_digits": cu,
                 "independently_valid": len(sq+cu) == base and
                    sorted(sq+cu) == list(range(base))}
        assert info["independently_valid"], info
    info["statistics"] = str(solver.statistics())
    return info


def stochastic_one(base, seed, trials=50000, restart_after=200):
    """Compare uniform sampling and n-digit hill climbing, with exact fitness.

    This does not prune or prove anything. Each proposal is inside the exact
    candidate interval. Improvements compare distinct count, then pair collisions.
    """
    rng = random.Random(seed)
    limits = bounds(base)
    if limits is None:
        return {"base": base, "result": "excluded_digit_count"}
    _, _, lower, upper = limits
    powers = [1]
    while powers[-1] * base <= upper:
        powers.append(powers[-1] * base)
    def fitness(n):
        ds = digits(n*n, base) + digits(n*n*n, base)
        counts = [0] * base
        for d in ds:
            counts[d] += 1
        return sum(c > 0 for c in counts), -sum(c*(c-1)//2 for c in counts)
    result = {"base": base, "seed": seed, "trials_per_method": trials,
              "restart_after": restart_after, "methods": {}}
    for method in ["uniform", "digit_hill_climb"]:
        started = time.monotonic()
        n = rng.randrange(lower, upper+1)
        current = fitness(n)
        best_n, best = n, current
        stagnation = 0
        accepted = 0
        for _ in range(trials):
            if method == "uniform" or stagnation >= restart_after:
                candidate = rng.randrange(lower, upper+1)
                stagnation = 0
                current = (-1, 0)
            else:
                place = rng.choice(powers)
                delta = (rng.randrange(base) - n//place % base) * place
                candidate = n + delta
                if not lower <= candidate <= upper:
                    candidate = rng.randrange(lower, upper+1)
            score = fitness(candidate)
            if score >= current:
                accepted += 1
                stagnation = 0 if score > current else stagnation + 1
                n, current = candidate, score
            else:
                stagnation += 1
            if score > best:
                best_n, best = candidate, score
            if best[0] == base:
                break
        sq, cu = digits(best_n*best_n, base), digits(best_n**3, base)
        result["methods"][method] = {
            "seconds": time.monotonic()-started, "n": str(best_n),
            "unique_digits": best[0], "pair_collisions": -best[1],
            "accepted_proposals": accepted, "square_digits": sq,
            "cube_digits": cu, "nice": len(sq+cu) == base and best[0] == base}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bases", nargs="+", type=int, required=True)
    parser.add_argument("--encoding", choices=["int", "carry", "bv", "karatsuba", "stochastic"], default="bv")
    parser.add_argument("--timeout", type=float, default=10,
                        help="Seconds per base, excluding model construction")
    parser.add_argument("--seed", type=int, default=20260923)
    parser.add_argument("--pin-n-digits", type=int, default=0)
    parser.add_argument("--no-residue-filter", action="store_true")
    parser.add_argument("--sat-search", choices=["cdcl", "local"], default="cdcl")
    parser.add_argument("--memory-mb", type=int, default=1024)
    parser.add_argument("--trials", type=int, default=50000)
    parser.add_argument("--distinct", choices=["pairwise", "sort"], default="pairwise")
    parser.add_argument("--leaf-bits", type=int, default=16)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.output, "a") as output:
        for base in args.bases:
            if args.encoding == "stochastic":
                result = stochastic_one(base, args.seed, args.trials)
            else:
                result = solve_one(base, args.encoding, args.seed,
                               round(args.timeout*1000), args.pin_n_digits,
                               not args.no_residue_filter, args.sat_search,
                               args.memory_mb, args.distinct, args.leaf_bits)
            output.write(json.dumps(result, sort_keys=True)+"\n")
            output.flush()
            print(json.dumps({k:v for k,v in result.items()
                              if k != "statistics"}), flush=True)


if __name__ == "__main__":
    main()
