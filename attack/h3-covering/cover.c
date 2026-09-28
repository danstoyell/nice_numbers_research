// cover.c -- which residue pairs (X mod M, Y mod M) do pandigital splits realize?
//
// Base b, lengths s + c (the "square word" X has s digits, the "cube word" Y has
// c digits), modulus M. A split assigns the digits 0..b-1 (each once; for K>1 the
// multiset with each digit K times is NOT handled here) to the s + c positions with
// both leading digits nonzero. This program computes the EXACT set of pairs
// (X mod M, Y mod M) over all splits by a dynamic programme over positions whose
// state is (set of digits used so far, X mod M, Y mod M); for each used-set the
// reachable (x, y) pairs are stored as an M x M bitset. It then compares the image
// with the set the digit-sum congruence alone allows,
//     {(x, y) : x + y == T (mod gcd(M, b-1))},  T = b(b-1)/2,
// which the image is always contained in (digit sum == X + Y mod b-1).
//
// Build: clang -O3 -o cover cover.c
// Run:   ./cover b s c M [M ...]     (one JSON line per M)
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint64_t u64;
static int b, s, c, M, W, T;

static int gcd(int x, int y) { while (y) { int t = x % y; x = y; y = t; } return x; }

// dst |= src rotated left by sh bits, as M-bit integers (bit y -> bit (y+sh) mod M).
static void row_rot_or(const u64 *src, u64 *dst, int sh) {
    u64 tmp[32];
    int top = M & 63;
    if (sh == 0) { for (int i = 0; i < W; ++i) dst[i] |= src[i]; return; }
    int ws = sh >> 6, bs = sh & 63;
    for (int i = W - 1; i >= 0; --i) {
        u64 v = 0; int j = i - ws;
        if (j >= 0) { v = src[j] << bs; if (bs && j - 1 >= 0) v |= src[j - 1] >> (64 - bs); }
        tmp[i] = v;
    }
    if (top) tmp[W - 1] &= (1ULL << top) - 1;
    int sr = M - sh; ws = sr >> 6; bs = sr & 63;
    for (int i = 0; i < W; ++i) {
        u64 v = 0; int j = i + ws;
        if (j < W) { v = src[j] >> bs; if (bs && j + 1 < W) v |= src[j + 1] << (64 - bs); }
        tmp[i] |= v;
    }
    if (top) tmp[W - 1] &= (1ULL << top) - 1;
    for (int i = 0; i < W; ++i) dst[i] |= tmp[i];
}

static int *idx;            // mask -> index within its level
static unsigned *lvl[64];   // masks per level
static int nlvl[64];

static void run(int Mv) {
    M = Mv; W = (M + 63) / 64;
    size_t rowwords = (size_t)M * W;   // words per state
    int maxlvl = 0;
    for (int j = 0; j <= b; ++j) if (nlvl[j] > maxlvl) maxlvl = nlvl[j];
    u64 *cur = calloc((size_t)maxlvl * rowwords, 8), *nxt = calloc((size_t)maxlvl * rowwords, 8);
    if (!cur || !nxt) { fprintf(stderr, "alloc failed\n"); exit(1); }
    // powers of b mod M
    int pw[128]; pw[0] = 1 % M; for (int i = 1; i < 128 && i <= (s > c ? s : c); ++i) pw[i] = (int)((long long)pw[i - 1] * b % M);
    // initial state: mask 0, (0,0)
    cur[0] = 1ULL;
    for (int step = 0; step < s + c; ++step) {
        int phaseX = step < s;
        int i = phaseX ? step : step - s;
        int weight = pw[i];
        int leading = phaseX ? (i == s - 1) : (i == c - 1);
        memset(nxt, 0, (size_t)nlvl[step + 1] * rowwords * 8);
        for (int a = 0; a < nlvl[step]; ++a) {
            unsigned mask = lvl[step][a];
            const u64 *st = cur + (size_t)a * rowwords;
            for (int d = 0; d < b; ++d) {
                if (mask >> d & 1) continue;
                if (leading && d == 0) continue;
                int delta = (int)((long long)d * weight % M);
                u64 *dst = nxt + (size_t)idx[mask | (1u << d)] * rowwords;
                if (phaseX) {   // x += delta: move row x to row (x+delta) mod M
                    for (int x = 0; x < M; ++x) {
                        int x2 = x + delta; if (x2 >= M) x2 -= M;
                        const u64 *sr = st + (size_t)x * W; u64 *dr = dst + (size_t)x2 * W;
                        for (int w = 0; w < W; ++w) dr[w] |= sr[w];
                    }
                } else {        // y += delta: rotate every row
                    for (int x = 0; x < M; ++x) row_rot_or(st + (size_t)x * W, dst + (size_t)x * W, delta);
                }
            }
        }
        u64 *t = cur; cur = nxt; nxt = t;
    }
    // final level: a single mask (all digits used)
    const u64 *fin = cur;
    int g = gcd(M, b - 1);
    long long image = 0, bad = 0;
    for (int x = 0; x < M; ++x)
        for (int y = 0; y < M; ++y)
            if (fin[(size_t)x * W + (y >> 6)] >> (y & 63) & 1) {
                ++image;
                if ((x + y - T) % g != 0) ++bad;
            }
    long long predicted = (long long)M * M / g;
    printf("{\"b\":%d,\"s\":%d,\"c\":%d,\"M\":%d,\"coprime_to_b\":%s,\"g\":%d,\"image\":%lld,\"predicted\":%lld,"
           "\"missing\":%lld,\"outside_prediction\":%lld,\"equal\":%s}\n",
           b, s, c, M, gcd(M, b) == 1 ? "true" : "false", g, image, predicted, predicted - image, bad,
           (image == predicted && bad == 0) ? "true" : "false");
    fflush(stdout);
    free(cur); free(nxt);
}

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: %s b s c M [M ...]\n", argv[0]); return 2; }
    b = atoi(argv[1]); s = atoi(argv[2]); c = atoi(argv[3]);
    if (s + c != b || b > 24) { fprintf(stderr, "need s + c == b <= 24 (each digit used once)\n"); return 2; }
    T = b * (b - 1) / 2;
    idx = malloc(sizeof(int) << b);
    for (int j = 0; j <= b; ++j) nlvl[j] = 0;
    for (unsigned m = 0; m < (1u << b); ++m) ++nlvl[__builtin_popcount(m)];
    for (int j = 0; j <= b; ++j) { lvl[j] = malloc(sizeof(unsigned) * nlvl[j]); nlvl[j] = 0; }
    for (unsigned m = 0; m < (1u << b); ++m) { int j = __builtin_popcount(m); idx[m] = nlvl[j]; lvl[j][nlvl[j]++] = m; }
    for (int a = 4; a < argc; ++a) { int Mv = atoi(argv[a]); if (Mv < 2 || Mv > 2048) continue; run(Mv); }
    return 0;
}
