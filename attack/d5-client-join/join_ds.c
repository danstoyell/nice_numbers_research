// join_ds.c -- copy of attack/p1-algorithm/overlap.c (join mode) with the
// client's digit-sum (mod b-1) residue filter added to the hash key, so the
// join and the client are compared with the same CRT filter. D5 addition:
// bottoms are bucketed by (overlap key, R_low mod (b-1)); each top P looks up
// one bucket per admissible class s - P (mod b-1), s in the digit-sum roots
// (n = P*b^F0 + R_low == P + R_low mod b-1). Lookups are counted; with DS=0
// the program is the original join. Extra last argument: DS (0/1).
//
// Original header of overlap.c follows.
// overlap.c -- exact k-nice search two ways, with work counters.
//
//   EDGE  (t + k = L):  bottom list B (n mod b^k, bottom k digits of n^2 and
//         n^3 certified) x top trie (prefixes of t digits, top digits of n^2
//         and n^3 certified on the prefix interval), walked with joint pruning.
//         Every trie leaf reached is one candidate n, fully checked.
//   JOIN  (t + k > L):  the same two lists but OVERLAPPING in o = t+k-L digits
//         of n, hash-joined on those shared digits. Each n in [lo,hi] is one
//         (P,R) pair; a key-equal pair ("match") costs one O(1) cross-check of
//         the certified digit counts; pairs that pass ("survivors") are fully
//         checked. Top certification is capped at position k so no output
//         position is counted by both lists.
//
// Soundness: a k-nice n uses no value more than K times in ANY subset of its
// output positions, so its prefix is in T, its residue is in B, and the pair
// passes the cross-check. Hence both modes return every k-nice n in [lo,hi].
//
// Build: clang -O3 -o overlap overlap.c -lpthread
// Run:   ./overlap edge B K LO HI S2 S3 T K_BOTTOM THREADS FULL
//        ./overlap join B K LO HI S2 S3 T K_BOTTOM P THREADS
//   (FULL=0 counts edge leaves without fully checking them.)
// Output: one JSON line.
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef unsigned __int128 u128;
typedef uint64_t u64;

static unsigned Bs, KM, S2, S3, L, NTHR;
static u64 LO, HI;
static u128 POW[64];
static u64 M33 = 0x3333333333333333ULL, H88 = 0x8888888888888888ULL, ADDK;

static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + 1e-9 * ts.tv_nsec; }

// ---- digit-count vectors: K==1 bitmask; K>=2 two-bit fields (b<=32) ----
static inline int cnt_add(u64 *c, unsigned d) {
    if (KM == 1) { u64 m = 1ULL << d; if (*c & m) return 0; *c |= m; return 1; }
    unsigned v = (unsigned)(*c >> (2 * d)) & 3u;
    if (v >= KM) return 0;
    *c += 1ULL << (2 * d);
    return 1;
}
static inline int cnt_ok(u64 a, u64 c) {
    if (KM == 1) return (a & c) == 0;
    u64 e = (a & M33) + (c & M33), o = ((a >> 2) & M33) + ((c >> 2) & M33);
    return (((e + ADDK) | (o + ADDK)) & H88) == 0;
}

// ---- full check (early exit on the first over-used value) ----
static u64 CHUNK; static unsigned CHUNKD;   // b^CHUNKD < 2^64
static inline int take_u64(u64 x, unsigned nd, unsigned *cnt) {
    for (unsigned i = 0; i < nd; ++i) { unsigned d = (unsigned)(x % Bs); x /= Bs; if (++cnt[d] > KM) return 0; }
    return 1;
}
static inline int take(u128 x, unsigned ndig, unsigned *cnt) {
    while (ndig > CHUNKD) {
        u128 q = x / CHUNK; u64 r = (u64)(x - q * CHUNK);
        if (!take_u64(r, CHUNKD, cnt)) return 0;
        x = q; ndig -= CHUNKD;
    }
    return take_u64((u64)x, ndig, cnt);
}
static int full_check(u64 n) {
    unsigned cnt[64] = {0};
    u128 sq = (u128)n * n;
    return take(sq, S2, cnt) && take(sq * n, S3, cnt);
}

// ---- top certification ----
typedef struct { u64 P; u64 cnt; uint8_t i2, i3; } Top;

// Extend prefix par (jp digits) by p digits with value v; cap = lowest position
// the top may certify. Returns 0 if the interval misses [LO,HI] or counts break.
static u64 top_calls;   // attempts (approximate under threads; informational)
static inline int cert_down(u128 a, u128 e, unsigned *ip, unsigned cap, u64 *cnt) {
    unsigned i = *ip;
    u128 diff = e - a;
    while (i > cap) {
        u128 pw = POW[i - 1];
        if (diff >= pw) break;                 // endpoints differ at position >= i-1
        u128 q = a / pw;
        if (e - q * pw >= pw) break;           // a carry separates them
        unsigned d = (q >> 64) ? (unsigned)(q % Bs) : (unsigned)((u64)q % Bs);
        if (!cnt_add(cnt, d)) return 0;
        --i;
    }
    *ip = i;
    return 1;
}
static inline int top_ext(const Top *par, unsigned jp, unsigned p, u64 v, unsigned cap, Top *out) {
    u64 P = par->P * (u64)POW[p] + v;
    unsigned j = jp + p;
    u128 w = POW[L - j];
    u128 A = (u128)P * w, E = A + w - 1;
    if (A < LO) A = LO;
    if (E > HI) E = HI;
    if (A > E) return 0;
    u64 cnt = par->cnt;
    unsigned i2 = par->i2, i3 = par->i3;
    u128 a2 = A * A, e2 = E * E;
    if (!cert_down(a2, e2, &i2, cap, &cnt)) return 0;
    if (!cert_down(a2 * A, e2 * E, &i3, cap, &cnt)) return 0;
    out->P = P; out->cnt = cnt; out->i2 = (uint8_t)i2; out->i3 = (uint8_t)i3;
    return 1;
}

// ---- growable arrays ----
typedef struct { void *a; size_t n, cap, sz; } Vec;
static void vpush(Vec *v, const void *x) {
    if (v->n == v->cap) { v->cap = v->cap ? 2 * v->cap : 1024; v->a = realloc(v->a, v->cap * v->sz); if (!v->a) { fprintf(stderr, "oom\n"); exit(1); } }
    memcpy((char *)v->a + v->n * v->sz, x, v->sz); v->n++;
}

// Top layer at depth `depth` (all surviving prefixes), cap as given; each level
// is expanded by NTHR threads.
static u64 top_nodes_built;
typedef struct { Top *par; size_t from, to; unsigned j, cap; Vec out; u64 calls; } LJob;
static void *layer_thread(void *arg) {
    LJob *jb = arg; Top ch;
    for (size_t i = jb->from; i < jb->to; ++i)
        for (unsigned d = 0; d < Bs; ++d) { jb->calls++; if (top_ext(&jb->par[i], jb->j, 1, d, jb->cap, &ch)) vpush(&jb->out, &ch); }
    return NULL;
}
static void top_layer(unsigned depth, unsigned cap, Vec *out) {
    Vec cur = {0, 0, 0, sizeof(Top)};
    Top root = {0, 0, (uint8_t)S2, (uint8_t)S3};
    vpush(&cur, &root);
    for (unsigned j = 0; j < depth; ++j) {
        pthread_t th[64]; LJob jobs[64];
        for (unsigned t = 0; t < NTHR; ++t) {
            jobs[t] = (LJob){(Top *)cur.a, cur.n * t / NTHR, cur.n * (t + 1) / NTHR, j, cap, {0, 0, 0, sizeof(Top)}, 0};
            pthread_create(&th[t], NULL, layer_thread, &jobs[t]);
        }
        Vec nxt = {0, 0, 0, sizeof(Top)};
        for (unsigned t = 0; t < NTHR; ++t) {
            pthread_join(th[t], NULL);
            top_calls += jobs[t].calls;
            for (size_t i = 0; i < jobs[t].out.n; ++i) vpush(&nxt, (Top *)jobs[t].out.a + i);
            free(jobs[t].out.a);
        }
        top_nodes_built += nxt.n;
        free(cur.a); cur = nxt;
    }
    *out = cur;
}

// ---- bottom list ----
typedef struct { u64 R; u64 cnt; } Bot;
static u64 bot_nodes_built;
static u64 bot_calls;
// DFS from a node at depth j to depth k; positions [f0, f0+p) forced to v.
static void bot_dfs(const Bot *node, unsigned j, unsigned k, unsigned f0, unsigned p, u64 v, Vec *out) {
    if (j == k) { vpush(out, node); return; }
    unsigned dlo = 0, dhi = Bs - 1;
    if (j >= f0 && j < f0 + p) { dlo = dhi = (unsigned)((v / (u64)POW[j - f0]) % Bs); }
    u64 R = node->R;
    unsigned u2 = 0, u3 = 0, s2 = 0, s3 = 0;
    if (j > 0) {
        u128 r2 = (u128)R * R, r3 = r2 * R;
        u2 = (unsigned)((r2 / POW[j]) % Bs); u3 = (unsigned)((r3 / POW[j]) % Bs);
        unsigned r0 = (unsigned)(R % Bs);
        s2 = 2 * r0 % Bs; s3 = 3 * (r0 * r0 % Bs) % Bs;
    }
    u64 pj = (u64)POW[j];
    __atomic_fetch_add(&bot_calls, dhi - dlo + 1, __ATOMIC_RELAXED);
    for (unsigned d = dlo; d <= dhi; ++d) {
        unsigned g2, g3;
        if (j == 0) { g2 = d * d % Bs; g3 = (d * d % Bs) * d % Bs; }
        else { g2 = (u2 + d * s2) % Bs; g3 = (u3 + d * s3) % Bs; }
        Bot ch = {R + (u64)d * pj, node->cnt};
        if (!cnt_add(&ch.cnt, g2) || !cnt_add(&ch.cnt, g3)) continue;
        __atomic_fetch_add(&bot_nodes_built, 1, __ATOMIC_RELAXED);
        bot_dfs(&ch, j + 1, k, f0, p, v, out);
    }
}

// ================= EDGE mode =================
typedef struct { u64 cnt; uint32_t first, nch; u64 P; } TNode;
static TNode **trie; static size_t *trie_n;
static unsigned TE, KE; static int FULL;
static Vec Blist;
typedef struct { size_t from, to; u64 visited, leaves, hits; u64 hitv[256]; unsigned nh; } EJob;

static void edge_walk(EJob *jb, unsigned depth, uint32_t idx, u64 rc, u64 R) {
    TNode *nd = &trie[depth][idx];
    jb->visited++;
    if (!cnt_ok(nd->cnt, rc)) return;
    if (depth == TE) {
        u64 n = nd->P * (u64)POW[KE] + R;
        if (n < LO || n > HI) return;
        jb->leaves++;
        if (FULL && full_check(n)) { if (jb->nh < 256) jb->hitv[jb->nh++] = n; jb->hits++; }
        return;
    }
    for (uint32_t c = 0; c < nd->nch; ++c) edge_walk(jb, depth + 1, nd->first + c, rc, R);
}
static void *edge_thread(void *arg) {
    EJob *jb = arg;
    for (size_t i = jb->from; i < jb->to; ++i) {
        Bot *b = (Bot *)Blist.a + i;
        edge_walk(jb, 0, 0, b->cnt, b->R);
    }
    return NULL;
}

static int cmp_u64(const void *a, const void *b) { u64 x = *(const u64 *)a, y = *(const u64 *)b; return x < y ? -1 : x > y; }

static void run_edge(void) {
    double t0 = now();
    // top trie, depth-by-depth, cap = KE
    trie = calloc(TE + 1, sizeof *trie); trie_n = calloc(TE + 1, sizeof *trie_n);
    Top *lay = malloc(sizeof(Top)); lay[0] = (Top){0, 0, (uint8_t)S2, (uint8_t)S3};
    size_t nl = 1;
    trie[0] = calloc(1, sizeof(TNode)); trie_n[0] = 1; trie[0][0] = (TNode){0, 0, 0, 0};
    for (unsigned j = 0; j < TE; ++j) {
        Vec nx = {0, 0, 0, sizeof(Top)};
        for (size_t i = 0; i < nl; ++i) {
            trie[j][i].first = (uint32_t)nx.n;
            Top ch;
            for (unsigned d = 0; d < Bs; ++d) { top_calls++; if (top_ext(&lay[i], j, 1, d, KE, &ch)) { vpush(&nx, &ch); top_nodes_built++; } }
            trie[j][i].nch = (uint32_t)(nx.n - trie[j][i].first);
        }
        free(lay); lay = nx.a; nl = nx.n;
        trie[j + 1] = calloc(nl ? nl : 1, sizeof(TNode)); trie_n[j + 1] = nl;
        for (size_t i = 0; i < nl; ++i) trie[j + 1][i] = (TNode){lay[i].cnt, 0, 0, lay[i].P};
    }
    free(lay);
    double t1 = now();
    // bottom list
    Blist = (Vec){0, 0, 0, sizeof(Bot)};
    Bot root = {0, 0};
    bot_dfs(&root, 0, KE, 0, 0, 0, &Blist);
    double t2 = now();
    pthread_t th[64]; EJob *jobs = calloc(NTHR, sizeof(EJob));
    for (unsigned i = 0; i < NTHR; ++i) {
        jobs[i].from = Blist.n * i / NTHR; jobs[i].to = Blist.n * (i + 1) / NTHR;
        pthread_create(&th[i], NULL, edge_thread, &jobs[i]);
    }
    u64 visited = 0, leaves = 0, hits = 0; Vec hv = {0, 0, 0, sizeof(u64)};
    for (unsigned i = 0; i < NTHR; ++i) {
        pthread_join(th[i], NULL);
        visited += jobs[i].visited; leaves += jobs[i].leaves; hits += jobs[i].hits;
        for (unsigned h = 0; h < jobs[i].nh; ++h) vpush(&hv, &jobs[i].hitv[h]);
    }
    double t3 = now();
    qsort(hv.a, hv.n, sizeof(u64), cmp_u64);
    printf("{\"mode\":\"edge\",\"base\":%u,\"mult\":%u,\"t\":%u,\"k\":%u,\"top_list\":%zu,\"top_nodes\":%llu,"
           "\"top_calls\":%llu,\"bottom_list\":%zu,\"bottom_nodes\":%llu,\"bottom_calls\":%llu,\"trie_visits\":%llu,\"leaves\":%llu,\"full\":%d,\"hits\":%llu,"
           "\"sec_top\":%.3f,\"sec_bottom\":%.3f,\"sec_walk\":%.3f,\"solutions\":[",
           Bs, KM, TE, KE, trie_n[TE], (unsigned long long)top_nodes_built, (unsigned long long)top_calls, Blist.n, (unsigned long long)bot_nodes_built, (unsigned long long)bot_calls,
           (unsigned long long)visited, (unsigned long long)leaves, FULL, (unsigned long long)hits, t1 - t0, t2 - t1, t3 - t2);
    for (size_t i = 0; i < hv.n; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)((u64 *)hv.a)[i]);
    printf("]}\n");
}

// ================= JOIN mode =================
static unsigned TT, KB, PP, OO, F0;
static Vec Tlay;            // top layer at depth TT-PP
static Vec Bpre;            // bottom layer at depth F0 (below the overlap)
static u64 next_v, NV;
static pthread_mutex_t vlock = PTHREAD_MUTEX_INITIALIZER;
typedef struct { u64 tcalls, tops, lookups, matches, survivors, hits; u64 hitv[256]; unsigned nh; double sec_b, sec_j; } JJob;
static int DS; static unsigned NROOTS, ROOTS[64], M1;

static void *join_thread(void *arg) {
    JJob *jb = arg;
    u64 keyspace = (u64)POW[OO - PP];
    u64 ncls = DS ? M1 : 1, nb = keyspace * ncls;
    uint32_t *off = malloc((nb + 1) * sizeof(uint32_t));
    Vec bl = {0, 0, 0, sizeof(Bot)};
    Bot *sorted = NULL; size_t scap = 0;
    for (;;) {
        pthread_mutex_lock(&vlock); u64 v = next_v++; pthread_mutex_unlock(&vlock);
        if (v >= NV) break;
        double ta = now();
        bl.n = 0;
        for (size_t i = 0; i < Bpre.n; ++i) bot_dfs((Bot *)Bpre.a + i, F0, KB, F0, PP, v, &bl);
        // counting sort by key = R / b^(F0+PP)
        memset(off, 0, (nb + 1) * sizeof(uint32_t));
        u64 kdiv = (u64)POW[F0 + PP], lowmod = (u64)POW[F0];
#define BKT(R) (((R) / kdiv) * ncls + (DS ? ((R) % lowmod) % M1 : 0))
        for (size_t i = 0; i < bl.n; ++i) off[BKT(((Bot *)bl.a)[i].R) + 1]++;
        for (u64 x = 0; x < nb; ++x) off[x + 1] += off[x];
        if (bl.n > scap) { scap = bl.n; sorted = realloc(sorted, scap * sizeof(Bot)); }
        for (size_t i = 0; i < bl.n; ++i) {
            Bot b = ((Bot *)bl.a)[i];
            u64 key = BKT(b.R);
            b.R %= lowmod;                  // keep only the non-overlap low part
            sorted[off[key]++] = b;
        }
        for (u64 x = nb; x > 0; --x) off[x] = off[x - 1];
        off[0] = 0;
        double tb = now();
        jb->sec_b += tb - ta;
        u64 pdiv = (u64)POW[PP];
        for (size_t i = 0; i < Tlay.n; ++i) {
            Top P;
            if (PP) { jb->tcalls++; if (!top_ext((Top *)Tlay.a + i, TT - PP, PP, v, KB, &P)) continue; }
            else P = ((Top *)Tlay.a)[i];
            jb->tops++;
            u64 key = (P.P / pdiv) % keyspace;
            unsigned pc = DS ? (unsigned)(P.P % M1) : 0;
            for (unsigned ri = 0; ri < (DS ? NROOTS : 1); ++ri) {
              u64 bk = key * ncls + (DS ? (ROOTS[ri] + M1 - pc) % M1 : 0);
              jb->lookups++;
              for (uint32_t x = off[bk]; x < off[bk + 1]; ++x) {
                jb->matches++;
                if (!cnt_ok(P.cnt, sorted[x].cnt)) continue;
                u64 n = P.P * lowmod + sorted[x].R;
                if (n < LO || n > HI) continue;
                jb->survivors++;
                if (full_check(n)) { if (jb->nh < 256) jb->hitv[jb->nh++] = n; jb->hits++; }
              }
            }
        }
        jb->sec_j += now() - tb;
    }
    free(off); free(bl.a); free(sorted);
    return NULL;
}

static void run_join(void) {
    double t0 = now();
    top_layer(TT - PP, KB, &Tlay);
    double t1 = now();
    Bpre = (Vec){0, 0, 0, sizeof(Bot)};
    Bot root = {0, 0};
    bot_dfs(&root, 0, F0, 0, 0, 0, &Bpre);
    NV = (u64)POW[PP]; next_v = 0;
    pthread_t th[64]; JJob *jobs = calloc(NTHR, sizeof(JJob));
    for (unsigned i = 0; i < NTHR; ++i) pthread_create(&th[i], NULL, join_thread, &jobs[i]);
    u64 tops = 0, lookups = 0, matches = 0, surv = 0, hits = 0; double sb = 0, sj = 0; Vec hv = {0, 0, 0, sizeof(u64)};
    for (unsigned i = 0; i < NTHR; ++i) {
        pthread_join(th[i], NULL);
        top_calls += jobs[i].tcalls; tops += jobs[i].tops; lookups += jobs[i].lookups; matches += jobs[i].matches; surv += jobs[i].survivors; hits += jobs[i].hits;
        sb += jobs[i].sec_b; sj += jobs[i].sec_j;
        for (unsigned h = 0; h < jobs[i].nh; ++h) vpush(&hv, &jobs[i].hitv[h]);
    }
    double t2 = now();
    qsort(hv.a, hv.n, sizeof(u64), cmp_u64);
    printf("{\"mode\":\"join\",\"ds\":%d,\"ds_classes\":%u,\"lookups\":%llu,\"base\":%u,\"mult\":%u,\"t\":%u,\"k\":%u,\"overlap\":%u,\"partition_digits\":%u,"
           "\"top_layer\":%zu,\"top_list\":%llu,\"top_nodes\":%llu,\"top_calls\":%llu,\"bottom_list_nodes\":%llu,\"bottom_calls\":%llu,\"matches\":%llu,"
           "\"survivors\":%llu,\"hits\":%llu,\"sec_top\":%.3f,\"sec_wall\":%.3f,\"cpu_bottom\":%.3f,\"cpu_join\":%.3f,\"solutions\":[",
           DS, DS ? NROOTS : 0, (unsigned long long)lookups, Bs, KM, TT, KB, OO, PP, Tlay.n, (unsigned long long)tops, (unsigned long long)top_nodes_built,
           (unsigned long long)top_calls, (unsigned long long)bot_nodes_built, (unsigned long long)bot_calls, (unsigned long long)matches, (unsigned long long)surv,
           (unsigned long long)hits, t1 - t0, t2 - t0, sb, sj);
    for (size_t i = 0; i < hv.n; ++i) printf("%s%llu", i ? "," : "", (unsigned long long)((u64 *)hv.a)[i]);
    printf("]}\n");
}

int main(int argc, char **argv) {
    if (argc < 11) { fprintf(stderr, "usage: see header\n"); return 2; }
    int edge = !strcmp(argv[1], "edge");
    Bs = atoi(argv[2]); KM = atoi(argv[3]);
    LO = strtoull(argv[4], 0, 10); HI = strtoull(argv[5], 0, 10);
    S2 = atoi(argv[6]); S3 = atoi(argv[7]);
    if ((KM >= 2 && Bs > 32) || Bs > 64 || KM > 3) { fprintf(stderr, "unsupported b/K\n"); return 2; }
    ADDK = (u64)(7 - KM) * 0x1111111111111111ULL;
    POW[0] = 1;
    CHUNK = 1; CHUNKD = 0; while ((u128)CHUNK * Bs < ((u128)1 << 64)) { CHUNK *= Bs; CHUNKD++; }
    for (unsigned i = 1; i < 64; ++i) POW[i] = POW[i - 1] * Bs;   // overflow beyond use is harmless
    L = 0; for (u64 x = HI; x; x /= Bs) L++;
    { unsigned l2 = 0; for (u64 x = LO; x; x /= Bs) l2++; if (l2 != L) { fprintf(stderr, "lo/hi lengths differ\n"); return 2; } }
    if (S3 > 38 || (double)HI * HI * HI > 3.3e38) { fprintf(stderr, "u128 overflow\n"); return 2; }
    if (edge) {
        TE = atoi(argv[8]); KE = atoi(argv[9]); NTHR = atoi(argv[10]); FULL = argc > 11 ? atoi(argv[11]) : 1;
        if (TE + KE != L) { fprintf(stderr, "edge needs t+k=L=%u\n", L); return 2; }
        run_edge();
    } else {
        TT = atoi(argv[8]); KB = atoi(argv[9]); PP = atoi(argv[10]); NTHR = argc > 11 ? atoi(argv[11]) : 1;
        DS = argc > 12 ? atoi(argv[12]) : 0;
        M1 = Bs - 1; NROOTS = 0;
        { unsigned long long tgt = ((unsigned long long)KM * Bs * (Bs - 1) / 2) % M1;
          for (unsigned long long r = 0; r < M1; ++r) if ((r * r + r * r * r) % M1 == tgt) ROOTS[NROOTS++] = (unsigned)r; }
        if (TT + KB <= L || TT > L || KB >= L) { fprintf(stderr, "join needs t+k>L, t<=L, k<L (L=%u)\n", L); return 2; }
        OO = TT + KB - L; F0 = L - TT;
        if (PP > OO) { fprintf(stderr, "p must be <= overlap %u\n", OO); return 2; }
        if ((double)POW[OO - PP] * (DS ? M1 : 1) > 3e8) { fprintf(stderr, "key space too large; raise p\n"); return 2; }
        run_join();
    }
    return 0;
}
