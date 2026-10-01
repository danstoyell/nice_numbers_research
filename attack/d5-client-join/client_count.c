// client_count.c -- faithful reimplementation of the public client's CPU
// niceonly search path (wasabipesto/nice, commit fe1b0b8, v3.4.5+), with
// operation counters, generalized to k-nice (multiplicity K) for the testbed.
// The ported client logic is Copyright (c) 2024 wasabipesto, used under the
// MIT License of https://github.com/wasabipesto/nice (see LICENSE there).
//
// Pipeline per chunk (client/src/main.rs, common/src/client_process.rs):
//   1. MSD recursion (msd_prefix_filter::get_valid_ranges_recursive_masked):
//      binary subdivision, max depth 22, floor FLOOR; every node larger than
//      FLOOR is analysed (analyze_range: interval digit domains of the top
//      output positions of n^2 and n^3 from the endpoint powers, Hall check);
//      rejected nodes are dropped; nodes smaller than 2*FLOOR are emitted as
//      leaves with the union of ancestor certificates (singleton digits at
//      output positions >= LSDK).
//   2. Stride iteration (stride_filter::iterate_range_masked): CRT table mod
//      (b-1)*b^LSDK of residues passing the digit-sum filter and the LSDK-digit
//      LSD filter; each candidate costs one AND of its exact low-digit mask
//      with the leaf certificate (cross-end residue filter); survivors get the
//      seeded full check.
// K > 1 generalization (the client itself is K = 1 only): Hall with capacity
// K per digit, counts instead of masks (2-bit fields), LSD filter "no value
// more than K times", digit-sum target K*b(b-1)/2 mod (b-1). For K = 1 every
// step is bit-for-bit the client's.
//
// Build: clang -O3 -o client_count client_count.c -lpthread            (b<=40 nice)
//        clang -O3 -DW256 -o client_count256 client_count.c -lpthread (b<=64)
// Run:   ./client_count range  B K LO HI_EXCL ORIGIN CHUNK FLOOR THREADS FULL
//        ./client_count sample B K LO HI_EXCL ORIGIN CHUNK FLOOR THREADS FULL NSAMPLES SEED
//   range : process [LO, HI_EXCL) cut into chunks of CHUNK aligned at ORIGIN.
//   sample: NSAMPLES stratified random aligned chunks of [LO, HI_EXCL).
//   FULL=0 counts full checks without running them.
// Output: one JSON line of counters (and hits).
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned __int128 u128;
typedef uint64_t u64;
typedef uint32_t u32;
typedef uint8_t u8;

#define LSDK 3
#define MAXDEPTH 22
#define MAXDIG 80
#define HALLMAX (2 * 38 + 2)

static u32 B, K;
static u128 FLOOR, CHUNK;
static int FULL;
static u64 CH64; static unsigned CHD;   // b^CHD < 2^64 (digit-extraction chunk)
static u64 BK;                          // b^LSDK

// ---------------------------------------------------------------- wide ints
#ifdef W256
typedef struct { u64 w[4]; } W;
static inline W w_from_u128(u128 a) { W r = {{(u64)a, (u64)(a >> 64), 0, 0}}; return r; }
static inline W w_mul_u128(u128 a, u128 b) {
    u64 a0 = (u64)a, a1 = (u64)(a >> 64), b0 = (u64)b, b1 = (u64)(b >> 64);
    u128 p00 = (u128)a0 * b0, p01 = (u128)a0 * b1, p10 = (u128)a1 * b0, p11 = (u128)a1 * b1;
    W r; r.w[0] = (u64)p00;
    u128 mid = (p00 >> 64) + (u64)p01 + (u64)p10;
    r.w[1] = (u64)mid;
    u128 hi = (mid >> 64) + (p01 >> 64) + (p10 >> 64) + (u64)p11;
    r.w[2] = (u64)hi;
    r.w[3] = (u64)((hi >> 64) + (p11 >> 64));
    return r;
}
static inline W w_mul_w_u128(W a, u128 b) {   // truncating to 256 bits
    u64 b0 = (u64)b, b1 = (u64)(b >> 64);
    W r = {{0, 0, 0, 0}};
    u128 c = 0;
    for (int i = 0; i < 4; ++i) { c += (u128)a.w[i] * b0 + r.w[i]; r.w[i] = (u64)c; c >>= 64; }
    c = 0;
    for (int i = 0; i + 1 < 4; ++i) { c += (u128)a.w[i] * b1 + r.w[i + 1]; r.w[i + 1] = (u64)c; c >>= 64; }
    return r;
}
static inline int w_zero(W a) { return !(a.w[0] | a.w[1] | a.w[2] | a.w[3]); }
static inline u64 w_divrem(W *a, u64 d) {      // d < 2^64
    u128 r = 0;
    for (int i = 3; i >= 0; --i) { u128 cur = (r << 64) | a->w[i]; a->w[i] = (u64)(cur / d); r = cur % d; }
    return (u64)r;
}
static inline int w_fits128(W a) { return !(a.w[2] | a.w[3]); }
static inline u128 w_lo128(W a) { return ((u128)a.w[1] << 64) | a.w[0]; }
#else
typedef u128 W;
static inline W w_from_u128(u128 a) { return a; }
static inline W w_mul_u128(u128 a, u128 b) { return a * b; }
static inline W w_mul_w_u128(W a, u128 b) { return a * b; }
#endif

// digits of a u64 chunk: exactly nd digits (nd<0: until zero)
static inline int dig_u64(u64 x, int nd, u8 *out) {
    int n = 0;
    if (nd < 0) { do { out[n++] = (u8)(x % B); x /= B; } while (x); }
    else for (; n < nd; ++n) { out[n] = (u8)(x % B); x /= B; }
    return n;
}
// all digits of x (LSD first); x==0 -> one digit 0
static int digits_of(W x, u8 *out) {
    int n = 0;
#ifdef W256
    while (!w_fits128(x)) { u64 r = w_divrem(&x, CH64); n += dig_u64(r, (int)CHD, out + n); }
    u128 y = w_lo128(x);
#else
    u128 y = x;
#endif
    while (y >> 64) { u128 q = y / CH64; u64 r = (u64)(y - q * CH64); n += dig_u64(r, (int)CHD, out + n); y = q; }
    n += dig_u64((u64)y, -1, out + n);
    return n;
}

// ---------------------------------------------------------------- counts (K>=2)
static const u64 M33 = 0x3333333333333333ULL, H88 = 0x8888888888888888ULL;
static u64 ADDK;
static inline int cnt_ok(u64 a, u64 c) {           // every 2-bit field a_d + c_d <= K
    if (K == 1) return (a & c) == 0;
    u64 e = (a & M33) + (c & M33), o = ((a >> 2) & M33) + ((c >> 2) & M33);
    return (((e + ADDK) | (o + ADDK)) & H88) == 0;
}
static inline u64 cnt_max(u64 a, u64 c) {          // elementwise max (certificate union)
    if (K == 1) return a | c;
    u64 r = 0;
    for (u32 d = 0; d < B; ++d) { u64 x = (a >> (2 * d)) & 3, y = (c >> (2 * d)) & 3; r |= (x > y ? x : y) << (2 * d); }
    return r;
}
static inline unsigned cnt_total(u64 a) {
    if (K == 1) return (unsigned)__builtin_popcountll(a);
    unsigned s = 0; for (u32 d = 0; d < B; ++d) s += (a >> (2 * d)) & 3; return s;
}

// ---------------------------------------------------------------- counters
typedef struct {
    u64 chunks, analyses, rejected_nodes, leaves;
    u128 rejected_n, leaf_n;
    u64 msd_digits, hall_calls;           // digit extractions in analyses, augment calls
    u64 visits, mask_rejects, full_checks, full_digits;
    double cert_sum;                      // sum over visits of certified high singletons
    double dom_sum;                       // sum over visits of constrained high positions
    u64 hits; u64 hitv[4096]; unsigned nh;
    // sample-mode moments (per chunk)
    double s_ops, s_ops2;
} Ctr;

// ---------------------------------------------------------------- Hall / analysis
static int hall_augment(int i, const u64 *doms, u64 *visited, int *owner, u64 *calls) {
    (*calls)++;
    u64 cand = doms[i] & ~*visited;
    while (cand) {
        int d = __builtin_ctzll(cand);
        *visited |= 1ULL << d;
        if (owner[d] < 0 || hall_augment(owner[d], doms, visited, owner, calls)) { owner[d] = i; return 1; }
        cand = doms[i] & ~*visited;
    }
    return 0;
}
static int has_distinct_assignment(const u64 *doms, int m, u64 *calls) {
    if (m <= 1) return 1;
    u64 uni = 0;
    for (int i = 0; i < m; ++i) uni |= doms[i];
    if (__builtin_popcountll(uni) < m) return 0;
    int owner[64];
    for (int i = 0; i < 64; ++i) owner[i] = -1;
    for (int i = 0; i < m; ++i) { u64 vis = 0; if (!hall_augment(i, doms, &vis, owner, calls)) return 0; }
    return 1;
}
// cyclic interval of `size` slots starting at `lo` in a ring of `ring` slots
static inline u64 cyc_mask(unsigned lo, unsigned size, unsigned ring) {
    if (lo + size <= ring) return (u64)((((u128)1 << size) - 1) << lo);
    unsigned wrapped = lo + size - ring;
    return (u64)(((((u128)1 << (ring - lo)) - 1) << lo) | (((u128)1 << wrapped) - 1));
}
// collect_power_domains, K-generalized: domains in "slot" space (digit d ->
// slots d*K..d*K+K-1); `fixed` gets singleton digits at positions >= LSDK
static void collect_power_domains(const u8 *xd, const u8 *yd, int len, u64 *doms, int *count, u64 *fixed, unsigned *ndom) {
    long diff = 0;
    for (int j = len - 1; j >= 0; --j) {
        if (*count == HALLMAX) return;
        diff = diff * (long)B + ((long)yd[j] - (long)xd[j]);
        if (diff >= (long)B - 1) return;
        if (diff == 0 && j >= LSDK) {
            if (K == 1) *fixed |= 1ULL << xd[j];
            else *fixed += 1ULL << (2 * xd[j]);
        }
        unsigned size = (unsigned)diff + 1, lo = xd[j];
        doms[(*count)++] = cyc_mask(lo * K, size * K, B * K);
        (*ndom)++;
    }
}
// analyze_range on [first, last]; returns 0 = rejected, 1 = live (*fixed, *ndom set)
static int analyze_range(u128 first, u128 last, u64 *fixed, unsigned *ndom, Ctr *c) {
    c->analyses++;
    *fixed = 0; *ndom = 0;
    if (first == last) return 1;
    u8 a2[MAXDIG], e2[MAXDIG], a3[MAXDIG], e3[MAXDIG];
    W s2 = w_mul_u128(first, first), t2 = w_mul_u128(last, last);
    W s3 = w_mul_w_u128(s2, first), t3 = w_mul_w_u128(t2, last);
    int la2 = digits_of(s2, a2), le2 = digits_of(t2, e2), la3 = digits_of(s3, a3), le3 = digits_of(t3, e3);
    c->msd_digits += (u64)(la2 + le2 + la3 + le3);
    u64 doms[HALLMAX]; int m = 0; u64 fx = 0;
    if (la2 == le2) collect_power_domains(a2, e2, la2, doms, &m, &fx, ndom);
    if (la3 == le3) collect_power_domains(a3, e3, la3, doms, &m, &fx, ndom);
    if (m == 0) return 1;
    if (has_distinct_assignment(doms, m, &c->hall_calls)) { *fixed = fx; return 1; }
    return 0;
}

// ---------------------------------------------------------------- stride table
static u64 SMOD;              // (b-1) * b^LSDK
static u32 *RES, *GAP; static u64 *LOWM; static size_t NRES;
static void build_stride(void) {
    u32 bm1 = B - 1;
    u64 target = ((u64)K * B * (B - 1) / 2) % bm1;
    u8 *rok = calloc(bm1, 1);
    for (u64 r = 0; r < bm1; ++r) if ((r * r + r * r * r) % bm1 == target) rok[r] = 1;
    u8 *lok = calloc(BK, 1); u64 *lm = calloc(BK, sizeof(u64));
    for (u64 s = 0; s < BK; ++s) {
        u64 v[2] = {(u64)((u128)s * s % BK), (u64)((u128)s * s % BK * s % BK)};
        u64 msk = 0; int ok = 1; unsigned cnt[64] = {0};
        for (int p = 0; p < 2 && ok; ++p) {
            u64 x = v[p];
            for (int i = 0; i < LSDK; ++i) {
                unsigned d = (unsigned)(x % B); x /= B;
                if (++cnt[d] > K) { ok = 0; break; }
                if (K == 1) msk |= 1ULL << d; else msk += 1ULL << (2 * d);
            }
        }
        lok[s] = (u8)ok; lm[s] = msk;
    }
    SMOD = (u64)bm1 * BK;
    size_t cap = 1 << 20; RES = malloc(cap * 4); LOWM = malloc(cap * 8); NRES = 0;
    for (u64 r = 0; r < SMOD; ++r) {
        if (!rok[r % bm1] || !lok[r % BK]) continue;
        if (NRES == cap) { cap *= 2; RES = realloc(RES, cap * 4); LOWM = realloc(LOWM, cap * 8); }
        RES[NRES] = (u32)r; LOWM[NRES] = lm[r % BK]; NRES++;
    }
    GAP = malloc(NRES * 4);
    for (size_t i = 0; i < NRES; ++i) GAP[i] = (i + 1 < NRES) ? RES[i + 1] - RES[i] : (u32)(SMOD - RES[i] + RES[0]);
    free(rok); free(lok); free(lm);
}

// ---------------------------------------------------------------- full check (seeded)
static int full_check_seeded(u128 n, u64 seed, u64 *ndig) {
    W sq = w_mul_u128(n, n), cu = w_mul_w_u128(sq, n);
    u8 dg[MAXDIG];
    if (K == 1) {
        u64 ind = seed;
        for (int p = 0; p < 2; ++p) {
            W x = p ? cu : sq;
            int nd = digits_of(x, dg);
            for (int i = LSDK; i < nd; ++i) {
                (*ndig)++;
                u64 bit = 1ULL << dg[i];
                if (ind & bit) return 0;
                ind |= bit;
            }
        }
        return 1;
    }
    unsigned cnt[64];
    for (u32 d = 0; d < B; ++d) cnt[d] = (unsigned)((seed >> (2 * d)) & 3);
    for (int p = 0; p < 2; ++p) {
        W x = p ? cu : sq;
        int nd = digits_of(x, dg);
        for (int i = LSDK; i < nd; ++i) { (*ndig)++; if (++cnt[dg[i]] > K) return 0; }
    }
    for (u32 d = 0; d < B; ++d) if (cnt[d] != K) return 0;
    return 1;
}

// ---------------------------------------------------------------- stride iteration of one leaf
static void iterate_leaf(u128 start, u128 end, u64 high, unsigned ndom, Ctr *c) {
    u64 r = (u64)(start % SMOD);
    size_t lo = 0, hi = NRES;                     // first residue >= r
    while (lo < hi) { size_t mid = (lo + hi) / 2; if (RES[mid] < r) lo = mid + 1; else hi = mid; }
    size_t idx = lo; u128 n;
    if (idx < NRES) n = start + (RES[idx] - r);
    else { idx = 0; n = start + (SMOD - r + RES[0]); }
    unsigned cert = cnt_total(high);
    u64 v0 = c->visits;
    while (n < end) {
        c->visits++;
        if (!cnt_ok(LOWM[idx], high)) c->mask_rejects++;
        else {
            c->full_checks++;
            if (FULL && full_check_seeded(n, LOWM[idx], &c->full_digits)) {
                if (c->nh < 4096) c->hitv[c->nh++] = (u64)n;
                c->hits++;
            }
        }
        n += GAP[idx];
        if (++idx == NRES) idx = 0;
    }
    double nv = (double)(c->visits - v0);
    c->cert_sum += nv * cert; c->dom_sum += nv * ndom;
}

// get_valid_ranges_recursive_masked + iterate
static void recurse(u128 s, u128 e, unsigned depth, u64 inh, unsigned inh_dom, Ctr *c) {
    u128 size = e - s;
    if (depth >= MAXDEPTH || size <= FLOOR) { c->leaves++; c->leaf_n += size; iterate_leaf(s, e, inh, inh_dom, c); return; }
    u64 fx; unsigned nd;
    if (!analyze_range(s, e - 1, &fx, &nd, c)) { c->rejected_nodes++; c->rejected_n += size; return; }
    u64 mask = cnt_max(inh, fx);
    if (size < FLOOR * 2) { c->leaves++; c->leaf_n += size; iterate_leaf(s, e, mask, nd, c); return; }
    u128 cs = size / 2;
    recurse(s, s + cs, depth + 1, mask, nd, c);
    recurse(s + cs, e, depth + 1, mask, nd, c);
}

// ---------------------------------------------------------------- drivers
static u128 LO, HIX, ORIGIN;
static int SAMPLE; static u64 NSAMP, SEED;
static u128 CH_FIRST; static u64 NCH;          // chunk index range
static atomic_ullong next_job;
static unsigned NTHR;

static u64 rng_state;
static u64 splitmix(u64 *s) { u64 z = (*s += 0x9E3779B97F4A7C15ULL); z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
static u128 *SAMPLE_STARTS;

static void do_chunk(u128 s, u128 e, Ctr *c) {
    c->chunks++;
    u64 before = c->analyses + c->visits + c->full_checks;
    recurse(s, e, 0, 0, 0, c);
    double ops = (double)(c->analyses + c->visits + c->full_checks - before);
    c->s_ops += ops; c->s_ops2 += ops * ops;
}
static void *worker(void *arg) {
    Ctr *c = arg;
    for (;;) {
        u64 j = atomic_fetch_add(&next_job, 1);
        if (SAMPLE) {
            if (j >= NSAMP) break;
            u128 s = SAMPLE_STARTS[j], e = s + CHUNK; if (e > HIX) e = HIX;
            do_chunk(s, e, c);
        } else {
            if (j >= NCH) break;
            u128 s = ORIGIN + (CH_FIRST + j) * CHUNK, e = s + CHUNK;
            if (s < LO) s = LO;
            if (e > HIX) e = HIX;
            if (s < e) do_chunk(s, e, c);
        }
    }
    return NULL;
}
static u128 parse_u128(const char *s) { u128 x = 0; while (*s) x = x * 10 + (u128)(*s++ - '0'); return x; }
static void print_u128(u128 x) { char buf[48]; int i = 47; buf[i] = 0; do { buf[--i] = (char)('0' + (int)(x % 10)); x /= 10; } while (x); printf("%s", buf + i); }
static int cmp_u64(const void *a, const void *b) { u64 x = *(const u64 *)a, y = *(const u64 *)b; return x < y ? -1 : x > y; }

int main(int argc, char **argv) {
    if (argc < 11) { fprintf(stderr, "usage: see header\n"); return 2; }
    SAMPLE = !strcmp(argv[1], "sample");
    B = (u32)atoi(argv[2]); K = (u32)atoi(argv[3]);
    LO = parse_u128(argv[4]); HIX = parse_u128(argv[5]); ORIGIN = parse_u128(argv[6]);
    CHUNK = parse_u128(argv[7]); FLOOR = parse_u128(argv[8]); NTHR = (unsigned)atoi(argv[9]); FULL = atoi(argv[10]);
    if (B > 64 || K < 1 || K > 3 || (K > 1 && B * K > 64) || (K > 1 && B > 32)) { fprintf(stderr, "unsupported b/K\n"); return 2; }
#ifndef W256
    { long double hx = (long double)HIX; if (hx * hx * hx > 3.3e38L) { fprintf(stderr, "u128 overflow: build with -DW256\n"); return 2; } }
#endif
    ADDK = (u64)(7 - K) * 0x1111111111111111ULL;
    CH64 = 1; CHD = 0; while ((u128)CH64 * B < ((u128)1 << 64)) { CH64 *= B; CHD++; }
    BK = 1; for (int i = 0; i < LSDK; ++i) BK *= B;
    build_stride();
    if (SAMPLE) {
        NSAMP = strtoull(argv[11], 0, 10); SEED = strtoull(argv[12], 0, 10); rng_state = SEED;
        // stratified: NSAMP equal strata of the aligned chunk index space
        u128 c0 = (LO - ORIGIN) / CHUNK, c1 = (HIX - 1 - ORIGIN) / CHUNK;   // inclusive
        u128 nch = c1 - c0 + 1;
        SAMPLE_STARTS = malloc(NSAMP * sizeof(u128));
        for (u64 i = 0; i < NSAMP; ++i) {
            u128 a = c0 + nch * i / NSAMP, b2 = c0 + nch * (i + 1) / NSAMP;
            if (b2 <= a) b2 = a + 1;
            u128 r = ((u128)splitmix(&rng_state) << 64 | splitmix(&rng_state)) % (b2 - a);
            u128 ci = a + r, s = ORIGIN + ci * CHUNK;
            if (s < LO) s = LO;
            // fully interior chunks only (edge chunks are partial); clamp
            if (s + CHUNK > HIX) s = HIX - CHUNK;
            SAMPLE_STARTS[i] = s;
        }
    } else {
        CH_FIRST = (LO - ORIGIN) / CHUNK;
        NCH = (u64)((HIX - 1 - ORIGIN) / CHUNK - CH_FIRST + 1);
    }
    atomic_store(&next_job, 0);
    pthread_t th[64]; Ctr *cs = calloc(NTHR, sizeof(Ctr));
    for (unsigned i = 0; i < NTHR; ++i) pthread_create(&th[i], NULL, worker, &cs[i]);
    Ctr t; memset(&t, 0, sizeof t);
    u64 *hv = malloc(4096 * 64 * sizeof(u64)); size_t nh = 0;
    for (unsigned i = 0; i < NTHR; ++i) {
        pthread_join(th[i], NULL);
        Ctr *c = &cs[i];
        t.chunks += c->chunks; t.analyses += c->analyses; t.rejected_nodes += c->rejected_nodes; t.leaves += c->leaves;
        t.rejected_n += c->rejected_n; t.leaf_n += c->leaf_n; t.msd_digits += c->msd_digits; t.hall_calls += c->hall_calls;
        t.visits += c->visits; t.mask_rejects += c->mask_rejects; t.full_checks += c->full_checks; t.full_digits += c->full_digits;
        t.cert_sum += c->cert_sum; t.dom_sum += c->dom_sum; t.hits += c->hits; t.s_ops += c->s_ops; t.s_ops2 += c->s_ops2;
        for (unsigned h = 0; h < c->nh; ++h) hv[nh++] = c->hitv[h];
    }
    qsort(hv, nh, sizeof(u64), cmp_u64);
    printf("{\"mode\":\"%s\",\"base\":%u,\"mult\":%u,\"lsd_k\":%d,\"floor\":", SAMPLE ? "sample" : "range", B, K, LSDK); print_u128(FLOOR);
    printf(",\"chunk\":"); print_u128(CHUNK);
    printf(",\"lo\":"); print_u128(LO); printf(",\"hi_excl\":"); print_u128(HIX);
    printf(",\"stride_modulus\":%llu,\"stride_residues\":%zu,\"chunks\":%llu,\"analyses\":%llu,\"rejected_nodes\":%llu,\"leaves\":%llu,\"rejected_n\":",
           (unsigned long long)SMOD, NRES, (unsigned long long)t.chunks, (unsigned long long)t.analyses, (unsigned long long)t.rejected_nodes, (unsigned long long)t.leaves);
    print_u128(t.rejected_n); printf(",\"leaf_n\":"); print_u128(t.leaf_n);
    printf(",\"msd_digits\":%llu,\"hall_calls\":%llu,\"visits\":%llu,\"mask_rejects\":%llu,\"full_checks\":%llu,\"full_digits\":%llu,"
           "\"cert_per_visit\":%.4f,\"doms_per_visit\":%.4f,\"sum_ops\":%.6e,\"sum_ops2\":%.6e,\"full_run\":%d,\"hits\":%llu,\"solutions\":[",
           (unsigned long long)t.msd_digits, (unsigned long long)t.hall_calls, (unsigned long long)t.visits, (unsigned long long)t.mask_rejects,
           (unsigned long long)t.full_checks, (unsigned long long)t.full_digits, t.visits ? t.cert_sum / t.visits : 0.0, t.visits ? t.dom_sum / t.visits : 0.0,
           t.s_ops, t.s_ops2, FULL, (unsigned long long)t.hits);
    for (size_t i = 0; i < nh; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)hv[i]);
    printf("]}\n");
    return 0;
}
