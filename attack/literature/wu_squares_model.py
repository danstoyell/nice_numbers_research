"""Random-digit model vs. the exact counts of strictly pandigital squares (OEIS A258103).

E(b) = #{n : n^2 has exactly b base-b digits, n mod (b-1) in A_b} * (b-1)*(b-1)!/b^(b-1)
where A_b = square roots of b(b-1)/2 mod (b-1) (Wu, arXiv:2403.20304, Thm 1).
The factor (b-1) conditions a random string on the digit-sum class that every
square in the allowed residues already satisfies.
"""
from math import factorial, isqrt
A258103 = {2:0,3:0,4:1,5:0,6:1,7:3,8:4,9:26,10:87,11:47,12:87,13:0,14:547,15:1303,16:3402,17:0,18:24192,19:187562}
tot_o = tot_e = 0.0
print(" b   observed    model   ratio")
for b in range(4, 20):
    m = b - 1
    T = b * (b - 1) // 2
    A = [r for r in range(m) if (r * r - T) % m == 0]
    lo = isqrt(b ** (b - 1) - 1) + 1          # smallest n with n^2 >= b^(b-1)
    hi = isqrt(b ** b - 1)                     # largest n with n^2 < b^b
    # count n in [lo, hi] with n mod m in A
    def cnt(x):  # n in [0, x]
        q, r = divmod(x + 1, m)
        return q * len(A) + sum(1 for a in A if a < r)
    ncand = cnt(hi) - cnt(lo - 1)
    E = ncand * m * factorial(b - 1) / b ** (b - 1)
    o = A258103[b]
    print(f"{b:2d} {o:10d} {E:10.1f}   {o/E if E else float('nan'):.3f}")
    if b >= 9 and E > 0:
        tot_o += o; tot_e += E
print(f"bases 9-19 pooled: observed {tot_o:.0f}, model {tot_e:.1f}, ratio {tot_o/tot_e:.3f}")
