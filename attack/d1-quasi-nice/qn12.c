// qn12.c -- exact pruned enumeration of (1,2)-nice numbers: n and n^2 together use every
// base-b digit exactly once (len(n) + len(n^2) = b).
//
// Enumeration: n = P * b^(s-t) + M * b^j + U, where
//   P = top t digits of n (distinct, band-intersecting; the leading digits of n^2 that are
//       common to the whole prefix range, at most AP of them, must be distinct and disjoint
//       from P's digits),
//   U = bottom j digits of n (distinct; the bottom j digits of n^2 = U^2 mod b^j must be
//       distinct and disjoint from U's digits),
//   M = the s-t-j middle digits, drawn from the digits not used by P, U or the known digits
//       of n^2; the last middle digit is forced by the digit-sum class
//       n + n^2 == b(b-1)/2 (mod b-1), using n == digitsum(n) (mod b-1).
// Every pruning rule only removes n that violate "n's digits distinct, valid class, top AP /
// bottom j digits of n^2 distinct and disjoint from n's digits", so the leaves are a superset
// of that set and the program also counts, exactly,
//   K(A,J) = #{n in band, valid class : n's s digits + n^2's top A and bottom J digits all distinct}
// for A in AP..AP+2, J in j..j+2. These give the exact-edge model expectation.
//
// Build (base as compile-time constant for fast division):
//   clang -O3 -mcpu=native -DBASE=29 -DHSPLIT=6 -o bin/qn12_b29 qn12.c
// Run: bin/qn12_b29 t j AP chunk nchunks   -> one JSON line on stdout
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned __int128 u128;
typedef uint64_t u64;

#ifndef BASE
#error "define BASE"
#endif
#ifndef HSPLIT
#define HSPLIT 6
#endif
#define b ((u64)BASE)
#define MAXD 64

static int S, C, T, J, AP, MID;
static u64 LO, HI;
static u64 PW[MAXD];  // b^i (only up to what fits)
static int VALID[MAXD];
static u64 BH;        // b^HSPLIT

static u64 isqrt128(u128 x) {
    u64 r = 0;
    // binary search on 64-bit result
    u64 lo = 0, hi = ((u64)1 << 63);
    while (lo < hi) {
        u64 mid = lo + (hi - lo + 1) / 2;
        if ((u128)mid * mid <= x) lo = mid; else hi = mid - 1;
    }
    r = lo;
    return r;
}
static u128 ipow128(int e) { u128 r = 1; while (e--) r *= b; return r; }

static inline int sqdigits(u64 n, int *D) {
    // n^2 in base b, little-endian, exactly C digits; returns number of digits produced
    u64 x = n / BH, y = n % BH;
    u64 y2 = y * y;
    u64 l0 = y2 % BH, cy = y2 / BH;
    u64 t1 = 2 * x * y + cy;
    u64 l1 = t1 % BH; cy = t1 / BH;
    u64 t2 = x * x + cy;
    u64 l2 = t2 % BH, l3 = t2 / BH;
    u64 L[4] = {l0, l1, l2, l3};
    int k = 0;
    for (int li = 0; li < 4 && k < C; ++li) {
        u64 v = L[li];
        for (int i = 0; i < HSPLIT && k < C; ++i) { D[k++] = (int)(v % b); v /= b; }
    }
    return k;
}

typedef struct { u64 u; u64 mn, msq; int ds; } Suf;
typedef struct { u64 P, nlo, nhi; u64 mn, msq; int ds; int known; } Top;

static Suf *suf; static long nsuf;
static Top *top; static long ntop;

// counters
static u64 leaves = 0, pairs = 0, pairs_disjoint = 0;
static u64 K[3][3];
static u64 hits = 0;
static u64 *hitlist; static long hitcap = 1 << 20;

static int force_list[MAXD][2 * MAXD]; static int force_n[MAXD];

static inline void leaf(u64 n, u64 nmask) {
    if (n < LO || n > HI) return;
    leaves++;
    int D[MAXD];
    sqdigits(n, D);
    // K grid
    for (int jj = 0; jj < 3; ++jj) {
        int Jc = J + jj;
        if (Jc > C) break;
        u64 m = nmask; int ok = 1;
        for (int i = 0; i < Jc; ++i) { u64 bit = 1ULL << D[i]; if (m & bit) { ok = 0; break; } m |= bit; }
        if (!ok) break; // larger J also fails
        for (int A = 1; A <= AP + 2 && A + Jc <= C; ++A) {
            u64 bit = 1ULL << D[C - A];
            if (m & bit) break;
            m |= bit;
            if (A >= AP) K[A - AP][jj]++;
        }
    }
    u64 m = nmask;
    for (int i = 0; i < C; ++i) { u64 bit = 1ULL << D[i]; if (m & bit) return; m |= bit; }
    if (hits < (u64)hitcap) hitlist[hits] = n;
    hits++;
}

// recursive middle enumeration: positions J .. S-T-1 (MID of them). pos index k = 0..MID-1 (k=0 is position J).
// The last one chosen (k = MID-1, i.e. the highest middle position) is forced by class.
static void middle(u64 nbase, u64 nmask, u64 pool, int ds, int k) {
    if (k == MID - 1) {
        int need = ds % (BASE - 1);
        for (int q = 0; q < force_n[need]; ++q) {
            int d = force_list[need][q];
            if (!(pool >> d & 1)) continue;
            leaf(nbase + (u64)d * PW[J + k], nmask | (1ULL << d));
        }
        return;
    }
    u64 p = pool;
    while (p) {
        int d = __builtin_ctzll(p); p &= p - 1;
        middle(nbase + (u64)d * PW[J + k], nmask | (1ULL << d), pool & ~(1ULL << d), ds + d, k + 1);
    }
}

int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage: %s t j AP chunk nchunks\n", argv[0]); return 1; }
    T = atoi(argv[1]); J = atoi(argv[2]); AP = atoi(argv[3]);
    int chunk = atoi(argv[4]), nchunks = atoi(argv[5]);
    // band
    int found = 0;
    for (int s = 1; s < BASE; ++s) {
        int c = BASE - s;
        if (c != 2 * s && c != 2 * s - 1) continue;
        u128 l1 = ipow128(s - 1), h1 = ipow128(s) - 1;
        u128 l2 = isqrt128(ipow128(c - 1) - 1) + 1, h2 = isqrt128(ipow128(c) - 1);
        u128 L = l1 > l2 ? l1 : l2, H = h1 < h2 ? h1 : h2;
        if (L <= H) { LO = (u64)L; HI = (u64)H; S = s; C = c; found = 1; break; }
    }
    if (!found) { printf("{\"b\":%d,\"band\":null}\n", BASE); return 0; }
    PW[0] = 1; for (int i = 1; i <= S + 1 && i < MAXD; ++i) PW[i] = PW[i - 1] * b;
    BH = 1; for (int i = 0; i < HSPLIT; ++i) BH *= b;
    // sanity for the limb split
    if (BH >= (1ULL << 32) || 4 * HSPLIT < C) { fprintf(stderr, "bad HSPLIT\n"); return 2; }
    if (T + J > S || T < 1) { fprintf(stderr, "bad t/j\n"); return 2; }
    MID = S - T - J;
    int m1 = BASE - 1, target = (BASE * (BASE - 1) / 2) % m1;
    int nroots = 0;
    for (int x = 0; x < m1; ++x) { VALID[x] = ((x + x * x) % m1 == target); nroots += VALID[x]; }
    for (int r = 0; r < m1; ++r) {  // r = digit sum so far mod m1; digits d making (r+d) valid
        force_n[r] = 0;
        for (int d = 0; d < BASE; ++d) if (VALID[(r + d) % m1]) force_list[r][force_n[r]++] = d;
    }
    hitlist = malloc(sizeof(u64) * hitcap);
    // suffixes
    u64 PJ = PW[J];
    suf = malloc(sizeof(Suf) * (PJ + 1)); nsuf = 0;
    for (u64 u = 0; u < PJ; ++u) {
        u64 mn = 0, v = u; int ok = 1, ds = 0;
        for (int i = 0; i < J; ++i) { int d = v % b; v /= b; ds += d; if (mn >> d & 1) { ok = 0; break; } mn |= 1ULL << d; }
        if (!ok) continue;
        u64 sq = (u64)(((u128)u * u) % PJ), msq = 0; v = sq;
        for (int i = 0; i < J; ++i) { int d = v % b; v /= b; u64 bit = 1ULL << d; if ((mn | msq) & bit) { ok = 0; break; } msq |= bit; }
        if (!ok) continue;
        suf[nsuf].u = u; suf[nsuf].mn = mn; suf[nsuf].msq = msq; suf[nsuf].ds = ds; nsuf++;
    }
    // tops
    u64 PT0 = PW[T - 1], PT1 = PW[T], span = PW[S - T];
    u128 BC = ipow128(C - AP);
    top = malloc(sizeof(Top) * (PT1 - PT0 + 1)); ntop = 0;
    for (u64 P = PT0; P < PT1; ++P) {
        u64 mn = 0, v = P; int ok = 1, ds = 0;
        for (int i = 0; i < T; ++i) { int d = v % b; v /= b; ds += d; if (mn >> d & 1) { ok = 0; break; } mn |= 1ULL << d; }
        if (!ok) continue;
        u64 nlo = P * span, nhi = nlo + span - 1;
        if (nhi < LO || nlo > HI) continue;
        if (nlo < LO) nlo = LO;
        if (nhi > HI) nhi = HI;
        u128 qa = ((u128)nlo * nlo) / BC, qb = ((u128)nhi * nhi) / BC;
        int da[MAXD], db[MAXD];
        for (int i = 0; i < AP; ++i) { da[i] = (int)(qa % b); qa /= b; db[i] = (int)(qb % b); qb /= b; }
        u64 msq = 0; int known = 0;
        for (int i = AP - 1; i >= 0; --i) {  // from the top
            if (da[i] != db[i]) break;
            u64 bit = 1ULL << da[i];
            if ((mn | msq) & bit) { ok = 0; break; }
            msq |= bit; known++;
        }
        if (!ok) continue;
        top[ntop].P = P; top[ntop].nlo = nlo; top[ntop].nhi = nhi; top[ntop].mn = mn; top[ntop].msq = msq;
        top[ntop].ds = ds; top[ntop].known = known; ntop++;
    }
    u64 ALL = (BASE == 64) ? ~0ULL : ((1ULL << BASE) - 1);
    long tops_mine = 0;
    for (long ti = chunk; ti < ntop; ti += nchunks) {
        Top *tp = &top[ti]; tops_mine++;
        u64 tmask = tp->mn | tp->msq;
        u64 nb0 = tp->P * span;
        for (long si = 0; si < nsuf; ++si) {
            Suf *sp = &suf[si];
            pairs++;
            if (tmask & (sp->mn | sp->msq)) continue;
            pairs_disjoint++;
            u64 used = tmask | sp->mn | sp->msq;
            u64 nmask = tp->mn | sp->mn;
            u64 nbase = nb0 + sp->u;
            int ds = tp->ds + sp->ds;
            if (MID == 0) {
                if (VALID[ds % m1]) leaf(nbase, nmask);
            } else {
                middle(nbase, nmask, ALL & ~used, ds, 0);
            }
        }
    }
    printf("{\"b\":%d,\"s\":%d,\"c\":%d,\"lo\":%llu,\"hi\":%llu,\"N\":%llu,\"roots\":%d,\"t\":%d,\"j\":%d,\"AP\":%d,"
           "\"chunk\":%d,\"nchunks\":%d,\"ntop\":%ld,\"tops_mine\":%ld,\"nsuf\":%ld,\"pairs\":%llu,\"pairs_disjoint\":%llu,"
           "\"leaves\":%llu,\"K\":{",
           BASE, S, C, (unsigned long long)LO, (unsigned long long)HI, (unsigned long long)(HI - LO + 1), nroots,
           T, J, AP, chunk, nchunks, ntop, tops_mine, nsuf, (unsigned long long)pairs,
           (unsigned long long)pairs_disjoint, (unsigned long long)leaves);
    int first = 1;
    for (int a = 0; a < 3; ++a) for (int jj = 0; jj < 3; ++jj) {
        if (AP + a + J + jj > C) continue;
        printf("%s\"%d,%d\":%llu", first ? "" : ",", AP + a, J + jj, (unsigned long long)K[a][jj]); first = 0;
    }
    printf("},\"hits\":%llu,\"witnesses\":[", (unsigned long long)hits);
    for (u64 i = 0; i < hits && i < (u64)hitcap; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)hitlist[i]);
    printf("]}\n");
    return 0;
}
