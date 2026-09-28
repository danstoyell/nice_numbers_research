// first_hit.c -- enumerator baseline for H5: candidates checked and time until the FIRST
// K-nice root, scanning the exact interval upward from a start point (wrapping at hi),
// visiting only residues mod b(b-1) that pass the digit-sum and distinct-last-digit
// filters. start = "lo" or a decimal seed for a uniformly random start point.
// Build: clang -O3 -o first_hit first_hit.c
// Run:   ./first_hit b K lo hi s c start
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
typedef unsigned __int128 u128; typedef uint64_t u64;
static int B, K, S2, S3; static u64 CHUNK; static int CHUNKD;
static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + 1e-9 * ts.tv_nsec; }
static inline void cnt64(u64 x, int nd, int *c) { for (int i = 0; i < nd; ++i) { c[x % B]++; x /= B; } }
static void cnt128(u128 x, int nd, int *c) { while (nd > CHUNKD) { u128 q = x / CHUNK; cnt64((u64)(x - q * CHUNK), CHUNKD, c); x = q; nd -= CHUNKD; } cnt64((u64)x, nd, c); }
static int knice(u64 n) { int c[64] = {0}; u128 sq = (u128)n * n; cnt128(sq, S2, c); cnt128(sq * n, S3, c); for (int a = 0; a < B; ++a) if (c[a] != K) return 0; return 1; }
int main(int argc, char **argv) {
    if (argc < 8) { fprintf(stderr, "usage: %s b K lo hi s c start\n", argv[0]); return 2; }
    B = atoi(argv[1]); K = atoi(argv[2]); u64 lo = strtoull(argv[3], 0, 10), hi = strtoull(argv[4], 0, 10); S2 = atoi(argv[5]); S3 = atoi(argv[6]);
    CHUNKD = 0; { u64 p = 1; while (p <= UINT64_MAX / B) { p *= B; ++CHUNKD; } CHUNK = p; }
    int m = B * (B - 1), T = (int)(((long long)K * B * (B - 1) / 2) % (B - 1));
    char *valid = calloc(m, 1);
    for (int r = 0; r < m; ++r) { int x = r % B, y = r % (B - 1); if ((x * x) % B == ((x * x) % B * x) % B) continue; if ((int)(((long long)y * y % (B - 1)) * (y + 1) % (B - 1)) != T) continue; valid[r] = 1; }
    u64 start = lo;
    if (strcmp(argv[7], "lo")) { u64 seed = strtoull(argv[7], 0, 10) * 0x9E3779B97F4A7C15ULL + 12345; seed ^= seed >> 29; seed *= 0xBF58476D1CE4E5B9ULL; seed ^= seed >> 32; start = lo + seed % (hi - lo + 1); }
    double t0 = now(); u64 checked = 0, visited = 0, n = start; int found = 0;
    for (;;) {
        if (valid[n % m]) { ++checked; if (knice(n)) { found = 1; break; } }
        ++visited; if (n == hi) n = lo; else ++n;
        if (n == start) break;
    }
    double dt = now() - t0;
    printf("{\"b\":%d,\"K\":%d,\"start\":%llu,\"found\":%d,\"witness\":%llu,\"full_checks\":%llu,\"visited\":%llu,\"seconds\":%.6f}\n",
           B, K, (unsigned long long)start, found, (unsigned long long)(found ? n : 0), (unsigned long long)checked, (unsigned long long)visited, dt);
    return 0;
}
