// nm12.c -- exhaustive deficiency histogram for the (1,2) problem: for every n in the band
// (len(n) + len(n^2) = b), the number of distinct digits among n and n^2 together; the
// deficiency is b minus that. Deficiency 0 = (1,2)-nice. Also splits the deficiency 1 and 2
// counts by n's class (valid digit-sum class or not) and records deficiency-1 witnesses
// (first 2000) for inspection.
// Build: clang -O3 -mcpu=native -DBASE=24 -o bin/nm12_b24 nm12.c
// Run:   bin/nm12_b24 chunk nchunks    (chunk = contiguous 1/nchunks of the band)
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef unsigned __int128 u128;
typedef uint64_t u64;
#ifndef BASE
#error "define BASE"
#endif
#define b ((u64)BASE)
#define HS 6

static u64 isqrt128(u128 x) {
    u64 lo = 0, hi = ((u64)1 << 63);
    while (lo < hi) { u64 mid = lo + (hi - lo + 1) / 2; if ((u128)mid * mid <= x) lo = mid; else hi = mid - 1; }
    return lo;
}
static u128 ipow128(int e) { u128 r = 1; while (e--) r *= b; return r; }

int main(int argc, char **argv) {
    int chunk = atoi(argv[1]), nchunks = atoi(argv[2]);
    int S = 0, C = 0; u64 LO = 0, HI = 0;
    for (int s = 1; s < BASE; ++s) {
        int c = BASE - s;
        if (c != 2 * s && c != 2 * s - 1) continue;
        u128 l1 = ipow128(s - 1), h1 = ipow128(s) - 1;
        u128 l2 = isqrt128(ipow128(c - 1) - 1) + 1, h2 = isqrt128(ipow128(c) - 1);
        u128 L = l1 > l2 ? l1 : l2, H = h1 < h2 ? h1 : h2;
        if (L <= H) { LO = (u64)L; HI = (u64)H; S = s; C = c; break; }
    }
    if (!S) { printf("{\"b\":%d,\"band\":null}\n", BASE); return 0; }
    u64 BH = 1; for (int i = 0; i < HS; ++i) BH *= b;
    int m1 = BASE - 1, target = (BASE * (BASE - 1) / 2) % m1;
    int valid[64]; for (int x = 0; x < m1; ++x) valid[x] = ((x + x * x) % m1 == target);
    u64 N = HI - LO + 1;
    u64 a = LO + (u64)((u128)N * chunk / nchunks), z = LO + (u64)((u128)N * (chunk + 1) / nchunks); // [a, z)
    u64 hist[65] = {0}, d1v = 0, d2v = 0;
    static u64 wit[2000]; int nw = 0;
    for (u64 n = a; n < z; ++n) {
        u64 m = 0, v = n;
        for (int i = 0; i < S; ++i) { m |= 1ULL << (v % b); v /= b; }
        u64 x = n / BH, y = n % BH;
        u64 y2 = y * y;
        u64 l0 = y2 % BH, cy = y2 / BH;
        u64 t1 = 2 * x * y + cy;
        u64 l1 = t1 % BH; cy = t1 / BH;
        u64 t2 = x * x + cy;
        u64 l2 = t2 % BH, l3 = t2 / BH;
        u64 L[4] = {l0, l1, l2, l3};
        int k = 0;
        for (int li = 0; li < 4 && k < C; ++li) { u64 w = L[li]; for (int i = 0; i < HS && k < C; ++i, ++k) { m |= 1ULL << (w % b); w /= b; } }
        int def = BASE - __builtin_popcountll(m);
        hist[def]++;
        if (def == 1 || def == 2) {
            int vc = valid[n % m1];
            if (def == 1) { d1v += vc; if (nw < 2000) wit[nw++] = n; } else d2v += vc;
        }
    }
    printf("{\"b\":%d,\"s\":%d,\"c\":%d,\"lo\":%llu,\"hi\":%llu,\"chunk\":%d,\"nchunks\":%d,\"from\":%llu,\"to\":%llu,\"hist\":[",
           BASE, S, C, (unsigned long long)LO, (unsigned long long)HI, chunk, nchunks, (unsigned long long)a, (unsigned long long)(z - 1));
    for (int d = 0; d <= BASE; ++d) printf("%s%llu", d ? "," : "", (unsigned long long)hist[d]);
    printf("],\"def1_valid_class\":%llu,\"def2_valid_class\":%llu,\"def1_witnesses\":[", (unsigned long long)d1v, (unsigned long long)d2v);
    for (int i = 0; i < nw; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)wit[i]);
    printf("]}\n");
    return 0;
}
