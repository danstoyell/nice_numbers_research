// quasi_nice.c -- exact enumeration of (1,2)-nice numbers: n and n^2 together use every
// base-b digit exactly once (total length b). Prints one JSON line per base with the band,
// the digit-sum/last-digit filtered count, the naive and conditional model expectations, and
// the exact hits. Build: clang -O3 -o quasi_nice quasi_nice.c -lm   Run: ./quasi_nice bmin bmax
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef unsigned __int128 u128; typedef uint64_t u64;
static int ndig(u128 x, int b) { int d = 0; while (x) { x /= b; ++d; } return d; }
static u128 ipow(int b, int e) { u128 r = 1; while (e--) r *= b; return r; }
static double lgam(double x) { return lgamma(x); }
int main(int argc, char **argv) {
    int bmin = atoi(argv[1]), bmax = atoi(argv[2]);
    for (int b = bmin; b <= bmax; ++b) {
        // band: s + c = b with s = digits(n), c = digits(n^2)
        u64 lo = 0, hi = 0; int found = 0, S = 0, C = 0;
        for (int s = 1; s < b; ++s) { int c = b - s; if (c != 2 * s && c != 2 * s - 1) continue;
            u128 l1 = ipow(b, s - 1), h1 = ipow(b, s) - 1;              // s digits
            // n^2 has c digits: b^(c-1) <= n^2 < b^c
            u128 l2 = (u128)ceill(sqrtl((long double)ipow(b, c - 1))), h2 = (u128)floorl(sqrtl((long double)(ipow(b, c) - 1)));
            while (l2 * l2 < ipow(b, c - 1)) ++l2; while (l2 > 0 && (l2 - 1) * (l2 - 1) >= ipow(b, c - 1)) --l2;
            while ((h2 + 1) * (h2 + 1) < ipow(b, c)) ++h2; while (h2 * h2 >= ipow(b, c)) --h2;
            u128 L = l1 > l2 ? l1 : l2, H = h1 < h2 ? h1 : h2;
            if (L <= H) { lo = (u64)L; hi = (u64)H; S = s; C = c; found = 1; break; } }
        if (!found) { printf("{\"b\":%d,\"band\":null}\n", b); continue; }
        int m = b - 1, T = (b * (b - 1) / 2) % m;
        // roots of x + x^2 = T mod (b-1); last digits with x != x^2 mod b
        int roots = 0; for (int x = 0; x < m; ++x) if ((x + x * x) % m == T) roots++;
        int lastok = 0; for (int x = 0; x < b; ++x) if ((x * x) % b != x) lastok++;
        u64 N = hi - lo + 1; double filt = (double)N * roots / m * lastok / b;
        double pnaive = exp(lgam(b + 1) - b * log(b));          // b!/b^b
        double e_naive = N * pnaive;
        // conditional model as in existence-counting: P(nice | digit-sum class, distinct last digits) ~ (b-1) * b/lastok * pnaive
        double e_cond = filt * pnaive * m * (double)b / lastok;
        long hits = 0; u64 hitlist[64]; 
        if (N <= 4000000000ULL) {
            for (u64 n = lo; n <= hi; ++n) {
                if (((n % m) + (n % m) * (n % m)) % m != T) continue;
                u128 sq = (u128)n * n; u64 mask = 0; int ok = 1; u64 x = n; u128 y = sq;
                for (int i = 0; i < S; ++i) { int d = x % b; x /= b; if (mask >> d & 1) { ok = 0; break; } mask |= 1ULL << d; }
                if (ok) for (int i = 0; i < C; ++i) { int d = (int)(y % b); y /= b; if (mask >> d & 1) { ok = 0; break; } mask |= 1ULL << d; }
                if (ok) { if (hits < 64) hitlist[hits] = n; hits++; }
            }
        } else hits = -1;
        printf("{\"b\":%d,\"s\":%d,\"c\":%d,\"lo\":%llu,\"hi\":%llu,\"N\":%llu,\"digit_sum_roots\":%d,\"expected_naive\":%.3f,\"expected_conditional\":%.3f,\"hits\":%ld,\"witnesses\":[",
               b, S, C, (unsigned long long)lo, (unsigned long long)hi, (unsigned long long)N, roots, e_naive, e_cond, hits);
        for (long i = 0; i < hits && i < 64; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)hitlist[i]);
        printf("]}\n"); fflush(stdout);
    }
    return 0;
}
