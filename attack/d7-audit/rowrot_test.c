// D7 audit: row_rot_or from h3-covering/cover.c (copied verbatim, lines 26-46) against a
// naive bit-by-bit rotation, for every shift and M in {64k-1, 64k, 64k+1} up to 2048.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint64_t u64;
static int M, W;
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
static u64 rs = 12345;
static u64 rnd(void) { u64 z = (rs += 0x9E3779B97F4A7C15ULL); z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
int main(void) {
    long tests = 0, bad = 0;
    for (int k = 1; k <= 32; ++k) for (int dm = -1; dm <= 1; ++dm) {
        M = 64 * k + dm; if (M > 2048 || M < 2) continue; W = (M + 63) / 64;
        for (int rep = 0; rep < 1; ++rep) {
            u64 src[32] = {0}, dst[32], ref[32];
            for (int i = 0; i < W; ++i) src[i] = rnd() & rnd();
            if (M & 63) src[W - 1] &= (1ULL << (M & 63)) - 1;
            for (int sh = 0; sh < M; ++sh) {
                for (int i = 0; i < W; ++i) { dst[i] = 0; ref[i] = 0; }
                row_rot_or(src, dst, sh);
                for (int y = 0; y < M; ++y) if (src[y >> 6] >> (y & 63) & 1) { int z = (y + sh) % M; ref[z >> 6] |= 1ULL << (z & 63); }
                int ok = 1; for (int i = 0; i < W; ++i) if (dst[i] != ref[i]) ok = 0;
                ++tests; if (!ok) { ++bad; if (bad < 5) printf("MISMATCH M=%d sh=%d\n", M, sh); }
            }
        }
    }
    printf("row_rot_or: %ld (M, shift, pattern) tests, %ld mismatches\n", tests, bad);
    return bad != 0;
}
