#!/usr/bin/env python3
"""Bounded randomized suffix lifting; no claim of exhaustive coverage.

Construct n one base-b digit at a time, requiring all exposed square/cube
suffix digits to differ. Use exact interval and CRT feasibility at each step.
Compare with uniform sampling conditioned on the same digit-sum constraint.
"""
import argparse
import json
import random
import time
from pathlib import Path
from verify import candidate_intervals, digits, verify


def sum_roots(b):
    return [r for r in range(b-1)
            if (r*r*(r+1)-b*(b-1)//2) % (b-1) == 0]


def feasible_suffix(r, m, lo, hi, b, roots):
    low_t, high_t = max(0, (lo-r+m-1)//m), (hi-r)//m
    if low_t > high_t:
        return False
    q = b-1
    if high_t-low_t >= q-1:
        return True
    # m = b**k = 1 mod (b-1), so r+m*t = r+t mod (b-1).
    return any(low_t + ((s-r-low_t) % q) <= high_t for s in roots)


def lift(rng, b, lo, hi, roots, levels, trial_cap, reached):
    r, m, mask = 0, 1, 0
    for depth in range(levels):
        # Sampling without replacement makes failures meaningful for this node.
        choices = rng.sample(range(b), min(b, trial_cap))
        for a in choices:
            nr, nm = r+a*m, m*b
            if not feasible_suffix(nr, nm, lo, hi, b, roots):
                continue
            sd, cd = (nr*nr//m) % b, (nr*nr*nr//m) % b
            bits = (1 << sd) | (1 << cd)
            if sd == cd or mask & bits:
                continue
            r, m, mask = nr, nm, mask | bits
            reached[depth] += 1
            break
        else:
            return None
    assert lo <= r <= hi
    return r


def score(n, b):
    return len(set(digits(n*n,b)+digits(n*n*n,b)))


def experiment(b, attempts, seed, trial_cap):
    started = time.monotonic()
    rng = random.Random(seed+b)
    intervals, roots = candidate_intervals(b), sum_roots(b)
    if not intervals or not roots:
        return {"base": b, "excluded": True}
    assert len(intervals) == 1
    lo, hi = intervals[0]['lo'], intervals[0]['hi']
    levels = len(digits(hi, b))
    reached = [0]*levels
    completed, total_score = 0, 0
    best = {"distinct_digits": -1}
    seen = set()
    for _ in range(attempts):
        n = lift(rng,b,lo,hi,roots,levels,trial_cap,reached)
        if n is None:
            continue
        completed += 1
        seen.add(n)
        s = score(n,b)
        total_score += s
        if s > best['distinct_digits']:
            best = verify(n,b)
        if best.get('nice') and n != 69:
            break
    baseline_total, baseline_best = 0, {"distinct_digits": -1}
    classes = []
    for root in roots:
        first = lo + (root-lo) % (b-1)
        count = max(0, (hi-first)//(b-1)+1)
        if count:
            classes.append((first,count))
    population = sum(count for first,count in classes)
    for _ in range(attempts):
        index = rng.randrange(population)
        for first,count in classes:
            if index < count:
                n = first + index*(b-1)
                break
            index -= count
        s = score(n,b)
        baseline_total += s
        if s > baseline_best['distinct_digits']:
            baseline_best = verify(n,b)
    return {
        "base": b, "attempts": attempts, "seed": seed+b,
        "trial_cap": trial_cap, "root_digits": levels,
        "interval": {"lo": str(lo), "hi": str(hi)},
        "sum_residue_count": len(roots), "reached_each_depth": reached,
        "completed": completed, "distinct_completed": len(seen),
        "mean_distinct_lifted": total_score/completed if completed else None,
        "best_lifted": best,
        "mean_distinct_baseline": baseline_total/attempts,
        "best_baseline": baseline_best,
        "elapsed_seconds": time.monotonic()-started,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bases', type=int, nargs='+', default=[57,64,100,128,150,200,512])
    ap.add_argument('--attempts', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=20260923)
    ap.add_argument('--trial-cap', type=int, default=64)
    ap.add_argument('--output', default='results/digit-lifting.json')
    args = ap.parse_args()
    results = []
    for b in args.bases:
        row = experiment(b,args.attempts,args.seed,args.trial_cap)
        results.append(row)
        Path(args.output).write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps({k:row.get(k) for k in ['base','completed','mean_distinct_lifted','mean_distinct_baseline','elapsed_seconds']}),flush=True)


if __name__ == '__main__':
    main()
