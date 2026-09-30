// smc.c -- H2 prototype: subset simulation (sequential Monte Carlo with MCMC
// rejuvenation) for K-nice roots, against uniform random sampling.
//
// Score phi(n) = sum over digit values a of max(0, count_a(n^2 || n^3) - K).
// phi == 0 iff n is K-nice (the interval fixes the total length K*b).
//
// One run: level 0 is P uniform roots in [lo, hi]. Repeat:
//   tau  = the p0-quantile of phi over the population (keep phi <= tau);
//   seeds = members with phi <= tau (each keeps its level-0 ancestor id);
//   rejuvenate: cycle through the seeds, running Metropolis chains with the hard
//   indicator phi <= tau; every visited state (moves that are rejected repeat the
//   current state) enters the new population until it has P members again.
// An episode ends when tau == 0 (witnesses in hand) or when the threshold has not
// decreased for max_stall levels; a fresh population then starts a new episode, until
// the evaluation budget is spent. Level statistics are printed for the first episode.
//
// Proposals (mode):
//   0  change one digit of n at a uniformly random position to a random value;
//   1  change one of the top two digits only (keeps the bottom output digits);
//   2  each step picks mode 0 or 1 with probability 1/2;
//   9  control: plain uniform random sampling with the same budget.
// A proposal outside [lo, hi] is rejected.
//
// Build: clang -O3 -o smc smc.c
// Run:   ./smc b K lo hi s c L P p0 runs seed mode budget thin max_stall
//   thin = proposals per kept state in each chain; max_stall = levels without a lower
//   threshold before giving up.
// Output: one JSON line per run with per-level statistics, evaluations, distinct
// witnesses found (each re-verified exactly by recomputing phi), and distinct
// level-0 ancestors surviving at each level (diversity).
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned __int128 u128;
typedef uint64_t u64;

static int B, K, S2, S3, L, P, MODE, THIN, MAXSTALL;
static u64 LO, HI, BUDGET;
static double P0;
static u128 POW[64];
static u64 CHUNK; static int CHUNKD;

static u64 rng_s;
static inline u64 rnd(void) { u64 z = (rng_s += 0x9E3779B97F4A7C15ULL); z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
static inline double unif(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }
static inline u64 rnd_below(u64 n) { return rnd() % n; }

static inline void count_u64(u64 x, int nd, int *cnt) { for (int i = 0; i < nd; ++i) { cnt[x % B]++; x /= B; } }
static void count_digits(u128 x, int ndig, int *cnt) {
    while (ndig > CHUNKD) { u128 q = x / CHUNK; u64 r = (u64)(x - q * CHUNK); count_u64(r, CHUNKD, cnt); x = q; ndig -= CHUNKD; }
    count_u64((u64)x, ndig, cnt);
}
static u64 evals;
static int phi(u64 n) {
    int cnt[64]; for (int a = 0; a < B; ++a) cnt[a] = 0;
    u128 sq = (u128)n * n; count_digits(sq, S2, cnt); count_digits(sq * n, S3, cnt);
    int e = 0; for (int a = 0; a < B; ++a) if (cnt[a] > K) e += cnt[a] - K;
    ++evals; return e;
}
static inline int digit_at(u64 n, int i) { return (int)((n / (u64)POW[i]) % B); }
static u64 propose(u64 n) {
    int i;
    int m = MODE == 2 ? (int)(rnd() & 1) : MODE;
    if (m == 0) i = (int)rnd_below(L); else i = L - 1 - (int)rnd_below(2);
    int d = digit_at(n, i), d2 = (int)rnd_below(B - 1); if (d2 >= d) d2++;
    long long delta = (long long)(d2 - d) * (long long)(u64)POW[i];
    long long nn = (long long)n + delta;
    if (nn < (long long)LO || nn > (long long)HI) return n;   // reject: out of range
    return (u64)nn;
}

typedef struct { u64 n; int f; int anc; } Member;
static int cmp_f(const void *a, const void *b) { int x = ((const Member *)a)->f, y = ((const Member *)b)->f; return (x > y) - (x < y); }

static int cmp_u64(const void *a, const void *b) { u64 x = *(const u64 *)a, y = *(const u64 *)b; return (x > y) - (x < y); }

int main(int argc, char **argv) {
    if (argc < 16) { fprintf(stderr, "usage: %s b K lo hi s c L P p0 runs seed mode budget thin max_stall\n", argv[0]); return 2; }
    B = atoi(argv[1]); K = atoi(argv[2]); LO = strtoull(argv[3], 0, 10); HI = strtoull(argv[4], 0, 10);
    S2 = atoi(argv[5]); S3 = atoi(argv[6]); L = atoi(argv[7]); P = atoi(argv[8]); P0 = atof(argv[9]);
    int runs = atoi(argv[10]); rng_s = strtoull(argv[11], 0, 10); MODE = atoi(argv[12]); BUDGET = strtoull(argv[13], 0, 10); THIN = atoi(argv[14]); MAXSTALL = atoi(argv[15]);
    POW[0] = 1; for (int i = 1; i < 64; ++i) POW[i] = POW[i - 1] * B;
    CHUNKD = 0; { u64 p = 1; while (p <= UINT64_MAX / B) { p *= B; ++CHUNKD; } CHUNK = p; }
    Member *pop = malloc(sizeof(Member) * P), *nxt = malloc(sizeof(Member) * P);
    u64 *wit = malloc(sizeof(u64) * 4 * P); int nwit;
    int *anc_seen = malloc(sizeof(int) * P);
    for (int run = 0; run < runs; ++run) {
        evals = 0; nwit = 0;
        if (MODE == 9) {   // control: uniform random sampling with the same budget and the same phi
            u64 *rw = malloc(sizeof(u64) * (BUDGET / 1000 + 16)); int nrw = 0;
            while (evals < BUDGET) { u64 n = LO + rnd_below(HI - LO + 1); if (phi(n) == 0 && nrw < (int)(BUDGET / 1000 + 15)) rw[nrw++] = n; }
            qsort(rw, nrw, sizeof(u64), cmp_u64);
            int distinct = 0; for (int i = 0; i < nrw; ++i) if (i == 0 || rw[i] != rw[i - 1]) distinct++;
            printf("{\"run\":%d,\"mode\":9,\"P\":0,\"p0\":0,\"levels\":[],\"evals\":%llu,\"distinct_witnesses\":%d,\"witnesses\":[", run, (unsigned long long)evals, distinct);
            int first = 1; for (int i = 0; i < nrw; ++i) if (i == 0 || rw[i] != rw[i - 1]) { printf("%s%llu", first ? "" : ",", (unsigned long long)rw[i]); first = 0; }
            printf("]}\n"); fflush(stdout); free(rw); continue;
        }
        int episodes = 0, ep_levels_sum = 0, ep_tau0 = 0, ep_stalled = 0;
        printf("{\"run\":%d,\"mode\":%d,\"P\":%d,\"p0\":%.3f,\"levels\":[", run, MODE, P, P0);
        while (evals < BUDGET) {   // episodes: fresh population each time the previous one finished or stalled
        for (int i = 0; i < P; ++i) { u64 n = LO + rnd_below(HI - LO + 1); pop[i].n = n; pop[i].f = phi(n); pop[i].anc = i; }
        int level = 0, tau_prev = 1 << 30, stall = 0, done = 0, first_ep = (episodes == 0);
        while (!done) {
            qsort(pop, P, sizeof(Member), cmp_f);
            int q = (int)(P0 * P); if (q < 1) q = 1;
            int tau = pop[q - 1].f;
            int nseed = 0; while (nseed < P && pop[nseed].f <= tau) ++nseed;
            // diversity: distinct ancestors among the whole population and among the seeds
            memset(anc_seen, 0, sizeof(int) * P);
            int div_pop = 0; for (int i = 0; i < P; ++i) if (!anc_seen[pop[i].anc]) { anc_seen[pop[i].anc] = 1; ++div_pop; }
            memset(anc_seen, 0, sizeof(int) * P);
            int div_seed = 0; for (int i = 0; i < nseed; ++i) if (!anc_seen[pop[i].anc]) { anc_seen[pop[i].anc] = 1; ++div_seed; }
            int minf = pop[0].f;
            if (tau == 0) {
                // collect distinct witnesses
                for (int i = 0; i < nseed && nwit < 4 * P; ++i) wit[nwit++] = pop[i].n;
                if (first_ep) printf("%s{\"level\":%d,\"tau\":0,\"min_phi\":%d,\"seeds\":%d,\"distinct_ancestors_pop\":%d,\"distinct_ancestors_seeds\":%d,\"accept\":null,\"evals\":%llu}",
                       level ? "," : "", level, minf, nseed, div_pop, div_seed, (unsigned long long)evals);
                ep_tau0++; done = 1; break;
            }
            if (tau >= tau_prev) { if (++stall >= MAXSTALL) { if (first_ep) printf("%s{\"level\":%d,\"tau\":%d,\"min_phi\":%d,\"seeds\":%d,\"distinct_ancestors_pop\":%d,\"distinct_ancestors_seeds\":%d,\"accept\":null,\"evals\":%llu,\"stalled\":true}", level ? "," : "", level, tau, minf, nseed, div_pop, div_seed, (unsigned long long)evals); ep_stalled++; break; } }
            else stall = 0;
            tau_prev = tau;
            // rejuvenation
            u64 acc = 0, tries = 0; int filled = 0, si = 0;
            // also harvest any exact witnesses seen during chains
            while (filled < P) {
                Member cur = pop[si % nseed]; ++si;
                int steps = (P + nseed - 1) / nseed;
                for (int st = 0; st < steps && filled < P; ++st) {
                    for (int th = 0; th < THIN; ++th) {
                        u64 cand = propose(cur.n);
                        if (cand != cur.n) {
                            int fc = phi(cand); ++tries;
                            if (fc <= tau) { cur.n = cand; cur.f = fc; ++acc; }
                            if (fc == 0 && nwit < 4 * P) wit[nwit++] = cand;
                        } else ++tries;
                    }
                    nxt[filled++] = cur;
                }
                if (evals > BUDGET) break;
            }
            if (first_ep) printf("%s{\"level\":%d,\"tau\":%d,\"min_phi\":%d,\"seeds\":%d,\"distinct_ancestors_pop\":%d,\"distinct_ancestors_seeds\":%d,\"accept\":%.5f,\"evals\":%llu}",
                   level ? "," : "", level, tau, minf, nseed, div_pop, div_seed, tries ? (double)acc / tries : 0.0, (unsigned long long)evals);
            if (evals > BUDGET) { done = 1; break; }
            // fill remainder if the loop ended early (cannot happen unless budget)
            for (int i = filled; i < P; ++i) nxt[i] = pop[i % nseed];
            Member *t = pop; pop = nxt; nxt = t; ++level;
        }
        // harvest: any phi==0 in the population
        for (int i = 0; i < P; ++i) if (pop[i].f == 0 && nwit < 4 * P) wit[nwit++] = pop[i].n;
        episodes++; ep_levels_sum += level;
        }   // end of episodes
        qsort(wit, nwit, sizeof(u64), cmp_u64);
        int distinct = 0; u64 *dw = malloc(sizeof(u64) * (nwit + 1));
        for (int i = 0; i < nwit; ++i) if (i == 0 || wit[i] != wit[i - 1]) { if (phi(wit[i]) == 0) dw[distinct++] = wit[i]; }
        printf("],\"episodes\":%d,\"episodes_reaching_tau0\":%d,\"episodes_stalled\":%d,\"mean_levels_per_episode\":%.2f,\"evals\":%llu,\"distinct_witnesses\":%d,\"witnesses\":[",
               episodes, ep_tau0, ep_stalled, episodes ? (double)ep_levels_sum / episodes : 0.0, (unsigned long long)evals, distinct);
        for (int i = 0; i < distinct; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)dw[i]);
        printf("]}\n"); fflush(stdout); free(dw);
    }
    return 0;
}
