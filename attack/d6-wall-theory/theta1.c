// theta1.c -- exact law of the linear coefficient theta1 of Lemma 1 (middle-digits report)
// over ALL batches of a shape, against the mixture formula of Theorem S (D6 note).
//
// Batch: c = Ptop*b^(k+f) + R, b^(t-1) <= Ptop < b^t, 0 <= R < b^k, t+k+f = L.
// theta1 = (3c^2 mod b^J)/b^J, J = P+1-k.  j := P+1-2k-f = J-(k+f).
//   j <= 0          : theta1 = {3R^2/b^J}                 (prefix-free)
//   1 <= j <= k+f   : theta1 = {3R^2/b^J + 6*Ptop*R/b^j}   (prefix enters linearly)
//   j >  k+f        : Ptop^2 enters (Theorem A regime), formula not evaluated here.
// Theorem S (complete case 1 <= j <= t-1): given R, theta1 is uniform on the coset
//   3R^2/b^J + (g/b^j)Z/Z,  g = gcd(6R, b^j)  (q_R = b^j/g points, each N_P/q_R times).
// Fourier form (any j >= 1):  E e(h theta1) = (1/(b^k N_P)) sum_R e(3hR^2/b^J) * sum_Ptop e(6hR Ptop/b^j)
//   and in the complete case  = b^-k sum_{R<b^k, b^j | 6hR} e(3hR^2/b^J).
//
// Output (one JSON line): exact 64-bin histogram max deviation by brute force and by the
// formula, whether the 64- and 4096-bin histograms agree exactly (integer counts), the
// Fourier coefficients at a list of h by brute force and by formula, and the class weights.
// Build: clang -O3 -o theta1 theta1.c -lm
// Usage: theta1 b L t k f P [h1,h2,...]
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned __int128 u128; typedef uint64_t u64;
static u128 POW[64];
static u64 gcdu(u64 a, u64 b) { while (b) { u64 t = a % b; a = b; b = t; } return a; }

int main(int argc, char **argv) {
    if (argc < 7) { fprintf(stderr, "usage: theta1 b L t k f P [hlist]\n"); return 2; }
    int b = atoi(argv[1]), L = atoi(argv[2]), t = atoi(argv[3]), k = atoi(argv[4]), f = atoi(argv[5]), P = atoi(argv[6]);
    if (t + k + f != L) { fprintf(stderr, "need t+k+f=L\n"); return 2; }
    POW[0] = 1; for (int i = 1; i < 64; ++i) POW[i] = POW[i - 1] * b;
    int H[64], nh = 0;
    { const char *s = argc > 7 ? argv[7] : "1,2,5,6,25,30,32,64,150"; char buf[512]; strncpy(buf, s, 511); buf[511] = 0;
      for (char *p = strtok(buf, ","); p && nh < 64; p = strtok(0, ",")) H[nh++] = atoi(p); }
    int J = P + 1 - k, j = P + 1 - 2 * k - f;
    if (J <= 0) { fprintf(stderr, "theta1 = 0 at this position\n"); return 2; }
    u128 bJ = POW[J];
    u64 Pmin = (u64)POW[t - 1], Pmax = (u64)POW[t], NP = Pmax - Pmin, bk = (u64)POW[k];
    const int NB = 64, NF = 4096;
    static u64 hb[64], hf[64], hb2[4096], hf2[4096];
    double *bre = calloc(nh, sizeof(double)), *bim = calloc(nh, sizeof(double));
    // ---- brute force over all batches ----
    for (u64 Pt = Pmin; Pt < Pmax; ++Pt) {
        for (u64 R = 0; R < bk; ++R) {
            u128 c = (u128)Pt * POW[k + f] + R;
            u128 v = (3 * c * c) % bJ;
            hb[(int)((v * NB) / bJ)]++; hb2[(int)((v * NF) / bJ)]++;
            double x = (double)(u64)(v >> 0) / (double)bJ;   // bJ < 2^64 for all runs
            for (int i = 0; i < nh; ++i) { double a = 2 * M_PI * fmod(H[i] * x, 1.0); bre[i] += cos(a); bim[i] += sin(a); }
        }
    }
    double tot = (double)NP * (double)bk;
    // ---- formula ----
    const char *regime; int formula_ok = 1;
    if (j <= 0) regime = "prefix-free";
    else if (j <= k + f) regime = (j <= t - 1) ? "linear-complete" : "linear-incomplete";
    else regime = "quadratic-in-prefix";
    u128 bj = j >= 1 ? POW[j] : 1, bkf = POW[k + f];
    // class weights: d = gcd(6R, b^j) -> count of R
    u64 dval[256]; u64 dcnt[256]; int nd = 0;
    if (!strcmp(regime, "prefix-free")) {
        for (u64 R = 0; R < bk; ++R) { u128 v = ((u128)3 * R * R) % bJ; hf[(int)((v * NB) / bJ)] += NP; hf2[(int)((v * NF) / bJ)] += NP; }
    } else if (!strcmp(regime, "linear-complete")) {
        for (u64 R = 0; R < bk; ++R) {
            u64 g = gcdu((u64)((6 * (u128)R) % bj), (u64)bj);   // gcd(6R, b^j); = b^j when b^j | 6R
            u64 q = (u64)bj / g, w = NP / q;
            if (NP % q) { fprintf(stderr, "internal: q does not divide NP\n"); return 3; }
            int di = 0; while (di < nd && dval[di] != g) ++di; if (di == nd) { dval[nd] = g; dcnt[nd++] = 0; } dcnt[di]++;
            u128 base = ((u128)3 * R * R) % bJ, step = (bkf * g) % bJ;
            u128 v = base;
            for (u64 i = 0; i < q; ++i) { hf[(int)((v * NB) / bJ)] += w; hf2[(int)((v * NF) / bJ)] += w; v += step; if (v >= bJ) v -= bJ; }
        }
    } else formula_ok = 0;
    // Fourier by formula (all j <= k+f), general Dirichlet-kernel form
    double *fre = calloc(nh, sizeof(double)), *fim = calloc(nh, sizeof(double));
    if (j <= k + f) {
        for (int i = 0; i < nh; ++i) {
            long double sr = 0, si = 0; u64 h = (u64)H[i];
            for (u64 R = 0; R < bk; ++R) {
                u128 ph = ((u128)3 * h % bJ) * (((u128)R * R) % bJ) % bJ;
                long double a = 2 * M_PI * (long double)(u64)ph / (long double)(u64)bJ;
                long double kr, ki;   // sum over Ptop of e(6hR Ptop / b^j), normalised by NP
                if (j <= 0) { kr = 1; ki = 0; }
                else {
                    u64 num = (u64)(((u128)6 * h % bj) * ((u128)R % bj) % bj);
                    if (num == 0) { kr = 1; ki = 0; }
                    else {
                        long double beta = (long double)num / (long double)(u64)bj;
                        // sum_{P=Pmin}^{Pmax-1} e(beta P) = e(beta Pmin)(e(beta NP)-1)/(e(beta)-1)
                        long double A = 2 * M_PI * fmodl(beta * (long double)Pmin, 1.0L), B = 2 * M_PI * fmodl(beta * (long double)NP, 1.0L), C = 2 * M_PI * beta;
                        long double nr = cosl(B) - 1, ni = sinl(B), dr = cosl(C) - 1, di2 = sinl(C);
                        long double den = dr * dr + di2 * di2;
                        long double qr = (nr * dr + ni * di2) / den, qi = (ni * dr - nr * di2) / den;
                        kr = (cosl(A) * qr - sinl(A) * qi) / NP; ki = (cosl(A) * qi + sinl(A) * qr) / NP;
                    }
                }
                sr += cosl(a) * kr - sinl(a) * ki; si += cosl(a) * ki + sinl(a) * kr;
            }
            fre[i] = (double)(sr / bk); fim[i] = (double)(si / bk);
        }
    }
    double devb = 0, devf = 0; int eq64 = 1, eq4096 = 1;
    for (int i = 0; i < NB; ++i) { devb = fmax(devb, fabs(hb[i] * (double)NB / tot - 1)); devf = fmax(devf, fabs(hf[i] * (double)NB / tot - 1)); if (hb[i] != hf[i]) eq64 = 0; }
    for (int i = 0; i < NF; ++i) if (hb2[i] != hf2[i]) eq4096 = 0;
    double maxfd = 0;
    printf("{\"b\":%d,\"L\":%d,\"t\":%d,\"k\":%d,\"f\":%d,\"P\":%d,\"J\":%d,\"j\":%d,\"regime\":\"%s\",\"batches\":%.0f,"
           "\"maxdev64_bruteforce\":%.5f,", b, L, t, k, f, P, J, j, regime, tot, devb);
    if (formula_ok) printf("\"maxdev64_formula\":%.5f,\"hist64_equal\":%s,\"hist4096_equal\":%s,", devf, eq64 ? "true" : "false", eq4096 ? "true" : "false");
    printf("\"fourier\":[");
    for (int i = 0; i < nh; ++i) {
        double br = bre[i] / tot, bi = bim[i] / tot;
        printf("%s{\"h\":%d,\"brute\":[%.6e,%.6e],\"abs\":%.6e", i ? "," : "", H[i], br, bi, hypot(br, bi));
        if (j <= k + f) { printf(",\"formula\":[%.6e,%.6e]", fre[i], fim[i]); maxfd = fmax(maxfd, hypot(br - fre[i], bi - fim[i])); }
        printf("}");
    }
    printf("],\"max_fourier_formula_error\":%.3e", maxfd);
    if (nd) { printf(",\"classes\":["); for (int i = 0; i < nd; ++i) printf("%s[%llu,%llu]", i ? "," : "", (unsigned long long)dval[i], (unsigned long long)dcnt[i]); printf("]"); }
    printf("}\n");
    return 0;
}
