// domains.c -- H1 oracle test: do exact middle-digit DOMAINS reject whole batches?
//
// K-nice search in base b on the exact interval [lo, hi] (roots have L digits; the
// square has s digits and the cube c digits, s + c = K*b). A batch fixes the top t
// digits P of n and the bottom k digits R and leaves f = L - t - k digits free:
//     n = P*b^(L-t) + m*b^k + R,   m = 0 .. b^f - 1,   restricted to lo <= n <= hi.
// For each batch:
//   1. certified positions: the bottom k digits of n^2 and n^3 (from R), and the top
//      digits of n^2 and n^3 that are constant over [n_min, n_max] (interval test);
//   2. the existing END CHECK: no value may occur more than K times among the
//      certified digits;
//   3. for batches passing 2, the ORACLE: enumerate the batch and record, for every
//      unresolved output position j, the exact domain D_j of values it takes;
//   4. Hall/matching test with value capacities K - u_a (u_a = certified count):
//      variant NOMID uses every unresolved position except the cube's middle third
//      [L, 2L); variant ALL uses every unresolved position. A batch is rejected if
//      no assignment of distinct-with-multiplicity values from the domains exists.
//   5. every K-nice root found is recorded, and it is asserted that no batch
//      containing one is rejected (soundness).
// Output: one JSON line of aggregate counters, batch- and root-weighted.
//
// Build: clang -O3 -o domains domains.c -lpthread
// Run:   ./domains b K lo hi s c L t k threads
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned __int128 u128;
typedef uint64_t u64;

static int B, K, S2, S3, L, T_, KB, NTHR;
static u64 LO, HI;
static u128 POW[64];
static u64 CHUNK; static int CHUNKD;

static inline void extract_u64(u64 x, int nd, uint8_t *out) {
    for (int i = 0; i < nd; ++i) { out[i] = (uint8_t)(x % B); x /= B; }
}
static void extract(u128 x, int ndig, uint8_t *out) {   // out[i] = digit at position i
    int pos = 0;
    while (ndig - pos > CHUNKD) {
        u128 q = x / CHUNK; u64 r = (u64)(x - q * CHUNK);
        extract_u64(r, CHUNKD, out + pos); pos += CHUNKD; x = q;
    }
    extract_u64((u64)x, ndig - pos, out + pos);
}

typedef struct {
    u64 batches, end_rej, survive, rej_nomid, rej_all;
    u64 roots, roots_end_rej, roots_rej_nomid, roots_rej_all;
    u64 hits, hits_in_rej_nomid, hits_in_rej_all;
    u64 cert_sum, unres_sum, mid_unres_sum;      // over surviving batches
    u64 mid_dom_hist[65], oth_dom_hist[65];      // domain sizes of unresolved positions (surviving batches)
    u64 mid_dom_sum, mid_dom_cnt, oth_dom_sum, oth_dom_cnt;
    u64 cert_hist[128];
} Stats;

// Kuhn matching with capacities: positions -> values. Returns 1 if all positions can be matched.
static int hall_ok(const u64 *dom, const int *pos, int np, const int *cap) {
    int owner[128][8]; int cnt[64];   // owner[v][j] = position occupying slot j of value v
    for (int v = 0; v < B; ++v) cnt[v] = 0;
    int visited[64];
    // recursive augment via explicit stack would be complex; use recursion (depth <= np)
    int assigned[128]; for (int i = 0; i < np; ++i) assigned[i] = -1;
    // simple DFS augment
    int order[128]; for (int i = 0; i < np; ++i) order[i] = i;
    for (int i = 0; i < np; ++i) {
        for (int v = 0; v < B; ++v) visited[v] = 0;
        // iterative DFS using recursion helper
        int stackp[128], stackv[128], sp = 0;
        // try direct
        int ok = 0;
        // recursive lambda substitute
        // We implement recursion with an explicit function below.
        {
            // --- recursive function (nested via static helper) ---
            extern int augment(int p, const u64 *dom, int *cnt, const int *cap, int owner[][8], int *assigned, int *visited);
            ok = augment(i, dom, cnt, cap, owner, assigned, visited);
        }
        (void)stackp; (void)stackv; (void)sp; (void)order;
        if (!ok) return 0;
    }
    (void)pos;
    return 1;
}
int augment(int p, const u64 *dom, int *cnt, const int *cap, int owner[][8], int *assigned, int *visited) {
    u64 d = dom[p];
    // first pass: a free slot
    for (int v = 0; v < B; ++v) if ((d >> v & 1) && cnt[v] < cap[v]) {
        owner[v][cnt[v]++] = p; assigned[p] = v; return 1;
    }
    // second pass: re-route an occupant
    for (int v = 0; v < B; ++v) if ((d >> v & 1) && !visited[v]) {
        visited[v] = 1;
        for (int j = 0; j < cnt[v]; ++j) {
            int q = owner[v][j];
            if (augment(q, dom, cnt, cap, owner, assigned, visited)) { owner[v][j] = p; assigned[p] = v; return 1; }
        }
    }
    return 0;
}

typedef struct { int tid; Stats st; } Arg;

static void *worker(void *vp) {
    Arg *A = vp; Stats *st = &A->st; memset(st, 0, sizeof *st);
    int t = T_, k = KB, f = L - t - k;
    u64 Pmin = (u64)POW[t - 1], Pmax = (u64)POW[t];
    u64 bk = (u64)POW[k], bf = (u64)POW[f], bLt = (u64)POW[L - t];
    uint8_t dsq[64], dcu[64];
    u64 dom[128]; int cap[64], u[64];
    int pos_all[128], pos_nomid[128];
    for (u64 P = Pmin + A->tid; P < Pmax; P += NTHR) {
        u64 base0 = P * bLt;
        for (u64 R = 0; R < bk; ++R) {
            u64 base = base0 + R;
            // m range with lo <= base + m*bk <= hi
            if (base > HI) break;
            u64 m_lo = 0, m_hi = bf - 1;
            if (base < LO) m_lo = (LO - base + bk - 1) / bk;
            if (base + m_hi * bk > HI) m_hi = (HI - base) / bk;
            if (m_lo > m_hi) continue;
            u64 nroots = m_hi - m_lo + 1;
            u64 nmin = base + m_lo * bk, nmax = base + m_hi * bk;
            st->batches++; st->roots += nroots;
            // ---- certification ----
            for (int a = 0; a < B; ++a) u[a] = 0;
            int certified[160]; memset(certified, 0, sizeof certified);   // index: square pos p -> p ; cube pos p -> S2+p
            // bottom: R^2, R^3 mod b^k
            {
                u128 r2 = (u128)R * R, r3 = r2 * R;
                uint8_t d2[64], d3[64];
                extract(r2 % POW[k], k, d2); extract(r3 % POW[k], k, d3);
                for (int p = 0; p < k; ++p) { certified[p] = 1; u[d2[p]]++; certified[S2 + p] = 1; u[d3[p]]++; }
            }
            // top: constant digits over [nmin, nmax]
            int p2 = S2, p3 = S3;
            {
                u128 a2 = (u128)nmin * nmin, b2 = (u128)nmax * nmax;
                u128 a3 = a2 * nmin, b3 = b2 * nmax;
                uint8_t ea[64], eb[64], fa[64], fb[64];
                extract(a2, S2, ea); extract(b2, S2, eb); extract(a3, S3, fa); extract(b3, S3, fb);
                // positions >= p2 constant iff all digits at positions >= p2 agree (monotone => equivalent to floor equality)
                p2 = S2; while (p2 > k && ea[p2 - 1] == eb[p2 - 1]) --p2;
                p3 = S3; while (p3 > k && fa[p3 - 1] == fb[p3 - 1]) --p3;
                for (int p = p2; p < S2; ++p) { certified[p] = 1; u[ea[p]]++; }
                for (int p = p3; p < S3; ++p) { certified[S2 + p] = 1; u[fa[p]]++; }
            }
            int ncert = 0; for (int p = 0; p < S2 + S3; ++p) ncert += certified[p];
            int endbad = 0; for (int a = 0; a < B; ++a) if (u[a] > K) endbad = 1;
            // ---- oracle enumeration (always, to find hits; domains only matter if surviving) ----
            for (int p = 0; p < S2 + S3; ++p) dom[p] = 0;
            u64 hits_here = 0;
            for (u64 m = m_lo; m <= m_hi; ++m) {
                u64 n = base + m * bk;
                u128 sq = (u128)n * n, cu = sq * n;
                extract(sq, S2, dsq); extract(cu, S3, dcu);
                int cnt[64]; for (int a = 0; a < B; ++a) cnt[a] = 0;
                for (int p = 0; p < S2; ++p) { dom[p] |= 1ULL << dsq[p]; cnt[dsq[p]]++; }
                for (int p = 0; p < S3; ++p) { dom[S2 + p] |= 1ULL << dcu[p]; cnt[dcu[p]]++; }
                int nice = 1; for (int a = 0; a < B; ++a) if (cnt[a] != K) { nice = 0; break; }
                if (nice) { hits_here++; }
            }
            st->hits += hits_here;
            if (endbad) {
                st->end_rej++; st->roots_end_rej += nroots;
                if (hits_here) { fprintf(stderr, "SOUNDNESS VIOLATION: end check rejected a batch with a hit (P=%llu R=%llu)\n", (unsigned long long)P, (unsigned long long)R); exit(3); }
                continue;
            }
            st->survive++; st->cert_sum += ncert; st->cert_hist[ncert]++;
            for (int a = 0; a < B; ++a) cap[a] = K - u[a];
            int na = 0, nn = 0, nmid = 0;
            for (int p = 0; p < S2 + S3; ++p) if (!certified[p]) {
                pos_all[na++] = p;
                int cubepos = p - S2;
                int is_mid = (p >= S2 && cubepos >= L && cubepos < 2 * L);
                int ds = __builtin_popcountll(dom[p]);
                if (is_mid) { nmid++; st->mid_dom_hist[ds]++; st->mid_dom_sum += ds; st->mid_dom_cnt++; }
                else { pos_nomid[nn++] = p; st->oth_dom_hist[ds]++; st->oth_dom_sum += ds; st->oth_dom_cnt++; }
            }
            st->unres_sum += na; st->mid_unres_sum += nmid;
            // Hall variants
            u64 dom_nomid[128]; for (int i = 0; i < nn; ++i) dom_nomid[i] = dom[pos_nomid[i]];
            u64 dom_all[128]; for (int i = 0; i < na; ++i) dom_all[i] = dom[pos_all[i]];
            int ok_nomid = hall_ok(dom_nomid, pos_nomid, nn, cap);
            int ok_all = ok_nomid ? hall_ok(dom_all, pos_all, na, cap) : 0;
            if (!ok_nomid) { st->rej_nomid++; st->roots_rej_nomid += nroots; st->hits_in_rej_nomid += hits_here; }
            if (!ok_all) { st->rej_all++; st->roots_rej_all += nroots; st->hits_in_rej_all += hits_here; }
            if (hits_here && !ok_all) { fprintf(stderr, "SOUNDNESS VIOLATION: Hall rejected a batch with a hit (P=%llu R=%llu)\n", (unsigned long long)P, (unsigned long long)R); exit(3); }
        }
    }
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 11) { fprintf(stderr, "usage: %s b K lo hi s c L t k threads\n", argv[0]); return 2; }
    B = atoi(argv[1]); K = atoi(argv[2]); LO = strtoull(argv[3], 0, 10); HI = strtoull(argv[4], 0, 10);
    S2 = atoi(argv[5]); S3 = atoi(argv[6]); L = atoi(argv[7]); T_ = atoi(argv[8]); KB = atoi(argv[9]); NTHR = atoi(argv[10]);
    if (B > 63 || K > 7 || T_ < 1 || KB < 0 || T_ + KB > L) { fprintf(stderr, "bad parameters\n"); return 2; }
    POW[0] = 1; for (int i = 1; i < 64; ++i) POW[i] = POW[i - 1] * B;
    CHUNKD = 0; { u64 p = 1; while (p <= UINT64_MAX / B) { p *= B; ++CHUNKD; } CHUNK = p; }
    if (POW[L] > (u128)UINT64_MAX || HI >= (1ULL << 42)) { fprintf(stderr, "n too large for 128-bit cubes\n"); return 2; }
    pthread_t th[64]; Arg args[64];
    for (int i = 0; i < NTHR; ++i) { args[i].tid = i; pthread_create(&th[i], 0, worker, &args[i]); }
    Stats tot; memset(&tot, 0, sizeof tot);
    for (int i = 0; i < NTHR; ++i) {
        pthread_join(th[i], 0); Stats *s = &args[i].st;
        u64 *a = (u64 *)&tot, *b = (u64 *)s; for (size_t j = 0; j < sizeof(Stats) / 8; ++j) a[j] += b[j];
    }
    int f = L - T_ - KB;
    printf("{\"b\":%d,\"K\":%d,\"lo\":%llu,\"hi\":%llu,\"s\":%d,\"c\":%d,\"L\":%d,\"t\":%d,\"k\":%d,\"f\":%d,",
           B, K, (unsigned long long)LO, (unsigned long long)HI, S2, S3, L, T_, KB, f);
    printf("\"batches\":%llu,\"end_rejected\":%llu,\"surviving\":%llu,\"hall_rejected_nomid\":%llu,\"hall_rejected_all\":%llu,",
           (unsigned long long)tot.batches, (unsigned long long)tot.end_rej, (unsigned long long)tot.survive,
           (unsigned long long)tot.rej_nomid, (unsigned long long)tot.rej_all);
    printf("\"roots\":%llu,\"roots_end_rejected\":%llu,\"roots_hall_rejected_nomid\":%llu,\"roots_hall_rejected_all\":%llu,",
           (unsigned long long)tot.roots, (unsigned long long)tot.roots_end_rej, (unsigned long long)tot.roots_rej_nomid, (unsigned long long)tot.roots_rej_all);
    printf("\"hits\":%llu,\"hits_in_rejected_nomid\":%llu,\"hits_in_rejected_all\":%llu,",
           (unsigned long long)tot.hits, (unsigned long long)tot.hits_in_rej_nomid, (unsigned long long)tot.hits_in_rej_all);
    printf("\"mean_certified_surviving\":%.4f,\"mean_unresolved_surviving\":%.4f,\"mean_mid_unresolved_surviving\":%.4f,",
           tot.survive ? (double)tot.cert_sum / tot.survive : 0.0, tot.survive ? (double)tot.unres_sum / tot.survive : 0.0,
           tot.survive ? (double)tot.mid_unres_sum / tot.survive : 0.0);
    printf("\"mid_domain_mean\":%.4f,\"other_domain_mean\":%.4f,",
           tot.mid_dom_cnt ? (double)tot.mid_dom_sum / tot.mid_dom_cnt : 0.0, tot.oth_dom_cnt ? (double)tot.oth_dom_sum / tot.oth_dom_cnt : 0.0);
    printf("\"mid_domain_hist\":["); for (int i = 0; i <= B; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)tot.mid_dom_hist[i]); printf("],");
    printf("\"other_domain_hist\":["); for (int i = 0; i <= B; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)tot.oth_dom_hist[i]); printf("],");
    printf("\"certified_hist\":{"); int first = 1; for (int i = 0; i < 128; ++i) if (tot.cert_hist[i]) { printf("%s\"%d\":%llu", first ? "" : ",", i, (unsigned long long)tot.cert_hist[i]); first = 0; } printf("}}\n");
    return 0;
}
