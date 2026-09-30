/*
 * count_knice.c -- count k-(1,2)-nice numbers in base b.
 *
 * n is k-(1,2)-nice in base b if the base-b digits of n and n^2 together
 * contain every digit 0..b-1 exactly k times.  Then s + c = k*b where s, c are
 * the digit lengths of n and n^2, c in {2s-1, 2s}.  The band is
 *   kb = 3s   : n in [ceil(b^(s-1/2)), b^s)        (c = 2s)
 *   kb = 3s-1 : n in [b^(s-1), ceil(b^(s-1/2)))    (c = 2s-1)
 * (kb = 1 mod 3 has no band).
 *
 * Usage:
 *   count_knice b k                  exhaustive over the band
 *   count_knice b k S L seed         stratified sample: S strata, one random
 *                                    contiguous block of L roots per stratum
 * Output: one JSON line.
 *
 * Digit counts are accumulated in a packed 64-bit word (6 bits per digit,
 * b <= 10), using a table of packed count vectors for all w-digit chunks.
 * Requires n^2 < 2^128.  1 core.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

typedef unsigned __int128 u128;

static int B, K;
static uint64_t *tab;      /* packed counts of all W-digit strings (with leading zeros) */
static int W;              /* chunk width in digits */
static uint64_t BW;        /* B^W */

static uint64_t ipow(uint64_t b, int e) { uint64_t r = 1; while (e--) r *= b; return r; }

static int ndigits(u128 x) { int d = 0; while (x) { x /= B; d++; } return d; }

/* packed count of the number x written with exactly `len` digits (len >= digits of x) */
static inline uint64_t packed(u128 x, int len) {
    uint64_t acc = 0;
    int chunks = (len + W - 1) / W;
    for (int i = 0; i < chunks; i++) {
        uint64_t c;
        if (x >> 64) { c = (uint64_t)(x % BW); x /= BW; }
        else { uint64_t y = (uint64_t)x; c = y % BW; x = y / BW; }
        acc += tab[c];
    }
    /* padding zeros: chunks*W - len extra zeros were counted in field 0 */
    acc -= (uint64_t)(chunks * W - len);
    return acc;
}

/* splitmix64 */
static uint64_t sm_state;
static uint64_t sm(void) {
    uint64_t z = (sm_state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

int main(int argc, char **argv) {
    if (argc != 3 && argc != 6) { fprintf(stderr, "usage: %s b k [S L seed]\n", argv[0]); return 1; }
    B = atoi(argv[1]); K = atoi(argv[2]);
    if (B < 2 || B > 10) { fprintf(stderr, "b must be 2..10\n"); return 1; }
    int kb = K * B;
    int s, c;
    if (kb % 3 == 0) { s = kb / 3; c = 2 * s; }
    else if (kb % 3 == 2) { s = (kb + 1) / 3; c = 2 * s - 1; }
    else { printf("{\"b\":%d,\"k\":%d,\"band\":0,\"note\":\"kb=1 mod 3: no band\"}\n", B, K); return 0; }

    /* band endpoints: smallest n with n^2 >= b^(c-1) and n >= b^(s-1); n < b^s; n^2 < b^c */
    u128 bs1 = 1, bs = 1, bc1 = 1, bc = 1;
    for (int i = 0; i < s - 1; i++) bs1 *= B;
    bs = bs1 * B;
    for (int i = 0; i < c - 1; i++) bc1 *= B;
    bc = bc1 * B;
    if (bc == 0 || bs == 0) { fprintf(stderr, "overflow\n"); return 1; }
    /* lo = max(b^(s-1), ceil(sqrt(b^(c-1)))) ; hi = min(b^s, ceil(sqrt(b^c))) (exclusive) */
    uint64_t lo, hi;
    {
        long double r = sqrtl((long double)bc1);
        uint64_t t = (uint64_t)r; if (t > 2) t -= 2;
        while ((u128)t * t < bc1) t++;
        lo = t;
        if ((u128)lo < bs1) lo = (uint64_t)bs1;
        r = sqrtl((long double)bc);
        t = (uint64_t)r; if (t > 2) t -= 2;
        while ((u128)t * t < bc) t++;
        hi = t;
        if ((u128)hi > bs) hi = (uint64_t)bs;
    }
    if (hi <= lo) { printf("{\"b\":%d,\"k\":%d,\"band\":0}\n", B, K); return 0; }

    /* chunk table */
    W = (B <= 6) ? 6 : (B <= 8 ? 5 : 5);
    BW = ipow(B, W);
    tab = malloc(BW * sizeof(uint64_t));
    for (uint64_t x = 0; x < BW; x++) {
        uint64_t acc = 0, y = x;
        for (int i = 0; i < W; i++) { acc += 1ULL << (6 * (y % B)); y /= B; }
        tab[x] = acc;
    }
    uint64_t target = 0;
    for (int d = 0; d < B; d++) target += (uint64_t)K << (6 * d);

    uint64_t band = hi - lo, tested = 0, hits = 0;
    uint64_t first_hit = 0;
    /* hits by residue of n mod (b-1), and n + n^2 mod (b-1) */
    uint64_t hit_res[16] = {0};

    if (argc == 3) {
        for (uint64_t n = lo; n < hi; n++) {
            u128 n2 = (u128)n * n;
            uint64_t p = packed(n, s) + packed(n2, c);
            if (p == target) { hits++; if (!first_hit) first_hit = n; if (B > 2) hit_res[(uint64_t)(((u128)n + n2) % (B - 1))]++; }
        }
        tested = band;
    } else {
        uint64_t S = strtoull(argv[3], 0, 10), L = strtoull(argv[4], 0, 10);
        sm_state = strtoull(argv[5], 0, 10);
        for (uint64_t j = 0; j < S; j++) {
            uint64_t a = lo + (uint64_t)(((u128)band * j) / S);
            uint64_t e = lo + (uint64_t)(((u128)band * (j + 1)) / S);
            uint64_t len = e - a;
            uint64_t start = a + (len > L ? sm() % (len - L) : 0);
            uint64_t stop = start + (len > L ? L : len);
            for (uint64_t n = start; n < stop; n++) {
                u128 n2 = (u128)n * n;
                uint64_t p = packed(n, s) + packed(n2, c);
                if (p == target) { hits++; if (!first_hit) first_hit = n; if (B > 2) hit_res[(uint64_t)(((u128)n + n2) % (B - 1))]++; }
            }
            tested += stop - start;
        }
    }
    printf("{\"b\":%d,\"k\":%d,\"s\":%d,\"c\":%d,\"lo\":%llu,\"hi\":%llu,\"band\":%llu,\"tested\":%llu,\"hits\":%llu,\"first_hit\":%llu,\"sampled\":%s,\"hits_by_n_plus_n2_mod_bm1\":[",
           B, K, s, c, (unsigned long long)lo, (unsigned long long)hi, (unsigned long long)band,
           (unsigned long long)tested, (unsigned long long)hits, (unsigned long long)first_hit, argc == 6 ? "true" : "false");
    for (int r = 0; r < B - 1; r++) printf("%s%llu", r ? "," : "", (unsigned long long)hit_res[r]);
    printf("]}\n");
    return 0;
}
