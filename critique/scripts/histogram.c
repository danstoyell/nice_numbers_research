// Exact distinct-digit histogram of (n^2, n^3) over an interval, base <= 64.
//
// Independent of the public client. Each thread seeds its chunk with exact
// 128-bit arithmetic, then advances n -> n+1 by digit-array additions:
//   n^2 += 2n+1,   n^3 += 3n^2+3n+1,   (3n^2+3n+1) += 6n+6,
// so no per-candidate division is needed. The distinct-digit count is the
// popcount of a 64-bit occupancy mask. Every candidate with at least
// (base - report_deficiency) distinct digits is printed.
//
// Build: clang -O3 -o histogram histogram.c -lpthread
// Run:   ./histogram BASE LO HI SQUARE_DIGITS CUBE_DIGITS THREADS REPORT_DEF [MULT]
// Output: one JSON object on stdout.
// MULT (default 1) is the required multiplicity for "exact hit" reporting:
// with MULT=2 the program also counts n whose digits contain every value
// exactly twice (used for the twice-nice analogue); lengths must sum to
// MULT*BASE for that count to be meaningful.
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned __int128 u128;
#define MAXD 160

static unsigned B, L2, L3, THREADS, REPORT_DEF, MULT;
static u128 LO, HI;

typedef struct {
    u128 start, end;           // inclusive
    uint64_t hist[65];
    uint64_t exact_hits;       // every digit exactly MULT times
    u128 hits[64];
    unsigned nhits;
    u128 reported[4096];
    unsigned char reported_distinct[4096];
    unsigned nreported;
    int overflow;
} Job;

static u128 parse_u128(const char *s) {
    u128 v = 0;
    for (; *s; ++s) v = v * 10 + (u128)(*s - '0');
    return v;
}

static void print_u128(FILE *f, u128 v) {
    char buf[64];
    int i = 63;
    buf[i] = 0;
    if (v == 0) buf[--i] = '0';
    while (v) { buf[--i] = (char)('0' + (int)(v % 10)); v /= 10; }
    fputs(buf + i, f);
}

// Write value's base-B digits (LSD first) into out[0..len-1]; return 0 if it
// does not fit in len digits.
static int to_digits(u128 value, unsigned *out, unsigned len) {
    for (unsigned i = 0; i < len; ++i) { out[i] = (unsigned)(value % B); value /= B; }
    return value == 0;
}

// a += d (both LSD-first, length len); return final carry.
static inline unsigned add_into(unsigned *a, const unsigned *d, unsigned len) {
    unsigned carry = 0;
    for (unsigned i = 0; i < len; ++i) {
        unsigned t = a[i] + d[i] + carry;
        carry = t >= B;
        a[i] = carry ? t - B : t;
    }
    return carry;
}

// a += small constant
static inline unsigned add_small(unsigned *a, unsigned len, unsigned c) {
    for (unsigned i = 0; i < len && c; ++i) {
        unsigned t = a[i] + c;
        c = t / B;
        a[i] = t % B;
    }
    return c;
}

static void *run(void *arg) {
    Job *job = (Job *)arg;
    unsigned sq[MAXD], cu[MAXD], d2[MAXD], d3[MAXD], e3[MAXD];
    u128 n = job->start;
    memset(sq, 0, sizeof sq); memset(cu, 0, sizeof cu);
    memset(d2, 0, sizeof d2); memset(d3, 0, sizeof d3); memset(e3, 0, sizeof e3);
    // Increments: d2 = 2n+1 (< n^2 width), d3 = 3n^2+3n+1, e3 = 6n+6.
    if (!to_digits(n * n, sq, L2) || !to_digits(n * n * n, cu, L3) ||
        !to_digits(2 * n + 1, d2, L2) || !to_digits(3 * n * n + 3 * n + 1, d3, L3) ||
        !to_digits(6 * n + 6, e3, L3)) {
        job->overflow = 1;
        return NULL;
    }
    unsigned counts[64];
    for (;;) {
        uint64_t mask = 0;
        for (unsigned i = 0; i < L2; ++i) mask |= 1ULL << sq[i];
        for (unsigned i = 0; i < L3; ++i) mask |= 1ULL << cu[i];
        unsigned distinct = (unsigned)__builtin_popcountll(mask);
        job->hist[distinct]++;
        if (distinct + REPORT_DEF >= B && job->nreported < 4096) {
            job->reported[job->nreported] = n;
            job->reported_distinct[job->nreported++] = (unsigned char)distinct;
        }
        if (MULT > 1 && distinct == B) {
            memset(counts, 0, sizeof counts);
            for (unsigned i = 0; i < L2; ++i) counts[sq[i]]++;
            for (unsigned i = 0; i < L3; ++i) counts[cu[i]]++;
            int ok = 1;
            for (unsigned v = 0; v < B; ++v) ok &= counts[v] == MULT;
            if (ok) { job->exact_hits++; if (job->nhits < 64) job->hits[job->nhits++] = n; }
        }
        if (n == job->end) break;
        // advance to n+1
        if (add_into(sq, d2, L2) || add_into(cu, d3, L3)) { job->overflow = 1; break; }
        add_into(d3, e3, L3);
        add_small(d2, L2, 2);
        add_small(e3, L3, 6);
        n += 1;
    }
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 8) {
        fprintf(stderr, "usage: %s BASE LO HI SQUARE_DIGITS CUBE_DIGITS THREADS REPORT_DEF [MULT]\n", argv[0]);
        return 2;
    }
    B = (unsigned)atoi(argv[1]);
    LO = parse_u128(argv[2]);
    HI = parse_u128(argv[3]);
    L2 = (unsigned)atoi(argv[4]);
    L3 = (unsigned)atoi(argv[5]);
    THREADS = (unsigned)atoi(argv[6]);
    REPORT_DEF = (unsigned)atoi(argv[7]);
    MULT = argc > 8 ? (unsigned)atoi(argv[8]) : 1;
    if (B < 2 || B > 64 || L2 > MAXD || L3 > MAXD || HI < LO || THREADS < 1) return 3;
    // n^3 must fit in 128 bits (checked on HI, the largest n)
    u128 hi = HI;
    if (hi > ((u128)1 << 42) * ((u128)1 << 42)) return 4;  // n < 2^84 at least
    long double approx = (long double)hi;
    if (approx * approx * approx >= 3.4e38L) return 5;
    u128 total = HI - LO + 1;
    Job *jobs = calloc(THREADS, sizeof(Job));
    pthread_t *tids = calloc(THREADS, sizeof(pthread_t));
    u128 step = total / THREADS;
    for (unsigned t = 0; t < THREADS; ++t) {
        jobs[t].start = LO + step * t;
        jobs[t].end = t + 1 == THREADS ? HI : LO + step * (t + 1) - 1;
        pthread_create(&tids[t], NULL, run, &jobs[t]);
    }
    uint64_t hist[65] = {0}, exact = 0;
    int overflow = 0;
    for (unsigned t = 0; t < THREADS; ++t) {
        pthread_join(tids[t], NULL);
        for (int i = 0; i <= 64; ++i) hist[i] += jobs[t].hist[i];
        exact += jobs[t].exact_hits;
        overflow |= jobs[t].overflow;
    }
    printf("{\"base\":%u,\"lo\":\"", B); print_u128(stdout, LO);
    printf("\",\"hi\":\""); print_u128(stdout, HI);
    printf("\",\"square_digits\":%u,\"cube_digits\":%u,\"mult\":%u,\"overflow\":%d,\"histogram\":[", L2, L3, MULT, overflow);
    for (unsigned i = 0; i <= B; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)hist[i]);
    printf("],\"exact_hits\":%llu,\"hits\":[", (unsigned long long)exact);
    int first = 1;
    for (unsigned t = 0; t < THREADS; ++t)
        for (unsigned i = 0; i < jobs[t].nhits; ++i) {
            printf("%s\"", first ? "" : ","); print_u128(stdout, jobs[t].hits[i]); printf("\"");
            first = 0;
        }
    printf("],\"reported\":[");
    first = 1;
    for (unsigned t = 0; t < THREADS; ++t)
        for (unsigned i = 0; i < jobs[t].nreported; ++i) {
            printf("%s[\"", first ? "" : ","); print_u128(stdout, jobs[t].reported[i]);
            printf("\",%u]", jobs[t].reported_distinct[i]);
            first = 0;
        }
    printf("]}\n");
    return overflow ? 6 : 0;
}
