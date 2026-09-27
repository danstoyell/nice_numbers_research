#!/usr/bin/env python3
"""Deficiency of structured (rational-block) families versus random candidates.

deficiency(n) = b - #distinct digits among n^2, n^3 (0 means nice when the
length is b). A family with a niceness boost e^(cb) must show a lower
deficiency distribution than random candidates from the same interval.

Families (all members lie in the base-b candidate interval, gcd(d, b) = 1):
  A  single block:  n = (a*b^m + r)/d, 2 <= d <= 200, |r| <= 600
  B  two blocks:    n = (a*b^m + c*b^k + r)/d, d <= 12, |c| < d, 1<=k<m, |r|<=6
  C  rotation d:    as A, but d ranges over divisors of b^j - 1 and b^j + 1
                    (j <= 3), i.e. denominators that give linear digit runs
                    (these are the periodic / arithmetic-run roots)
Members are drawn at random from each family (seeded); Random: uniform
n in the interval, same sample size.

usage: family_scan.py BASE [BASE ...] [--quick]
"""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify import candidate_intervals  # noqa: E402

_pow_cache = {}


def _pows(b, n):
    key = b
    ps = _pow_cache.setdefault(key, [b])
    while ps[-1].bit_length() * 2 <= n.bit_length() + 64:
        ps.append(ps[-1] * ps[-1])
    return ps


def digits_le(x, b):
    """All base-b digits of x (order irrelevant here), divide and conquer."""
    ps = _pows(b, x)
    out = []

    def rec(v, k, pad):
        if k < 0:
            out.append(v)
            return
        hi, lo = divmod(v, ps[k])
        if hi or pad:
            rec(lo, k - 1, True)
            rec(hi, k - 1, pad)
        else:
            rec(lo, k - 1, pad)
    k = len(ps) - 1
    while k >= 0 and ps[k] > x:
        k -= 1
    rec(x, k, False)
    # strip leading zeros produced at the top of the unpadded recursion
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def deficiency(n, b):
    sq, cu = digits_le(n * n, b), digits_le(n * n * n, b)
    if len(sq) + len(cu) != b:
        return None
    return b - len(set(sq) | set(cu))


def divisors(x, limit):
    out, i = set(), 1
    while i * i <= x and i <= limit:
        if x % i == 0:
            out.add(i)
            if x // i <= limit:
                out.add(x // i)
        i += 1
    return sorted(out)


def family_A(b, lo, hi, m, dlist, R):
    B = b ** m
    for d in dlist:
        if d < 2 or math.gcd(d, b) != 1:
            continue
        amin, amax = (lo * d) // B, (hi * d) // B + 1
        for a in range(max(1, amin), amax + 1):
            if math.gcd(a, d) != 1:
                continue
            r0 = (-a * B) % d
            for r in range(r0 - ((R + r0) // d) * d, R + 1, d):
                n = (a * B + r) // d
                if lo <= n <= hi:
                    yield n


def family_B(b, lo, hi, m, DB, R, cap, rng):
    B = b ** m
    out = []
    for d in range(2, DB + 1):
        if math.gcd(d, b) != 1:
            continue
        amin, amax = (lo * d) // B, (hi * d) // B + 1
        for a in range(max(1, amin), amax + 1):
            if math.gcd(a, d) != 1:
                continue
            for k in range(1, m):
                for c in range(-(d - 1), d):
                    if c == 0:
                        continue
                    N0 = a * B + c * b ** k
                    r0 = (-N0) % d
                    for r in range(r0 - ((R + r0) // d) * d, R + 1, d):
                        n = (N0 + r) // d
                        if lo <= n <= hi:
                            out.append(n)
    if len(out) > cap:
        out = rng.sample(out, cap)
    return out


def stats(ds, b):
    ds = [x for x in ds if x is not None]
    if not ds:
        return None
    mu = sum(ds) / len(ds)
    var = sum((x - mu) ** 2 for x in ds) / max(1, len(ds) - 1)
    return {"count": len(ds), "mean": mu, "sd": math.sqrt(var),
            "min": min(ds), "mean_frac": mu / b}


def sample_family(b, lo, hi, m, dlist, R, blocks, count, rng, tries=200000):
    """Uniform-ish random members: d from dlist, a with a/d in range, r (and
    a second block c*b^k) random; rejects n outside [lo, hi]."""
    B = b ** m
    out = set()
    dlist = [d for d in dlist if d >= 2 and math.gcd(d, b) == 1]
    for _ in range(tries):
        if len(out) >= count or not dlist:
            break
        d = rng.choice(dlist)
        a = rng.randrange(max(1, (lo * d) // B), (hi * d) // B + 2)
        if math.gcd(a, d) != 1:
            continue
        N0 = a * B
        if blocks == 2:
            k = rng.randrange(1, m)
            c = rng.randrange(-(d - 1), d) or 1
            N0 += c * b ** k
        r = rng.randrange(-R, R + 1)
        r -= (N0 + r) % d
        n = (N0 + r) // d
        if lo <= n <= hi:
            out.add(n)
    return list(out)


def scan(b, quick):
    rng = random.Random(b)
    iv = candidate_intervals(b)
    if not iv:
        return None
    iv = iv[0]
    lo, hi = iv["lo"], iv["hi"]
    L = len(digits_le(hi, b))
    m = L - 1
    cnt = 3000 if quick else 20000
    rot = set()
    for j in (1, 2, 3):
        for x in (b ** j - 1, b ** j + 1):
            rot.update(divisors(x, b ** 3))
    fams = {
        "A": sample_family(b, lo, hi, m, range(2, 201), 600, 1, cnt, rng),
        "B": sample_family(b, lo, hi, m, range(2, 13), 6, 2, cnt, rng),
        "C": sample_family(b, lo, hi, m, sorted(rot), 50, 1, cnt, rng),
    }
    res = {"base": b, "L": L}
    for name, ns in fams.items():
        res[name] = stats([deficiency(n, b) for n in ns], b)
    nr = max(v["count"] for k, v in res.items() if isinstance(v, dict) and v)
    res["random"] = stats([deficiency(rng.randrange(lo, hi + 1), b)
                           for _ in range(nr)], b)
    return res


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quick = "--quick" in sys.argv
    out = []
    for a in args:
        b = int(a)
        res = scan(b, quick)
        if res is None:
            print(f"b={b}: no interval")
            continue
        out.append(res)
        line = f"b={b:>4} L={res['L']:>3} "
        for k in ("A", "B", "C", "random"):
            s = res.get(k)
            line += (f"| {k}: n={s['count']} mean={s['mean']:.1f} sd={s['sd']:.1f} "
                     f"min={s['min']} " if s else f"| {k}: - ")
        print(line, flush=True)
    tag = "quick" if quick else "full"
    p = Path(__file__).parent / "results" / f"family_scan_{tag}_{'_'.join(args)}.json"
    p.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
