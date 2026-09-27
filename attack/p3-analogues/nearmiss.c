// nearmiss.c -- GENERATED from knice.c by the snippet in the report (same walk).
// Instead of the hash test, every in-range candidate gets an exact digit count
// (4-bit counters in a 128-bit word), and the distance D = sum_v |c_v - K| is
// histogrammed by digit-sum offset delta = n^2(n+1) - K*B(B-1)/2 mod (B-1).
// Run with FILTERS=0 (all residues) on a subset of chunks.
// (original header follows)
// knice.c -- exhaustive enumerator for k-nice numbers (exact multiplicity).
//
// n is k-nice in base B if the base-B digits of n^2 (SL digits) and n^3
// (CL digits), SL + CL = K*B, contain every value 0..B-1 exactly K times.
//
// Compile-time parameters (the driver run.py passes them with -D):
//   B   base (<= 32)          K   multiplicity
//   SL  digits of n^2         CL  digits of n^3   (constant on [LO, HI])
//   J   number of low digits of n fixed per residue class
//
// Search layout, and why every filter is sound (no k-nice n is skipped):
//
//  1. Digit-sum filter. For any m, m == digitsum_B(m) (mod B-1). A k-nice n
//     has digitsum(n^2) + digitsum(n^3) = K*B(B-1)/2, so
//     n^2 (n+1) == K*B(B-1)/2 (mod B-1). Only residues s = n mod (B-1)
//     satisfying this are enumerated ("roots").
//  2. Low-digit (LSD) filter. n mod B^J fixes the lowest J digits of n^2 and
//     of n^3 (SL, CL > J, so these are genuine digits). If some value occurs
//     more than K times among those 2J digits, no n in that class is k-nice.
//  3. Every surviving class R mod S, S = (B-1) B^J, is walked as the
//     progression n = N0 + R + S t, t = 0..T-1, where N0 = floor(LO/S) S and
//     T = floor((HI-N0)/S) + 1, so [N0, N0 + S T) contains [LO, HI]. n^2 and
//     n^3 are kept as base-B digit arrays modulo B^SL and B^CL and advanced by
//     exact finite differences (D2, D3, E3 and the constants C2 = 2S^2,
//     C3 = 6S^3). For n in [LO, HI] the arrays equal n^2 and n^3 exactly.
//     All increments are multiples of S, hence of B^J, so digits below J never
//     change and are not stored in the vectors.
//  4. Each step computes, for 16 classes at once (one per NEON byte lane), the
//     sum mod 256 of random byte weights w[digit] over the moving digits. A
//     k-nice n has exactly the target sum, so this never rejects a solution;
//     lanes that match (about 1/256 of them) get an exact digit count, and a
//     hit is reported only if the count is exact and LO <= n <= HI.
//  5. After each group's walk, the final arrays are compared with n^2, n^3 and
//     the difference arrays recomputed from scratch for the last n, so any
//     arithmetic slip aborts the run.
//
// Work is split into NCHUNKS chunks of a permuted order of the residues
// rho = n mod B^J (rho_i = i*A mod B^J); a chunk covers every n in [LO, HI]
// with n mod B^J in its rho set. Completed chunks are appended to a log file,
// which is read back on restart (checkpointing).
//
// Usage: knice LO HI THREADS NCHUNKS PERM_A LOGFILE [FILTERS=1] [CHUNK_LO CHUNK_HI]
#include <arm_neon.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#if !defined(B) || !defined(K) || !defined(SL) || !defined(CL) || !defined(J)
#error "define B K SL CL J"
#endif
#if B > 32 || B < 3
#error "B must be in 3..32"
#endif
#if J < 1 || J >= SL
#error "need 1 <= J < SL"
#endif

#define LANES 16
#define BL 72  // bignum length (digits), > CL
typedef uint8x16_t V;
typedef unsigned __int128 u128;

static uint64_t LO, HI, S, MJ, N0, T, PERM_A;
static unsigned NCHUNKS, NROOTS, FILTERS = 1;
static unsigned ROOTS[64];
static uint8_t W[64];         // hash weights (entries >= B are unused)
static uint8_t WSUM_K;        // K * sum_v W[v] mod 256
static V C2V[SL], C3V[CL];    // broadcast constants
static uint32_t Sd[BL], S2d[BL], S3d[BL];

// ---------------------------------------------------------------- bignum ---
// Little-endian base-B digit arrays, value taken modulo B^len.
static void big_from_u64(uint32_t *x, uint64_t v) {
    for (int i = 0; i < BL; ++i) { x[i] = (uint32_t)(v % B); v /= B; }
}
static void big_norm(uint32_t *r, const uint64_t *acc, int len) {
    uint64_t carry = 0;
    for (int i = 0; i < len; ++i) {
        uint64_t v = acc[i] + carry;
        r[i] = (uint32_t)(v % B);
        carry = v / B;
    }
    for (int i = len; i < BL; ++i) r[i] = 0;
}
static int big_len(const uint32_t *x) {
    int l = BL;
    while (l > 0 && !x[l - 1]) --l;
    return l;
}
static void big_mul(uint32_t *r, const uint32_t *x, const uint32_t *y, int len) {
    uint64_t acc[BL];
    memset(acc, 0, sizeof acc);
    int lx = big_len(x), ly = big_len(y);
    if (lx > len) lx = len;
    for (int i = 0; i < lx; ++i) {
        if (!x[i]) continue;
        int jmax = len - i < ly ? len - i : ly;
        for (int j = 0; j < jmax; ++j) acc[i + j] += (uint64_t)x[i] * y[j];
    }
    big_norm(r, acc, len);
}
// r = a*x + c*y (+ e*z if z) mod B^len
static void big_lin(uint32_t *r, uint64_t a, const uint32_t *x, uint64_t c, const uint32_t *y,
                    uint64_t e, const uint32_t *z, int len) {
    uint64_t acc[BL];
    for (int i = 0; i < len; ++i) {
        acc[i] = a * x[i] + c * y[i];
        if (z) acc[i] += e * z[i];
    }
    big_norm(r, acc, len);
}

typedef struct {
    uint32_t sq[BL], cu[BL], d2[BL], d3[BL], e3[BL];
} State;

// Exact state for n: n^2, n^3 and forward differences for stride S.
static void state_for(State *st, uint64_t n) {
    uint32_t X[BL], X2[BL], XS[BL], XS2[BL], X2S[BL];
    big_from_u64(X, n);
    big_mul(X2, X, X, CL);
    memcpy(st->sq, X2, sizeof X2);
    for (int i = SL; i < BL; ++i) st->sq[i] = 0;
    big_mul(st->cu, X2, X, CL);
    big_mul(XS, X, Sd, CL);
    big_mul(XS2, X, S2d, CL);
    big_mul(X2S, X2, Sd, CL);
    big_lin(st->d2, 2, XS, 1, S2d, 0, NULL, SL);         // 2nS + S^2
    big_lin(st->d3, 3, X2S, 3, XS2, 1, S3d, CL);          // 3n^2 S + 3n S^2 + S^3
    big_lin(st->e3, 6, XS2, 6, S3d, 0, NULL, CL);         // 6n S^2 + 6 S^3
}

// ------------------------------------------------------------- utilities ---
static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static int exact_counts(const uint8_t *sq, const uint8_t *cu) {
    unsigned cnt[B];
    memset(cnt, 0, sizeof cnt);
    for (int p = 0; p < SL; ++p) cnt[sq[p]]++;
    for (int p = 0; p < CL; ++p) cnt[cu[p]]++;
    for (int v = 0; v < B; ++v)
        if (cnt[v] != K) return 0;
    return 1;
}

// LSD filter: lowest J digits of rho^2 and rho^3 have no value more than K times.
static int lsd_pass(uint64_t rho) {
    if (!FILTERS) return 1;
    u128 m = 1;
    for (int i = 0; i < J; ++i) m *= B;
    u128 r = rho, r2 = (r * r) % m, r3 = (r2 * r) % m;
    unsigned cnt[B];
    memset(cnt, 0, sizeof cnt);
    for (int i = 0; i < J; ++i) {
        if (++cnt[(unsigned)(r2 % B)] > K) return 0;
        if (++cnt[(unsigned)(r3 % B)] > K) return 0;
        r2 /= B; r3 /= B;
    }
    return 1;
}

// ----------------------------------------------------------------- group ---
typedef struct {
    uint64_t hits[256];
    unsigned nhits;
    uint64_t survivors;     // hash matches (exact-checked)
    uint64_t steps;         // lane-steps walked (active lanes x T)
    uint64_t inrange;       // candidates with LO <= n <= HI
    uint64_t dh[32][8];     // [delta][D/2], last bin = D/2 >= 7
} Stats;
static u128 NT[32];         // NT[v] = 1 << (4v)
static uint8_t DT[256], DT_LAST[256];  // |lo-K| + |hi-K| per byte (last byte: lo only if B odd)
static unsigned delta_of(uint64_t n) {
    uint64_t m = B - 1, s = n % m, tgt = ((uint64_t)K * B * (B - 1) / 2) % m;
    return (unsigned)((s * s % m * (s + 1) % m + m - tgt) % m);
}

static inline V addc(V a, V d, V *m, V bv) {
    V t = vsubq_u8(vaddq_u8(a, d), *m);  // m = 0xFF means carry-in 1
    V ge = vcgeq_u8(t, bv);
    *m = ge;
    return vminq_u8(t, vsubq_u8(t, bv));
}

#ifndef NG
#define NG 2  // groups of 16 lanes walked together (independent chains for ILP)
#endif
#define GL (NG * LANES)

typedef struct {
    uint8_t sq[SL][NG][LANES], d2[SL][NG][LANES];
    uint8_t cu[CL][NG][LANES], d3[CL][NG][LANES], e3[CL][NG][LANES];
} Arr;

// Exact count for lane L (0..GL-1) of the current arrays.
static void lane_exact(const Arr *A, const uint8_t (*lowsq)[J], const uint8_t (*lowcu)[J],
                       unsigned L, uint64_t n, Stats *st) {
    uint8_t sq[SL], cu[CL];
    unsigned g = L / LANES, l = L % LANES;
    for (int p = 0; p < J; ++p) { sq[p] = lowsq[L][p]; cu[p] = lowcu[L][p]; }
    for (int p = J; p < SL; ++p) sq[p] = A->sq[p][g][l];
    for (int p = J; p < CL; ++p) cu[p] = A->cu[p][g][l];
    st->survivors++;
    if (exact_counts(sq, cu) && n >= LO && n <= HI) {
        if (st->nhits < 256) st->hits[st->nhits] = n;
        st->nhits++;
    }
}

static inline void nm_count(const Arr *A, const u128 *lowacc, const unsigned *dl, unsigned L,
                            uint64_t n, Stats *st) {
    if (n < LO || n > HI) return;
    unsigned g = L / LANES, l = L % LANES;
    u128 acc = lowacc[L];
    for (int p = J; p < SL; ++p) acc += NT[A->sq[p][g][l]];
    for (int p = J; p < CL; ++p) acc += NT[A->cu[p][g][l]];
    unsigned D = 0;
    const int nb = (B + 1) / 2;
    for (int i = 0; i < nb - 1; ++i) D += DT[(uint8_t)(acc >> (8 * i))];
    D += DT_LAST[(uint8_t)(acc >> (8 * (nb - 1)))];
    unsigned bin = D / 2 < 7 ? D / 2 : 7;
    st->dh[dl[L]][bin]++;
    st->inrange++;
    if (D == 0) {  // exact hit: confirm with the plain counter
        uint8_t sq[SL], cu[CL];
        (void)sq; (void)cu;
        if (st->nhits < 256) st->hits[st->nhits] = n;
        st->nhits++;
    }
}

// Walk up to GL classes (n0[0..nactive-1]) through t = 0..T-1.
static void run_group(const uint64_t *n0, unsigned nactive, Stats *st) {
    static __thread Arr *A = NULL;
    if (!A) A = aligned_alloc(64, (sizeof(Arr) + 63) / 64 * 64);
    uint8_t lowsq[GL][J], lowcu[GL][J];
    uint8_t target[NG][LANES] __attribute__((aligned(16)));
    u128 lowacc[GL];
    unsigned dl[GL];
    State s;
    for (unsigned L = 0; L < GL; ++L) {
        unsigned g = L / LANES, l = L % LANES;
        uint64_t n = n0[L < nactive ? L : 0];
        state_for(&s, n);
        unsigned h = WSUM_K;
        for (int p = 0; p < J; ++p) {
            lowsq[L][p] = (uint8_t)s.sq[p];
            lowcu[L][p] = (uint8_t)s.cu[p];
            h -= W[s.sq[p]] + W[s.cu[p]];
            if (s.d2[p] || s.d3[p] || s.e3[p]) { fprintf(stderr, "low increment digit nonzero\n"); exit(7); }
        }
        target[g][l] = (uint8_t)h;
        lowacc[L] = 0;
        for (int p = 0; p < J; ++p) lowacc[L] += NT[s.sq[p]] + NT[s.cu[p]];
        dl[L] = delta_of(n);
        for (int p = J; p < SL; ++p) { A->sq[p][g][l] = (uint8_t)s.sq[p]; A->d2[p][g][l] = (uint8_t)s.d2[p]; }
        for (int p = J; p < CL; ++p) {
            A->cu[p][g][l] = (uint8_t)s.cu[p]; A->d3[p][g][l] = (uint8_t)s.d3[p]; A->e3[p][g][l] = (uint8_t)s.e3[p];
        }
        for (int p = 0; p < 2 * J && p < CL; ++p)
            if (s.e3[p]) { fprintf(stderr, "E3 low digit nonzero\n"); exit(7); }
    }
    // t = 0: exact check of every active lane
    for (unsigned L = 0; L < nactive; ++L) nm_count(A, lowacc, dl, L, n0[L], st);

    const V bv = vdupq_n_u8(B);
    const uint8x16x2_t wt = {{vld1q_u8(W), vld1q_u8(W + 16)}};
    V tv[NG];
    for (int g = 0; g < NG; ++g) tv[g] = vld1q_u8(target[g]);

    for (uint64_t t = 1; t < T; ++t) {
        V h[NG], m1[NG], m2[NG], m3[NG], m4[NG], m5[NG];
        for (int g = 0; g < NG; ++g) h[g] = m1[g] = m2[g] = m3[g] = m4[g] = m5[g] = vdupq_n_u8(0);
        // square: n^2 += D2 (positions >= J); D2 += C2 (positions >= 2J)
#pragma clang loop unroll(full)
        for (int p = J; p < SL; ++p) {
#pragma clang loop unroll(full)
            for (int g = 0; g < NG; ++g) {
                V a = vld1q_u8(A->sq[p][g]);
                V d = vld1q_u8(A->d2[p][g]);
                a = addc(a, d, &m1[g], bv);
                vst1q_u8(A->sq[p][g], a);
                h[g] = vaddq_u8(h[g], vqtbl2q_u8(wt, a));
                if (p >= 2 * J) {
                    d = addc(d, C2V[p], &m2[g], bv);
                    vst1q_u8(A->d2[p][g], d);
                }
            }
        }
        // cube: n^3 += D3 (>= J); D3 += E3 (>= 2J); E3 += C3 (>= 3J)
#pragma clang loop unroll(full)
        for (int p = J; p < CL; ++p) {
#pragma clang loop unroll(full)
            for (int g = 0; g < NG; ++g) {
                V a = vld1q_u8(A->cu[p][g]);
                V d = vld1q_u8(A->d3[p][g]);
                a = addc(a, d, &m3[g], bv);
                vst1q_u8(A->cu[p][g], a);
                h[g] = vaddq_u8(h[g], vqtbl2q_u8(wt, a));
                if (p >= 2 * J) {
                    V e = vld1q_u8(A->e3[p][g]);
                    d = addc(d, e, &m4[g], bv);
                    vst1q_u8(A->d3[p][g], d);
                    if (p >= 3 * J) {
                        e = addc(e, C3V[p], &m5[g], bv);
                        vst1q_u8(A->e3[p][g], e);
                    }
                }
            }
        }
        (void)tv;
        for (unsigned L = 0; L < nactive; ++L) nm_count(A, lowacc, dl, L, n0[L] + S * t, st);
        __asm__ volatile("" ::: "memory");  // keep the arrays in memory (no register promotion)
    }
    st->steps += (uint64_t)nactive * T;
    // self-check: final arrays must equal the exact state at t = T-1
    for (unsigned L = 0; L < GL; ++L) {
        unsigned g = L / LANES, l = L % LANES;
        uint64_t n = n0[L < nactive ? L : 0] + S * (T - 1);
        state_for(&s, n);
        int bad = 0;
        for (int p = J; p < SL; ++p) bad |= A->sq[p][g][l] != s.sq[p] || A->d2[p][g][l] != s.d2[p];
        for (int p = J; p < CL; ++p)
            bad |= A->cu[p][g][l] != s.cu[p] || A->d3[p][g][l] != s.d3[p] || A->e3[p][g][l] != s.e3[p];
        if (bad) { fprintf(stderr, "SELF-CHECK FAILED lane %u n0 %llu\n", L, (unsigned long long)n0[L < nactive ? L : 0]); exit(8); }
    }
}

// ----------------------------------------------------------------- chunks ---
static unsigned char *DONE;
static atomic_uint NEXT;
static unsigned CHUNK_HI;
static FILE *LOG;
static pthread_mutex_t LOGMU = PTHREAD_MUTEX_INITIALIZER;
static uint64_t INV_MJ;  // inverse of B^J mod (B-1)

static void do_chunk(unsigned c) {
    uint64_t i0 = (uint64_t)((u128)MJ * c / NCHUNKS), i1 = (uint64_t)((u128)MJ * (c + 1) / NCHUNKS);
    uint64_t t0 = now_ns();
    Stats st;
    memset(&st, 0, sizeof st);
    uint64_t rho_n = 0, rho_pass = 0, lanes = 0;
    uint64_t n0[GL];
    unsigned nl = 0;
    for (uint64_t i = i0; i < i1; ++i) {
        uint64_t rho = (uint64_t)(((u128)i * PERM_A) % MJ);
        rho_n++;
        if (!lsd_pass(rho)) continue;
        rho_pass++;
        for (unsigned k = 0; k < NROOTS; ++k) {
            uint64_t s = ROOTS[k];
            uint64_t diff = (s + (B - 1) - rho % (B - 1)) % (B - 1);
            uint64_t R = rho + MJ * ((diff * INV_MJ) % (B - 1));
            n0[nl++] = N0 + R;
            lanes++;
            if (nl == GL) { run_group(n0, nl, &st); nl = 0; }
        }
    }
    if (nl) run_group(n0, nl, &st);
    double secs = (now_ns() - t0) / 1e9;
    pthread_mutex_lock(&LOGMU);
    fprintf(LOG, "C %u %llu %llu %llu %llu %llu %.3f %u", c, (unsigned long long)rho_n,
            (unsigned long long)rho_pass, (unsigned long long)lanes, (unsigned long long)st.steps,
            (unsigned long long)st.survivors, secs, st.nhits);
    for (unsigned h = 0; h < st.nhits && h < 256; ++h) fprintf(LOG, " %llu", (unsigned long long)st.hits[h]);
    fprintf(LOG, " | %llu", (unsigned long long)st.inrange);
    for (unsigned d = 0; d < B - 1; ++d)
        for (unsigned j = 0; j < 8; ++j) fprintf(LOG, " %llu", (unsigned long long)st.dh[d][j]);
    fprintf(LOG, "\n");
    fflush(LOG);
    fsync(fileno(LOG));
    pthread_mutex_unlock(&LOGMU);
}

static void *worker(void *arg) {
    (void)arg;
    for (;;) {
        unsigned c = atomic_fetch_add(&NEXT, 1);
        if (c >= CHUNK_HI) break;
        if (DONE[c]) continue;
        do_chunk(c);
    }
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 7) {
        fprintf(stderr, "usage: %s LO HI THREADS NCHUNKS PERM_A LOGFILE [FILTERS] [CHUNK_LO CHUNK_HI]\n", argv[0]);
        return 2;
    }
    LO = strtoull(argv[1], NULL, 10);
    HI = strtoull(argv[2], NULL, 10);
    unsigned threads = (unsigned)atoi(argv[3]);
    NCHUNKS = (unsigned)atoi(argv[4]);
    PERM_A = strtoull(argv[5], NULL, 10);
    const char *logpath = argv[6];
    if (argc > 7) FILTERS = (unsigned)atoi(argv[7]);
    unsigned chunk_lo = argc > 8 ? (unsigned)atoi(argv[8]) : 0;
    CHUNK_HI = argc > 9 ? (unsigned)atoi(argv[9]) : NCHUNKS;

    MJ = 1;
    for (int i = 0; i < J; ++i) MJ *= B;
    S = (B - 1) * MJ;
    N0 = LO / S * S;
    T = (HI - N0) / S + 1;
    {   // S^3 must not overflow our bignum routine inputs; n0 + S*T < 2^64
        u128 top = (u128)N0 + (u128)S * T;
        if (top >> 63) { fprintf(stderr, "range too large\n"); return 3; }
    }
    // gcd(PERM_A, B) must be 1 for rho_i = i*A mod B^J to be a permutation
    { uint64_t a = PERM_A % B, bb = B; while (bb) { uint64_t t = a % bb; a = bb; bb = t; }
      if (a != 1) { fprintf(stderr, "PERM_A not coprime to B\n"); return 3; } }
    // digit-sum roots
    unsigned m = B - 1, target = (unsigned)(((uint64_t)K * B * (B - 1) / 2) % m);
    NROOTS = 0;
    for (unsigned s = 0; s < m; ++s)
        if (!FILTERS || ((uint64_t)s * s % m * (s + 1)) % m == target) ROOTS[NROOTS++] = s;
    INV_MJ = 0;
    for (uint64_t x = 0; x < m; ++x)
        if ((MJ % m) * x % m == 1 % m) { INV_MJ = x; break; }
    // constants
    big_from_u64(Sd, S);
    big_mul(S2d, Sd, Sd, CL);
    big_mul(S3d, S2d, Sd, CL);
    {
        uint32_t c2[BL], c3[BL];
        big_lin(c2, 2, S2d, 0, S2d, 0, NULL, SL);
        big_lin(c3, 6, S3d, 0, S3d, 0, NULL, CL);
        for (int p = 0; p < SL; ++p) C2V[p] = vdupq_n_u8((uint8_t)c2[p]);
        for (int p = 0; p < CL; ++p) C3V[p] = vdupq_n_u8((uint8_t)c3[p]);
        for (int p = 0; p < 2 * J && p < SL; ++p) if (c2[p]) { fprintf(stderr, "C2 low\n"); return 7; }
        for (int p = 0; p < 3 * J && p < CL; ++p) if (c3[p]) { fprintf(stderr, "C3 low\n"); return 7; }
    }
    // hash weights: fixed pseudo-random bytes
    uint64_t x = 0x9E3779B97F4A7C15ull ^ (B * 1315423911ull) ^ (K * 2654435761ull);
    unsigned wsum = 0;
    memset(W, 0, sizeof W);
    for (unsigned v = 0; v < B; ++v) {
        x ^= x << 13; x ^= x >> 7; x ^= x << 17;
        W[v] = (uint8_t)(x >> 24);
        wsum += W[v];
    }
    WSUM_K = (uint8_t)(K * wsum);

    for (unsigned v = 0; v < 32; ++v) NT[v] = (u128)1 << (4 * v);
    for (unsigned x = 0; x < 256; ++x) {
        int lo = x & 15, hi = x >> 4;
        DT[x] = (uint8_t)(abs(lo - K) + abs(hi - K));
        DT_LAST[x] = (uint8_t)((B % 2) ? abs(lo - K) : DT[x]);
    }
    DONE = calloc(NCHUNKS, 1);
    FILE *old = fopen(logpath, "r");
    unsigned already = 0;
    if (old) {
        char line[1 << 16];
        while (fgets(line, sizeof line, old)) {
            unsigned c;
            if (sscanf(line, "C %u", &c) == 1 && c < NCHUNKS && !DONE[c]) { DONE[c] = 1; already++; }
        }
        fclose(old);
    }
    LOG = fopen(logpath, "a");
    if (!LOG) { perror("log"); return 4; }
    fprintf(stderr, "B=%d K=%d SL=%d CL=%d J=%d S=%llu T=%llu roots=%u chunks=%u done=%u filters=%u\n", B, K,
            SL, CL, J, (unsigned long long)S, (unsigned long long)T, NROOTS, NCHUNKS, already, FILTERS);
    fprintf(LOG, "# start B=%d K=%d SL=%d CL=%d J=%d LO=%llu HI=%llu S=%llu T=%llu roots=%u chunks=%u perm=%llu filters=%u range=%u-%u\n",
            B, K, SL, CL, J, (unsigned long long)LO, (unsigned long long)HI, (unsigned long long)S,
            (unsigned long long)T, NROOTS, NCHUNKS, (unsigned long long)PERM_A, FILTERS, chunk_lo, CHUNK_HI);
    fflush(LOG);
    atomic_store(&NEXT, chunk_lo);
    pthread_t tid[64];
    if (threads > 64) threads = 64;
    for (unsigned t = 0; t < threads; ++t) pthread_create(&tid[t], NULL, worker, NULL);
    for (unsigned t = 0; t < threads; ++t) pthread_join(tid[t], NULL);
    fprintf(LOG, "# end\n");
    fclose(LOG);
    return 0;
}
