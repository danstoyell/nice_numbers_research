// D7 audit: hall_ok/augment from h1-domains/domains.c (lines 60-103, copied verbatim apart
// from dead locals) against an exhaustive backtracking search, on random small instances.
// Also tests the top-edge certification scan (domains.c lines 139-147) for soundness:
// every certified position must be constant over ALL n in [nmin, nmax].
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint64_t u64; typedef unsigned __int128 u128;
static int B;
int augment(int p, const u64 *dom, int *cnt, const int *cap, int owner[][8], int *assigned, int *visited);
static int hall_ok(const u64 *dom, const int *pos, int np, const int *cap) {
    int owner[128][8]; int cnt[64];
    for (int v = 0; v < B; ++v) cnt[v] = 0;
    int visited[64];
    int assigned[128]; for (int i = 0; i < np; ++i) assigned[i] = -1;
    for (int i = 0; i < np; ++i) {
        for (int v = 0; v < B; ++v) visited[v] = 0;
        int ok = augment(i, dom, cnt, cap, owner, assigned, visited);
        if (!ok) return 0;
    }
    (void)pos;
    return 1;
}
int augment(int p, const u64 *dom, int *cnt, const int *cap, int owner[][8], int *assigned, int *visited) {
    u64 d = dom[p];
    for (int v = 0; v < B; ++v) if ((d >> v & 1) && cnt[v] < cap[v]) {
        owner[v][cnt[v]++] = p; assigned[p] = v; return 1;
    }
    for (int v = 0; v < B; ++v) if ((d >> v & 1) && !visited[v]) {
        visited[v] = 1;
        for (int j = 0; j < cnt[v]; ++j) {
            int q = owner[v][j];
            if (augment(q, dom, cnt, cap, owner, assigned, visited)) { owner[v][j] = p; assigned[p] = v; return 1; }
        }
    }
    return 0;
}
static int brute(const u64 *dom, int np, int i, int *left) {
    if (i == np) return 1;
    for (int v = 0; v < B; ++v) if ((dom[i] >> v & 1) && left[v] > 0) {
        left[v]--; int r = brute(dom, np, i + 1, left); left[v]++;
        if (r) return 1;
    }
    return 0;
}
static u64 rs = 987654321;
static u64 rnd(void) { u64 z = (rs += 0x9E3779B97F4A7C15ULL); z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
static void digits(u128 x, int nd, int b, uint8_t *out) { for (int i = 0; i < nd; ++i) { out[i] = (uint8_t)(x % b); x /= b; } }
int main(void) {
    long tests = 0, bad = 0, feasible = 0;
    for (long it = 0; it < 2000000; ++it) {
        B = 2 + (int)(rnd() % 7);                 // 2..8 values
        int K = 1 + (int)(rnd() % 3);             // capacities up to 3
        int cap[64], tot = 0; for (int v = 0; v < B; ++v) { cap[v] = (int)(rnd() % (K + 1)); tot += cap[v]; }
        int np = (int)(rnd() % (tot + 2)); if (np > 12) np = 12;
        u64 dom[128]; int dens = 1 + (int)(rnd() % 4);
        for (int i = 0; i < np; ++i) { u64 m = 0; for (int v = 0; v < B; ++v) if ((int)(rnd() % 5) < dens) m |= 1ULL << v; dom[i] = m; }
        int left[64]; for (int v = 0; v < B; ++v) left[v] = cap[v];
        int a = hall_ok(dom, 0, np, cap), r = brute(dom, np, 0, left);
        ++tests; feasible += r; if (a != r) { ++bad; if (bad < 5) printf("HALL MISMATCH B=%d np=%d hall=%d brute=%d\n", B, np, a, r); }
    }
    printf("hall_ok: %ld random instances (%ld feasible), %ld mismatches\n", tests, feasible, bad);
    // top-edge scan soundness: small bases, all windows [nmin, nmax] of a batch shape
    long wins = 0, unsound = 0, certified_total = 0;
    for (int b = 3; b <= 12; ++b) for (int S = 2; S <= 7; ++S) {
        u128 lo = 1; for (int i = 0; i < S - 1; ++i) lo *= b; u128 hi = lo * b - 1;   // S-digit window of values n^2 (use n^2 < b^S)
        // choose n range so that n^2 has exactly S digits
        u64 nlo = 1; while ((u128)nlo * nlo < lo) ++nlo; u64 nhi = nlo; while ((u128)(nhi + 1) * (nhi + 1) <= hi) ++nhi;
        if (nhi < nlo) continue;
        for (int rep = 0; rep < 4000; ++rep) {
            u64 a = nlo + rnd() % (nhi - nlo + 1), w = rnd() % 40, z = a + w; if (z > nhi) z = nhi;
            int k = (int)(rnd() % 2);
            uint8_t ea[64], eb[64], ex[64];
            digits((u128)a * a, S, b, ea); digits((u128)z * z, S, b, eb);
            int p2 = S; while (p2 > k && ea[p2 - 1] == eb[p2 - 1]) --p2;     // domains.c line 146
            ++wins; certified_total += S - p2;
            for (u64 n = a; n <= z; ++n) { digits((u128)n * n, S, b, ex); for (int p = p2; p < S; ++p) if (ex[p] != ea[p]) { ++unsound; goto next; } }
            next:;
        }
    }
    printf("top-edge scan: %ld windows, %ld certified positions in total, %ld unsound\n", wins, certified_total, unsound);
    return bad || unsound;
}
