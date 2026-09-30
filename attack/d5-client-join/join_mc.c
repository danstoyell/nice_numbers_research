// join_mc.c -- Monte Carlo measurement of the overlap join's list and match
// rates at bases where the join cannot be run in full (57-64), with the
// exact certification rules of overlap.c:
//   top list, depth j, cap c: prefix interval [A,E] = the n sharing the top j
//     digits of n (clipped to [lo,hi]); certified = output positions >= c of
//     n^2 and n^3 where floor(A^p/b^i) == floor(E^p/b^i); pass = distinct.
//   bottom list, depth j: positions 0..j-1 of n^2 and n^3 distinct.
//   digit-sum filter: n mod (b-1) in the roots.
// For uniform random n in [lo,hi] it records, for every depth j and every
// cap c, whether n's depth-j prefix passes (the probability equals the pass
// fraction of depth-j prefixes), whether n's depth-j residue passes, and for
// every (t,k) with t+k > L whether n is a match (ds & top(t,cap k) &
// bottom(k)) and a survivor (ds & all certified digits jointly distinct).
// Nothing else is modelled: list sizes, calls, matches and survivors of any
// region size follow from these rates (model_gain.py).
//
// Build: clang -O3 -o join_mc join_mc.c -lpthread
// Run:   ./join_mc B LO HI NSAMPLES SEED THREADS   (LO, HI decimal, inclusive)
// Output: one JSON line of counts.
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned __int128 u128;
typedef uint64_t u64;
typedef uint8_t u8;
typedef struct { u64 w[4]; } W;

static unsigned B, L, S2, S3;
static u128 LO, HI, POWB[40];
static unsigned NROOTS; static u8 ROOT_OK[64];

static W w_mul_u128(u128 a, u128 b) {
    u64 a0 = (u64)a, a1 = (u64)(a >> 64), b0 = (u64)b, b1 = (u64)(b >> 64);
    u128 p00 = (u128)a0 * b0, p01 = (u128)a0 * b1, p10 = (u128)a1 * b0, p11 = (u128)a1 * b1;
    W r; r.w[0] = (u64)p00;
    u128 mid = (p00 >> 64) + (u64)p01 + (u64)p10; r.w[1] = (u64)mid;
    u128 hi = (mid >> 64) + (p01 >> 64) + (p10 >> 64) + (u64)p11; r.w[2] = (u64)hi;
    r.w[3] = (u64)((hi >> 64) + (p11 >> 64));
    return r;
}
static W w_mul_w_u128(W a, u128 b) {
    u64 b0 = (u64)b, b1 = (u64)(b >> 64);
    W r = {{0, 0, 0, 0}}; u128 c = 0;
    for (int i = 0; i < 4; ++i) { c += (u128)a.w[i] * b0 + r.w[i]; r.w[i] = (u64)c; c >>= 64; }
    c = 0;
    for (int i = 0; i + 1 < 4; ++i) { c += (u128)a.w[i] * b1 + r.w[i + 1]; r.w[i + 1] = (u64)c; c >>= 64; }
    return r;
}
static u64 CH64; static unsigned CHD;               // b^CHD < 2^64
static inline u64 w_divrem64(W *a, u64 d) {
    u128 r = 0;
    for (int i = 3; i >= 0; --i) { u128 cur = (r << 64) | a->w[i]; a->w[i] = (u64)(cur / d); r = cur % d; }
    return (u64)r;
}
static int digits_of(W x, u8 *out) {           // LSD first, chunked through u64
    int n = 0;
    while (x.w[2] | x.w[3]) { u64 r = w_divrem64(&x, CH64); for (unsigned i = 0; i < CHD; ++i) { out[n++] = (u8)(r % B); r /= B; } }
    u128 y = ((u128)x.w[1] << 64) | x.w[0];
    while (y >> 64) { u128 q = y / CH64; u64 r = (u64)(y - q * CH64); for (unsigned i = 0; i < CHD; ++i) { out[n++] = (u8)(r % B); r /= B; } y = q; }
    u64 z = (u64)y;
    while (z) { out[n++] = (u8)(z % B); z /= B; }
    return n;
}

#define MAXL 16
#define MAXD 48
// per-thread counts
typedef struct {
    u64 n, ds;
    u64 top[MAXL + 1][MAXL + 1];            // [depth j][cap c]
    u64 bot[MAXL + 1];                      // [depth j]
    u64 match[MAXL + 1][MAXL + 1];          // [t][k]
    u64 surv[MAXL + 1][MAXL + 1];
    u64 seed;
} Acc;

static u64 splitmix(u64 *s) { u64 z = (*s += 0x9E3779B97F4A7C15ULL); z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
static u64 NS; static unsigned NTHR;

static void *worker(void *arg) {
    Acc *a = arg;
    u128 span = HI - LO + 1;
    u8 d2[MAXD], d3[MAXD], xa2[MAXD], xe2[MAXD], xa3[MAXD], xe3[MAXD];
    for (u64 s = 0; s < NS / NTHR; ++s) {
        u128 r = ((u128)splitmix(&a->seed) << 64) | splitmix(&a->seed);
        u128 n = LO + r % span;
        a->n++;
        int ds = ROOT_OK[(unsigned)(n % (B - 1))];
        a->ds += ds;
        W sq = w_mul_u128(n, n), cu = w_mul_w_u128(sq, n);
        int l2 = digits_of(sq, d2), l3 = digits_of(cu, d3);
        (void)l2; (void)l3;
        // bottom: positions 0..j-1 of both powers distinct
        int botok[MAXL + 1]; u64 m = 0; botok[0] = 1;
        for (unsigned j = 1; j <= L; ++j) {
            int ok = botok[j - 1];
            if (ok) { u64 b1 = 1ULL << d2[j - 1], b2 = 1ULL << d3[j - 1]; if ((m & b1) || (m & b2) || b1 == b2) ok = 0; m |= b1 | b2; }
            botok[j] = ok;
            a->bot[j] += ok;
        }
        // top: for each depth j, the certified block of each power is the
        // common MSD prefix [i2, S2) / [i3, S3) of the interval endpoints'
        // powers; for cap c the positions >= max(c, i) count. Masks for caps
        // L..0 are built incrementally (positions >= L first, then c = L-1..0).
        int topok[MAXL + 1][MAXL + 1];
        u64 topmask[MAXL + 1][MAXL + 1];
        for (unsigned j = 1; j <= L; ++j) {
            u128 w = POWB[L - j];
            u128 P = n / w;
            u128 A = P * w, E = A + w - 1;
            if (A < LO) A = LO;
            if (E > HI) E = HI;
            W a2 = w_mul_u128(A, A), e2 = w_mul_u128(E, E), a3 = w_mul_w_u128(a2, A), e3 = w_mul_w_u128(e2, E);
            int la2 = digits_of(a2, xa2), le2 = digits_of(e2, xe2), la3 = digits_of(a3, xa3), le3 = digits_of(e3, xe3);
            int i2 = (int)S2, i3 = (int)S3;
            if (la2 == le2 && la2 == (int)S2) while (i2 > 0 && xa2[i2 - 1] == xe2[i2 - 1]) --i2;
            if (la3 == le3 && la3 == (int)S3) while (i3 > 0 && xa3[i3 - 1] == xe3[i3 - 1]) --i3;
            u64 mm = 0; int ok = 1;
            for (int i = (int)S2 - 1; i >= i2 && i >= (int)L; --i) { u64 bt = 1ULL << xa2[i]; if (mm & bt) ok = 0; mm |= bt; }
            for (int i = (int)S3 - 1; i >= i3 && i >= (int)L; --i) { u64 bt = 1ULL << xa3[i]; if (mm & bt) ok = 0; mm |= bt; }
            topok[j][L] = ok; topmask[j][L] = mm;
            for (int c = (int)L - 1; c >= 0; --c) {
                if (ok && c >= i2) { u64 bt = 1ULL << xa2[c]; if (mm & bt) ok = 0; mm |= bt; }
                if (ok && c >= i3) { u64 bt = 1ULL << xa3[c]; if (mm & bt) ok = 0; mm |= bt; }
                topok[j][c] = ok; topmask[j][c] = mm;
            }
            for (unsigned c = 0; c <= L; ++c) a->top[j][c] += topok[j][c];
        }
        // matches and survivors for every (t,k), t+k > L, k < L
        u64 bm[MAXL + 1]; bm[0] = 0;
        for (unsigned j = 1; j <= L; ++j) bm[j] = bm[j - 1] | (1ULL << d2[j - 1]) | (1ULL << d3[j - 1]);
        if (!ds) continue;
        for (unsigned t = 1; t <= L; ++t)
            for (unsigned k = 1; k < L; ++k) {
                if (t + k <= L) continue;
                if (topok[t][k] && botok[k]) {
                    a->match[t][k]++;
                    if (!(topmask[t][k] & bm[k])) a->surv[t][k]++;
                }
            }
    }
    return NULL;
}
static u128 parse_u128(const char *s) { u128 x = 0; while (*s) x = x * 10 + (u128)(*s++ - '0'); return x; }

int main(int argc, char **argv) {
    if (argc < 7) { fprintf(stderr, "usage: join_mc B LO HI NSAMPLES SEED THREADS\n"); return 2; }
    B = (unsigned)atoi(argv[1]); LO = parse_u128(argv[2]); HI = parse_u128(argv[3]);
    NS = strtoull(argv[4], 0, 10); u64 seed = strtoull(argv[5], 0, 10); NTHR = (unsigned)atoi(argv[6]);
    POWB[0] = 1; for (int i = 1; i < 40; ++i) POWB[i] = POWB[i - 1] * B;
    CH64 = 1; CHD = 0; while ((u128)CH64 * B < ((u128)1 << 64)) { CH64 *= B; CHD++; }
    L = 0; for (u128 x = HI; x; x /= B) L++;
    { u8 tmp[MAXD]; W sq = w_mul_u128(LO, LO), cu = w_mul_w_u128(sq, LO); S2 = (unsigned)digits_of(sq, tmp); S3 = (unsigned)digits_of(cu, tmp); }
    unsigned m1 = B - 1, tgt = (unsigned)(((u64)B * (B - 1) / 2) % m1);
    for (unsigned r = 0; r < m1; ++r) if ((unsigned)(((u64)r * r + (u64)r * r * r) % m1) == tgt) { ROOT_OK[r] = 1; NROOTS++; }
    pthread_t th[64]; Acc *acc = calloc(NTHR, sizeof(Acc));
    for (unsigned i = 0; i < NTHR; ++i) { acc[i].seed = seed * 1000003ULL + i; pthread_create(&th[i], NULL, worker, &acc[i]); }
    Acc t; memset(&t, 0, sizeof t);
    for (unsigned i = 0; i < NTHR; ++i) {
        pthread_join(th[i], NULL);
        t.n += acc[i].n; t.ds += acc[i].ds;
        for (unsigned j = 0; j <= MAXL; ++j) {
            t.bot[j] += acc[i].bot[j];
            for (unsigned c = 0; c <= MAXL; ++c) { t.top[j][c] += acc[i].top[j][c]; t.match[j][c] += acc[i].match[j][c]; t.surv[j][c] += acc[i].surv[j][c]; }
        }
    }
    printf("{\"base\":%u,\"L\":%u,\"S2\":%u,\"S3\":%u,\"roots\":%u,\"n\":%llu,\"ds\":%llu,\"bot\":[", B, L, S2, S3, NROOTS, (unsigned long long)t.n, (unsigned long long)t.ds);
    for (unsigned j = 0; j <= L; ++j) printf("%s%llu", j ? "," : "", (unsigned long long)(j ? t.bot[j] : t.n));
    printf("],\"top\":[");
    for (unsigned j = 0; j <= L; ++j) { printf("%s[", j ? "," : ""); for (unsigned c = 0; c <= L; ++c) printf("%s%llu", c ? "," : "", (unsigned long long)(j ? t.top[j][c] : t.n)); printf("]"); }
    printf("],\"match\":[");
    for (unsigned j = 0; j <= L; ++j) { printf("%s[", j ? "," : ""); for (unsigned c = 0; c <= L; ++c) printf("%s%llu", c ? "," : "", (unsigned long long)t.match[j][c]); printf("]"); }
    printf("],\"surv\":[");
    for (unsigned j = 0; j <= L; ++j) { printf("%s[", j ? "," : ""); for (unsigned c = 0; c <= L; ++c) printf("%s%llu", c ? "," : "", (unsigned long long)t.surv[j][c]); printf("]"); }
    printf("]}\n");
    return 0;
}
