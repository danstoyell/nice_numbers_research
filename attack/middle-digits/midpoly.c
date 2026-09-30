// midpoly.c -- measurements behind the structure lemma for middle digits of cubes.
//
// A search batch fixes the top t and bottom k digits of the root and frees f digits
// at positions [k, k+f):  n(m) = c + b^k m,  m = 0..b^f-1,  where c has zero digits at
// [k, k+f).  Then n(m)^3 = c^3 + 3c^2 b^k m + 3c b^(2k) m^2 + b^(3k) m^3, so the digit of
// n(m)^3 at position P is  floor( b * frac( x0 + th1*m + th2*m^2 + th3*m^3 ) )  with
//   x0  = (c^3      mod b^(P+1))    / b^(P+1)
//   th1 = (3c^2     mod b^(P+1-k))  / b^(P+1-k)         (P+1 > k)
//   th2 = (3c       mod b^(P+1-2k)) / b^(P+1-2k)        (P+1 > 2k)
//   th3 = 1 / b^(P+1-3k)                                (P+1 > 3k)
// (coefficients whose power is <= 0 are integers and drop out of the fractional part).
//
// Modes:
//   coeff  b L t k f P samples seed
//      samples random batches c; verifies the identity for every m (exact integers);
//      histograms x0, th1, th2 (64 bins) and (x0,th1) jointly (16x16); records the number
//      of distinct digits at position P along the batch; and simulates the same statistic
//      for (i) the polynomial model with uniform random coefficients and (ii) iid digits.
//   sens   b lo hi L samples seed
//      random roots n in [lo,hi]; for each position i of n, replaces digit i by a random
//      other digit and records, per output position of n^2 and n^3, how often the digit
//      changed.
//   batch  b lo hi L t seed
//      one large batch (top t digits fixed at a random prefix, all lower digits free):
//      for each position P of the cube, the digit frequencies and their maximum
//      deviation from 1/b.
// Build: clang -O3 -o midpoly midpoly.c -lm
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned __int128 u128; typedef uint64_t u64;
static u64 rs;
static inline u64 rnd(void) { u64 z = (rs += 0x9E3779B97F4A7C15ULL); z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
static inline double unif(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }
static u128 POW[80];
static int digit_at(u128 x, int p, int b) { return (int)((x / POW[p]) % b); }

static void mode_coeff(int argc, char **argv) {
    int b = atoi(argv[2]), L = atoi(argv[3]), t = atoi(argv[4]), k = atoi(argv[5]), f = atoi(argv[6]), P = atoi(argv[7]);
    long S = atol(argv[8]); rs = strtoull(argv[9], 0, 10);
    if (t + k + f != L) { fprintf(stderr, "need t+k+f=L\n"); exit(2); }
    int nb = 64; long h0[64] = {0}, h1[64] = {0}, h2[64] = {0}, h01[16][16] = {{0}};
    long dom_meas[64] = {0}, dom_poly[64] = {0}, dom_polyu[64] = {0}, dom_iid[64] = {0};
    long M = 1; for (int i = 0; i < f; ++i) M *= b;
    u128 modP = POW[P + 1];
    int e1 = P + 1 - k, e2 = P + 1 - 2 * k, e3 = P + 1 - 3 * k;
    long mismatches = 0; double th2_max = 0;
    for (long s = 0; s < S; ++s) {
        // c = Ptop * b^(k+f) + R, top digit nonzero
        u64 Pmin = (u64)POW[t - 1], Pmax = (u64)POW[t];
        u64 Ptop = Pmin + rnd() % (Pmax - Pmin), R = rnd() % (u64)POW[k];
        u128 c = (u128)Ptop * POW[k + f] + R;
        u128 c2 = c * c, c3 = c2 * c;
        double x0 = (double)(u64)(c3 % modP) / (double)(u64)modP;   // fits: b^(P+1) <= b^(2L) < 2^64 for the cases run
        double th1 = e1 > 0 ? (double)(u64)((3 * c2) % POW[e1]) / (double)(u64)POW[e1] : 0.0;
        double th2 = e2 > 0 ? (double)(u64)((3 * c) % POW[e2]) / (double)(u64)POW[e2] : 0.0;
        double th3 = e3 > 0 ? 1.0 / (double)(u64)POW[e3] : 0.0;
        if (th2 > th2_max) th2_max = th2;
        h0[(int)(x0 * nb)]++; h1[(int)(th1 * nb)]++; h2[(int)(th2 * nb)]++; h01[(int)(x0 * 16)][(int)(th1 * 16)]++;
        u64 seen = 0, seenp = 0, seenq = 0, seeni = 0;
        for (long m = 0; m < M; ++m) {
            u128 n = c + POW[k] * (u128)m, cube = n * n * n;
            int d = digit_at(cube, P, b);
            // identity check with exact integers: digit P of (c^3 + 3c^2 b^k m + 3c b^2k m^2 + b^3k m^3) mod b^(P+1)
            u128 recon = (c3 + 3 * c2 * POW[k] * (u128)m + 3 * c * POW[2 * k] * (u128)(m * m) + POW[3 * k] * (u128)(m * m * m)) % modP;
            if ((int)((recon / POW[P]) % b) != d) mismatches++;
            seen |= 1ULL << d;
            // Lemma 1 as stated: the digit from the REDUCED residues over the common denominator b^(P+1)
            // (D7 audit, 2026-09-28: the check above only re-expands the binomial)
            u128 lem = c3 % modP;
            if (e1 > 0) lem += ((3 * c2) % POW[e1]) * POW[k] * (u128)m;
            if (e2 > 0) lem += ((3 * c) % POW[e2]) * POW[2 * k] * (u128)(m * m);
            if (e3 > 0) lem += POW[3 * k] * (u128)(m * m * m);
            if ((int)(((lem % modP) / POW[P]) % b) != d) mismatches++;
        }
        dom_meas[__builtin_popcountll(seen)]++;
        // polynomial model: x0 and th1 uniform random, th2 and th3 the EXACT arithmetic values of this batch
        double px0 = unif(), pth1 = unif(), pth2 = th2;
        for (long m = 0; m < M; ++m) { double y = px0 + pth1 * m + pth2 * (double)m * m + th3 * (double)m * m * m; y -= floor(y); int d = (int)(y * b); if (d >= b) d = b - 1; seenp |= 1ULL << d; }
        dom_poly[__builtin_popcountll(seenp)]++;
        // polynomial model with ALL coefficients uniform (th2 on [0,1)): for contrast
        double qth2 = unif();
        for (long m = 0; m < M; ++m) { double y = px0 + pth1 * m + qth2 * (double)m * m + th3 * (double)m * m * m; y -= floor(y); int d = (int)(y * b); if (d >= b) d = b - 1; seenq |= 1ULL << d; }
        dom_polyu[__builtin_popcountll(seenq)]++;
        for (long m = 0; m < M; ++m) seeni |= 1ULL << (rnd() % b);
        dom_iid[__builtin_popcountll(seeni)]++;
    }
    double dev0 = 0, dev1 = 0, dev2 = 0, dev01 = 0;
    for (int i = 0; i < nb; ++i) { dev0 = fmax(dev0, fabs(h0[i] * (double)nb / S - 1)); dev1 = fmax(dev1, fabs(h1[i] * (double)nb / S - 1)); dev2 = fmax(dev2, fabs(h2[i] * (double)nb / S - 1)); }
    for (int i = 0; i < 16; ++i) for (int j = 0; j < 16; ++j) dev01 = fmax(dev01, fabs(h01[i][j] * 256.0 / S - 1));
    double mm = 0, mp = 0, mq = 0, mi = 0; for (int d = 0; d <= b; ++d) { mm += d * (double)dom_meas[d]; mp += d * (double)dom_poly[d]; mq += d * (double)dom_polyu[d]; mi += d * (double)dom_iid[d]; }
    double tvp = 0, tvq = 0, tvi = 0; for (int d = 0; d <= b; ++d) { tvp += fabs(dom_meas[d] - dom_poly[d]); tvq += fabs(dom_meas[d] - dom_polyu[d]); tvi += fabs(dom_meas[d] - dom_iid[d]); } tvp /= 2.0 * S; tvq /= 2.0 * S; tvi /= 2.0 * S;
    long lo_m = 0, lo_p = 0, lo_i = 0; for (int d = 0; d <= 3; ++d) { lo_m += dom_meas[d]; lo_p += dom_poly[d]; lo_i += dom_iid[d]; }
    printf("{\"mode\":\"coeff\",\"b\":%d,\"L\":%d,\"t\":%d,\"k\":%d,\"f\":%d,\"P\":%d,\"samples\":%ld,\"identity_mismatches\":%ld,"
           "\"zone\":\"%s\",\"th2_natural_range\":%.6g,\"maxdev_x0_64bins\":%.4f,\"maxdev_th1_64bins\":%.4f,\"maxdev_th2_64bins\":%.4f,\"maxdev_joint_x0_th1_16x16\":%.4f,"
           "\"iid_noise_64bins\":%.4f,\"mean_distinct\":{\"measured\":%.4f,\"poly_exact_th2\":%.4f,\"poly_uniform_th2\":%.4f,\"iid_model\":%.4f,\"iid_exact\":%.4f},"
           "\"tv_measured_vs\":{\"poly_exact_th2\":%.4f,\"poly_uniform_th2\":%.4f,\"iid\":%.4f},\"frac_domain_le3\":{\"measured\":%.2e,\"poly_exact_th2\":%.2e,\"iid\":%.2e},",
           b, L, t, k, f, P, S, mismatches, e3 > 0 ? "cubic" : (e2 > 0 ? "quadratic" : (e1 > 0 ? "affine" : "fixed")),
           e2 > 0 ? fmin(1.0, 3.0 * (double)(u64)POW[L] / (double)(u64)POW[e2]) : 0.0,
           dev0, dev1, dev2, dev01, sqrt((double)nb / S), mm / S, mp / S, mq / S, mi / S, b * (1 - pow(1 - 1.0 / b, M)),
           tvp, tvq, tvi, (double)lo_m / S, (double)lo_p / S, (double)lo_i / S);
    printf("\"dom_hist_measured\":["); for (int d = 0; d <= b; ++d) printf("%s%ld", d ? "," : "", dom_meas[d]);
    printf("],\"dom_hist_poly\":["); for (int d = 0; d <= b; ++d) printf("%s%ld", d ? "," : "", dom_poly[d]);
    printf("],\"dom_hist_poly_uniform\":["); for (int d = 0; d <= b; ++d) printf("%s%ld", d ? "," : "", dom_polyu[d]);
    printf("],\"dom_hist_iid\":["); for (int d = 0; d <= b; ++d) printf("%s%ld", d ? "," : "", dom_iid[d]);
    printf("]}\n");
}

static void mode_sens(int argc, char **argv) {
    int b = atoi(argv[2]); u64 lo = strtoull(argv[3], 0, 10), hi = strtoull(argv[4], 0, 10); int L = atoi(argv[5]); long S = atol(argv[6]); rs = strtoull(argv[7], 0, 10);
    // digits of n^2: 2L positions, n^3: 3L positions (upper bound); count changes per (i, position)
    static long chg2[16][48], chg3[16][80]; long cnt[16] = {0};
    for (long s = 0; s < S; ++s) {
        u64 n = lo + rnd() % (hi - lo + 1);
        int i = (int)(rnd() % L);
        int d = (int)((n / (u64)POW[i]) % b), d2 = (int)(rnd() % (b - 1)); if (d2 >= d) d2++;
        long long n2 = (long long)n + (long long)(d2 - d) * (long long)(u64)POW[i];
        if (n2 < (long long)lo || n2 > (long long)hi) continue;
        u128 a2 = (u128)n * n, a3 = a2 * n, c2 = (u128)(u64)n2 * (u64)n2, c3 = c2 * (u64)n2;
        cnt[i]++;
        for (int p = 0; p < 2 * L; ++p) if (digit_at(a2, p, b) != digit_at(c2, p, b)) chg2[i][p]++;
        for (int p = 0; p < 3 * L; ++p) if (digit_at(a3, p, b) != digit_at(c3, p, b)) chg3[i][p]++;
    }
    printf("{\"mode\":\"sens\",\"b\":%d,\"L\":%d,\"samples\":%ld,\"expected_random\":%.5f,\"rows\":[", b, L, S, 1 - 1.0 / b);
    for (int i = 0; i < L; ++i) {
        printf("%s{\"flipped_digit\":%d,\"count\":%ld,\"square\":[", i ? "," : "", i, cnt[i]);
        for (int p = 0; p < 2 * L; ++p) printf("%s%.4f", p ? "," : "", cnt[i] ? (double)chg2[i][p] / cnt[i] : 0);
        printf("],\"cube\":["); for (int p = 0; p < 3 * L; ++p) printf("%s%.4f", p ? "," : "", cnt[i] ? (double)chg3[i][p] / cnt[i] : 0);
        printf("]}");
    }
    printf("]}\n");
}

static void mode_batch(int argc, char **argv) {
    int b = atoi(argv[2]); u64 lo = strtoull(argv[3], 0, 10), hi = strtoull(argv[4], 0, 10); int L = atoi(argv[5]), t = atoi(argv[6]); rs = strtoull(argv[7], 0, 10);
    u64 Pmin = (u64)POW[t - 1], Pmax = (u64)POW[t], Ptop;
    do { Ptop = Pmin + rnd() % (Pmax - Pmin); } while (Ptop * (u64)POW[L - t] < lo || (Ptop + 1) * (u64)POW[L - t] - 1 > hi);
    u64 N = (u64)POW[L - t];
    static long freq[80][64];
    for (u64 u = 0; u < N; ++u) { u64 n = Ptop * N + u; u128 cube = (u128)n * n * n; for (int p = 0; p < 3 * L; ++p) freq[p][digit_at(cube, p, b)]++; }
    printf("{\"mode\":\"batch\",\"b\":%d,\"L\":%d,\"t\":%d,\"prefix\":%llu,\"N\":%llu,\"weyl_bound_N^-1/4\":%.5f,\"iid_noise\":%.6f,\"rows\":[", b, L, t, (unsigned long long)Ptop, (unsigned long long)N, pow((double)N, -0.25), sqrt((1.0 / b) * (1 - 1.0 / b) / (double)N));
    for (int p = 0; p < 3 * L; ++p) {
        double mx = 0; int distinct = 0; for (int a = 0; a < b; ++a) { if (freq[p][a]) distinct++; mx = fmax(mx, fabs((double)freq[p][a] / N - 1.0 / b)); }
        printf("%s{\"P\":%d,\"distinct\":%d,\"maxdev\":%.6f}", p ? "," : "", p, distinct, mx);
    }
    printf("]}\n");
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: midpoly coeff|sens|batch ...\n"); return 2; }
    int b = atoi(argv[2]); POW[0] = 1; for (int i = 1; i < 80; ++i) POW[i] = POW[i - 1] * b;
    if (!strcmp(argv[1], "coeff")) mode_coeff(argc, argv);
    else if (!strcmp(argv[1], "sens")) mode_sens(argc, argv);
    else if (!strcmp(argv[1], "batch")) mode_batch(argc, argv);
    else return 2;
    return 0;
}
