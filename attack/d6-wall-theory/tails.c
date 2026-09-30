// tails.c -- degenerate batches (D6 note, step 2).
//
// mode h1   b K lo hi s c L t k seed
//   Re-enumerates exactly the population of H1's tail table (attack/h1-domains/domains.c, logic
//   copied): batches n = Ptop*b^(L-t) + m*b^k + R (f = L-t-k = 1), intersected with [lo,hi];
//   bottom k digits and constant top digits certified; end check with multiplicity K.
//   For every cube position P in the middle third [L,2L) it records the number D of distinct
//   values along the batch, split by: surviving/rejected, full/truncated batch, certified or not.
//   It also evaluates, for the same batch and position, the "structured model": the digit at P of
//   (X0 + 3c^2 b^k m + 3c b^2k m^2 + b^3k m^3) mod b^(P+1) with X0 uniform random (exact integers),
//   i.e. Lemma 1 with the batch's exact theta1, theta2, theta3 and a uniform x0.
// mode model b samples seed
//   Monte Carlo of P(D <= s), s = 1..4, for b points y_m = x0 + th1 m + th2 m^2 (m < b):
//   rotation (th2 = 0) and quadratic (th2 uniform) with x0, th1 uniform; and the quadratic model
//   with th2 uniform on [0, rho) for rho = b^-1, b^-2, b^-3.
// Build: clang -O3 -o tails tails.c -lm
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned __int128 u128; typedef uint64_t u64;
static int B, K, S2, S3, L, T_, KB;
static u64 LO, HI;
static u128 POW[64];
static u64 rs;
static inline u64 rnd(void) { u64 z = (rs += 0x9E3779B97F4A7C15ULL); z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
static inline double unif(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }
static void extract(u128 x, int nd, uint8_t *out) { for (int i = 0; i < nd; ++i) { out[i] = (uint8_t)(x % B); x /= B; } }

// counters: [P-L][class][D] ; class 0 = surviving full uncertified, 1 = surviving truncated uncertified,
// 2 = surviving certified (any), 3 = rejected by end check (full, uncertified)
#define NCL 4
static u64 H[40][NCL][65], HS[40][NCL][65];

static void mode_h1(char **argv) {
    B = atoi(argv[2]); K = atoi(argv[3]); LO = strtoull(argv[4], 0, 10); HI = strtoull(argv[5], 0, 10);
    S2 = atoi(argv[6]); S3 = atoi(argv[7]); L = atoi(argv[8]); T_ = atoi(argv[9]); KB = atoi(argv[10]); rs = strtoull(argv[11], 0, 10);
    POW[0] = 1; for (int i = 1; i < 64; ++i) POW[i] = POW[i - 1] * B;
    int t = T_, k = KB, f = L - t - k;
    if (f != 1) { fprintf(stderr, "f must be 1\n"); exit(2); }
    u64 Pmin = (u64)POW[t - 1], Pmax = (u64)POW[t], bk = (u64)POW[k], bf = (u64)POW[f], bLt = (u64)POW[L - t];
    uint8_t dsq[64], dcu[64];
    u64 nb = 0, nsurv = 0, ntrunc = 0;
    for (u64 P = Pmin; P < Pmax; ++P) {
        u64 base0 = P * bLt;
        if (base0 + bLt - 1 < LO || base0 > HI) continue;
        for (u64 R = 0; R < bk; ++R) {
            u64 base = base0 + R;
            if (base > HI) break;
            u64 m_lo = 0, m_hi = bf - 1;
            if (base < LO) m_lo = (LO - base + bk - 1) / bk;
            if (base + m_hi * bk > HI) m_hi = (HI - base) / bk;
            if (m_lo > m_hi) continue;
            u64 nroots = m_hi - m_lo + 1, nmin = base + m_lo * bk, nmax = base + m_hi * bk;
            int u[64] = {0}; int cert3[64] = {0};
            { u128 r2 = (u128)R * R, r3 = r2 * R; uint8_t d2[64], d3[64];
              extract(r2 % POW[k], k, d2); extract(r3 % POW[k], k, d3);
              for (int p = 0; p < k; ++p) { u[d2[p]]++; u[d3[p]]++; cert3[p] = 1; } }
            int p2 = S2, p3 = S3;
            { u128 a2 = (u128)nmin * nmin, b2 = (u128)nmax * nmax, a3 = a2 * nmin, b3 = b2 * nmax;
              uint8_t ea[64], eb[64], fa[64], fb[64];
              extract(a2, S2, ea); extract(b2, S2, eb); extract(a3, S3, fa); extract(b3, S3, fb);
              while (p2 > k && ea[p2 - 1] == eb[p2 - 1]) --p2;
              while (p3 > k && fa[p3 - 1] == fb[p3 - 1]) --p3;
              for (int p = p2; p < S2; ++p) u[ea[p]]++;
              for (int p = p3; p < S3; ++p) { u[fa[p]]++; cert3[p] = 1; } }
            int endbad = 0; for (int a = 0; a < B; ++a) if (u[a] > K) endbad = 1;
            nb++; if (!endbad) nsurv++; int trunc = nroots < bf; if (trunc) ntrunc++;
            if (endbad && trunc) continue;
            u64 dom[40] = {0}, doms[40] = {0};
            u128 c = (u128)base;   // free digit block is zero in base
            for (u64 m = m_lo; m <= m_hi; ++m) {
                u128 n = c + (u128)bk * m, cu = n * n * n;
                extract(cu, S3, dcu);
                for (int P3 = L; P3 < 2 * L; ++P3) dom[P3 - L] |= 1ULL << dcu[P3];
            }
            // structured model: x0 replaced by a uniform residue, exact theta1..3 of this batch
            for (int P3 = L; P3 < 2 * L; ++P3) {
                u128 M = POW[P3 + 1];
                u128 X0 = (((u128)rnd() << 64) | rnd()) % M;
                u128 T1 = (3 * c % M) * c % M * (POW[k] % M) % M;
                u128 T2 = (3 * c % M) * (POW[2 * k] % M) % M;
                u128 T3 = POW[3 * k] % M;
                for (u64 m = m_lo; m <= m_hi; ++m) {
                    u128 mm = m, v = (X0 + T1 * mm % M + T2 * (mm * mm) % M + T3 * (mm * mm * mm) % M) % M;
                    doms[P3 - L] |= 1ULL << (int)((v / POW[P3]) % B);
                }
            }
            for (int P3 = L; P3 < 2 * L; ++P3) {
                int cl = endbad ? 3 : (cert3[P3] ? 2 : (trunc ? 1 : 0));
                H[P3 - L][cl][__builtin_popcountll(dom[P3 - L])]++;
                HS[P3 - L][cl][__builtin_popcountll(doms[P3 - L])]++;
            }
        }
    }
    (void)dsq; (void)S2;
    printf("{\"mode\":\"h1\",\"b\":%d,\"K\":%d,\"lo\":%llu,\"hi\":%llu,\"L\":%d,\"t\":%d,\"k\":%d,\"batches\":%llu,\"surviving\":%llu,\"truncated\":%llu,"
           "\"classes\":[\"surviving_full_uncertified\",\"surviving_truncated_uncertified\",\"surviving_certified\",\"rejected_full_uncertified\"],\"positions\":[",
           B, K, (unsigned long long)LO, (unsigned long long)HI, L, t, k, (unsigned long long)nb, (unsigned long long)nsurv, (unsigned long long)ntrunc);
    for (int P3 = L; P3 < 2 * L; ++P3) {
        printf("%s{\"P\":%d,\"hist\":[", P3 > L ? "," : "", P3);
        for (int cl = 0; cl < NCL; ++cl) { printf("%s[", cl ? "," : ""); for (int d = 0; d <= B; ++d) printf("%s%llu", d ? "," : "", (unsigned long long)H[P3 - L][cl][d]); printf("]"); }
        printf("],\"hist_structured_model\":[");
        for (int cl = 0; cl < NCL; ++cl) { printf("%s[", cl ? "," : ""); for (int d = 0; d <= B; ++d) printf("%s%llu", d ? "," : "", (unsigned long long)HS[P3 - L][cl][d]); printf("]"); }
        printf("]}");
    }
    printf("]}\n");
}

// number of distinct digits of b points y_m = x0 + a1 m + a2 m^2 (mod 1), stopping once > smax
static int distinct(int b, double x0, double a1, double a2, int smax) {
    u64 seen = 0; int cnt = 0;
    for (int m = 0; m < b; ++m) {
        double y = x0 + a1 * m + a2 * (double)m * m; y -= floor(y);
        int d = (int)(y * b); if (d >= b) d = b - 1;
        if (!(seen >> d & 1)) { seen |= 1ULL << d; if (++cnt > smax) return cnt; }
    }
    return cnt;
}

static void mode_model(char **argv) {
    int b = atoi(argv[2]); long S = atol(argv[3]); rs = strtoull(argv[4], 0, 10);
    const int SM = 4;
    // models: 0 rotation, 1 quadratic uniform, 2..4 quadratic with th2 in [0, b^-1), [0,b^-2), [0,b^-3)
    const char *names[5] = {"rotation", "quadratic_uniform", "quadratic_rho_b^-1", "quadratic_rho_b^-2", "quadratic_rho_b^-3"};
    printf("{\"mode\":\"model\",\"b\":%d,\"samples\":%ld,\"models\":{", b, S);
    for (int md = 0; md < 5; ++md) {
        long cnt[8] = {0};
        double rho = md == 2 ? 1.0 / b : md == 3 ? 1.0 / ((double)b * b) : md == 4 ? 1.0 / ((double)b * b * b) : 1.0;
        for (long i = 0; i < S; ++i) {
            double x0 = unif(), a1 = unif(), a2 = md == 0 ? 0.0 : rho * unif();
            int D = distinct(b, x0, a1, a2, SM);
            if (D <= SM) cnt[D]++;
        }
        printf("%s\"%s\":{\"rho\":%.6g,\"P_D_le\":[", md ? "," : "", names[md], md == 0 ? 0.0 : rho);
        long acc = 0; for (int s = 1; s <= SM; ++s) { acc += cnt[s]; printf("%s%.6e", s > 1 ? "," : "", (double)acc / S); }
        printf("],\"counts_le\":["); acc = 0; for (int s = 1; s <= SM; ++s) { acc += cnt[s]; printf("%s%ld", s > 1 ? "," : "", acc); }
        printf("]}");
    }
    printf("}}\n");
}


// mode model2 b samples seed th3exp rho : x0, th1 uniform; th2 uniform on [0,rho) (rho=1: whole circle; rho=0: rotation);
// th3 = b^-th3exp fixed (th3exp = 0: no cubic term). Prints P(D <= s), s = 1..4.
static void mode_model2(char **argv) {
    int b = atoi(argv[2]); long S = atol(argv[3]); rs = strtoull(argv[4], 0, 10); int e3 = atoi(argv[5]); double rho = atof(argv[6]);
    double th3 = e3 > 0 ? pow((double)b, -e3) : 0.0; long cnt[8] = {0};
    for (long i = 0; i < S; ++i) {
        double x0 = unif(), a1 = unif(), a2 = rho * unif();
        u64 seen = 0; int c = 0;
        for (int m = 0; m < b; ++m) {
            double y = x0 + a1 * m + a2 * (double)m * m + th3 * (double)m * m * m; y -= floor(y);
            int d = (int)(y * b); if (d >= b) d = b - 1;
            if (!(seen >> d & 1)) { seen |= 1ULL << d; if (++c > 4) break; }
        }
        if (c <= 4) cnt[c]++;
    }
    printf("{\"mode\":\"model2\",\"b\":%d,\"samples\":%ld,\"th3_exp\":%d,\"rho\":%g,\"P_D_le\":[", b, S, e3, rho);
    long acc = 0; for (int s = 1; s <= 4; ++s) { acc += cnt[s]; printf("%s%.6e", s > 1 ? "," : "", (double)acc / S); }
    printf("],\"counts_le\":["); acc = 0; for (int s = 1; s <= 4; ++s) { acc += cnt[s]; printf("%s%ld", s > 1 ? "," : "", acc); }
    printf("]}\n");
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: tails h1|model ...\n"); return 2; }
    if (!strcmp(argv[1], "h1")) { if (argc < 12) { fprintf(stderr, "tails h1 b K lo hi s c L t k seed\n"); return 2; } mode_h1(argv); }
    else if (!strcmp(argv[1], "model2")) { if (argc < 7) return 2; mode_model2(argv); }
    else if (!strcmp(argv[1], "model")) { if (argc < 5) { fprintf(stderr, "tails model b samples seed\n"); return 2; } mode_model(argv); }
    else return 2;
    return 0;
}
