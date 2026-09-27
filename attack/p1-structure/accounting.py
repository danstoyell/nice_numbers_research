#!/usr/bin/env python3
"""Exchange-rate accounting for structured families (Path 1, structure).

Model. A family has F = b^f members. In each member, S output digits are
"structured" (fixed by the family, assumed distinct for free) and the other
R = b - S behave like uniform random digits. The member is nice only if the
R random digits are exactly the R values the structured part misses:
probability R!/b^R. So the expected number of nice members is

    E = b^f * R! / b^R.

kappa = R / f is the exchange rate: random output digits created per free
input digit. The generic interval has f = b/5, R = b (kappa = 5).

Prints, for bases 60..1000:
  * log10 E for the generic interval (sanity check vs the critique's model);
  * R_max: the most random digits a family of size 10^20 (searchable) can
    leave while still having E >= 1, and the forced fraction this implies;
  * the smallest family size with E >= 1 at kappa = 5 and kappa = 9.
"""
import math

LN10 = math.log(10)


def log_fill(R, b):
    """ln(R!/b^R)."""
    return math.lgamma(R + 1) - R * math.log(b)


def r_max_for(logF, b):
    """Largest R with logF + ln(R!/b^R) >= 0."""
    R = 0
    while R < b and logF + log_fill(R + 1, b) >= 0:
        R += 1
    return R


def best_family(kappa, b):
    """Max over f of ln E with R = kappa*f <= b; also min F with E >= 1."""
    best, minF = -1e18, None
    fmax = b / kappa
    steps = 2000
    for i in range(1, steps + 1):
        f = fmax * i / steps
        lnE = f * math.log(b) + log_fill(kappa * f, b)
        best = max(best, lnE)
        if lnE >= 0 and minF is None:
            minF = f * math.log(b) / LN10
    return best / LN10, minF


def main():
    print(f"{'b':>5} {'log10E_gen':>10} {'Rmax@1e20':>9} {'forced%':>8} "
          f"{'kappa_max':>9} {'k=5:max log10E':>14} {'minF':>8} "
          f"{'k=9:max log10E':>14} {'minF':>8}")
    for b in (60, 80, 100, 118, 150, 200, 300, 500, 700, 1000):
        gen = (b / 5) * math.log(b) + log_fill(b, b)
        logF = 20 * LN10
        R = r_max_for(logF, b)
        f = logF / math.log(b)
        k5, m5 = best_family(5, b)
        k9, m9 = best_family(9, b)
        print(f"{b:>5} {gen/LN10:>10.1f} {R:>9} {100*(1-R/b):>7.1f}% "
              f"{R/f:>9.2f} {k5:>14.1f} {('%.0f' % m5) if m5 else '-':>8} "
              f"{k9:>14.1f} {('%.0f' % m9) if m9 else '-':>8}")


if __name__ == "__main__":
    main()
