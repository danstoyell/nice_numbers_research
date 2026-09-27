#define _POSIX_C_SOURCE 200809L
#include "nice.h"
#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

typedef __uint128_t wide;
typedef struct { const char *raw; int64_t *v, min, max; size_t count; } alphabet;
typedef struct { unsigned long base; char *number; } solution;
typedef struct {
    uint64_t sum, carry2;
    wide carry3;
    size_t next;
    unsigned long d2, d3;
} frame;
typedef struct {
    unsigned long base, length;
    const alphabet *alpha;
    uint64_t nodes, complete, valid, *depths;
    const char *status, *obstruction;
    int sums_defined, elapsed_defined, best_defined;
    double elapsed;
    unsigned long modulus, *residues;
    size_t residue_count;
    uint64_t sum_lo, sum_hi;
    mpz_t best;
    size_t best_unique;
    char **solutions;
    size_t solution_count;
} record;
typedef struct {
    unsigned long max_base, node_limit, denominator_max, min_base;
    double seconds;
    const char *output, *snapshot;
    alphabet *alphabets;
    size_t alphabet_count;
} options;

static void *allocate(size_t n, size_t size) {
    if (size && n > SIZE_MAX / size) nice_die("allocation size overflow");
    void *p = calloc(n ? n : 1, size);
    if (!p) nice_die("cannot allocate dense-search workspace");
    return p;
}
static void *resize(void *p, size_t n, size_t size) {
    if (size && n > SIZE_MAX / size) nice_die("allocation size overflow");
    void *q = realloc(p, n * size);
    if (!q) nice_die("cannot grow dense-search output");
    return q;
}
static void json_string(FILE *out, const char *s) {
    fputc('"', out);
    for (const unsigned char *p = (const unsigned char *)s; *p; ++p) {
        if (*p == '"' || *p == '\\') { fputc('\\', out); fputc(*p, out); }
        else if (*p < 32) fprintf(out, "\\u%04x", *p);
        else fputc(*p, out);
    }
    fputc('"', out);
}
static void print_wide(FILE *out, wide value) {
    char s[40]; size_t used = 0;
    do { s[used++] = (char)('0' + value % 10); value /= 10; } while (value);
    while (used) fputc(s[--used], out);
}
static char *decimal(mpz_srcptr n) {
    char *s = allocate(mpz_sizeinbase(n, 10) + 2, 1);
    mpz_get_str(s, 10, n);
    return s;
}
static void clear_alphabets(options *o) {
    for (size_t i = 0; i < o->alphabet_count; ++i) free(o->alphabets[i].v);
    free(o->alphabets); o->alphabets = NULL; o->alphabet_count = 0;
}
static void add_alphabet(options *o, const char *text) {
    alphabet a = {.raw = text, .min = INT64_MAX, .max = INT64_MIN};
    const char *p = text;
    if (!*p) nice_die("alphabet must be a nonempty comma-separated integer list");
    for (;;) {
        char *end; errno = 0;
        long long value = strtoll(p, &end, 10);
        if (errno || end == p) nice_die("invalid or oversized alphabet digit");
        while (isspace((unsigned char)*end)) ++end;
        if (*end && *end != ',') nice_die("alphabet digits must be separated by commas");
        a.v = resize(a.v, a.count + 1, sizeof(*a.v));
        a.v[a.count++] = (int64_t)value;
        if (value < a.min) a.min = value;
        if (value > a.max) a.max = value;
        if (!*end) break;
        p = end + 1;
        if (!*p) nice_die("alphabet has an empty trailing digit");
    }
    o->alphabets = resize(o->alphabets, o->alphabet_count + 1, sizeof(*o->alphabets));
    o->alphabets[o->alphabet_count++] = a;
}
static int option_is(const char *arg, const char *name, const char **value) {
    size_t n = strlen(name);
    if (strncmp(arg, name, n) || (arg[n] && arg[n] != '=')) return 0;
    *value = arg[n] == '=' ? arg + n + 1 : NULL;
    return 1;
}
static const char *argument(int *i, int argc, char **argv, const char *inline_value) {
    if (inline_value) return inline_value;
    if (++*i >= argc) nice_die("missing option argument");
    return argv[*i];
}
static options parse_options(int argc, char **argv) {
    options o = {.max_base = 300, .node_limit = 250000, .seconds = 120,
        .output = "results/native-transformations-dense.jsonl", .denominator_max = 199,
        .min_base = 57, .snapshot = "results/public-near-misses-2026-09-23.json"};
    for (int i = 1; i < argc; ++i) {
        const char *value;
        if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-h")) {
            puts("Usage: dense-search [--max-base N] [--alphabets A,B [C,D ...]]\n"
                 "  [--node-limit N] [--seconds S] [--output PATH] [--mode dense]\n"
                 "Defaults: max-base=300; alphabets=2,3 1,2,3,4; node-limit=250000;\n"
                 "  seconds=120; output=results/native-transformations-dense.jsonl\n"
                 "Alphabet order and duplicate entries are preserved. Bases are limited to 1000000.");
            exit(EXIT_SUCCESS);
        } else if (option_is(argv[i], "--max-base", &value)) {
            o.max_base = nice_parse_ulong(argument(&i, argc, argv, value), 2, NICE_MAX_BASE, "invalid --max-base");
        } else if (option_is(argv[i], "--node-limit", &value)) {
            o.node_limit = nice_parse_ulong(argument(&i, argc, argv, value), 0, ULONG_MAX, "invalid --node-limit");
        } else if (option_is(argv[i], "--seconds", &value)) {
            const char *s = argument(&i, argc, argv, value); char *end;
            errno = 0; o.seconds = strtod(s, &end);
            if (errno || end == s || *end || !isfinite(o.seconds) || o.seconds < 0)
                nice_die("--seconds must be finite and nonnegative");
        } else if (option_is(argv[i], "--output", &value)) {
            o.output = argument(&i, argc, argv, value);
            if (!*o.output) nice_die("--output must not be empty");
        } else if (option_is(argv[i], "--mode", &value)) {
            if (strcmp(argument(&i, argc, argv, value), "dense")) nice_die("this executable supports only --mode dense");
        } else if (option_is(argv[i], "--denominator-max", &value)) {
            o.denominator_max = nice_parse_ulong(argument(&i, argc, argv, value), 0, ULONG_MAX, "invalid --denominator-max");
        } else if (option_is(argv[i], "--min-base", &value)) {
            o.min_base = nice_parse_ulong(argument(&i, argc, argv, value), 0, ULONG_MAX, "invalid --min-base");
        } else if (option_is(argv[i], "--snapshot", &value)) {
            o.snapshot = argument(&i, argc, argv, value);
        } else if (option_is(argv[i], "--alphabets", &value)) {
            clear_alphabets(&o);
            if (value) add_alphabet(&o, value);
            while (i + 1 < argc && strncmp(argv[i + 1], "--", 2) && strcmp(argv[i + 1], "-h"))
                add_alphabet(&o, argv[++i]);
            if (!o.alphabet_count) nice_die("--alphabets requires at least one alphabet");
        } else nice_die("unknown option; use --help");
    }
    if (!o.alphabet_count) { add_alphabet(&o, "2,3"); add_alphabet(&o, "1,2,3,4"); }
    return o;
}

/* Sums are periodic modulo b-1. This compact representation has exactly the
   same sorted values as Python's range/filter and bisect_left, without a list
   that can grow quadratically with the base. */
static int first_sum(const record *r, uint64_t lower, uint64_t *answer) {
    if (!r->residue_count) return 0;
    uint64_t block = lower / r->modulus;
    unsigned long residue = (unsigned long)(lower % r->modulus);
    size_t lo = 0, hi = r->residue_count;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (r->residues[mid] < residue) lo = mid + 1; else hi = mid;
    }
    if (lo == r->residue_count) { ++block; lo = 0; }
    *answer = block * r->modulus + r->residues[lo];
    return 1;
}
static int sums_intersect(const record *r, uint64_t lower, uint64_t upper) {
    uint64_t value;
    return first_sum(r, lower, &value) && value <= upper;
}
static int used_digit(const uint64_t *used, unsigned long d) {
    return (used[d / 64] >> (d % 64)) & 1;
}
static void set_digit(uint64_t *used, unsigned long d) { used[d / 64] |= UINT64_C(1) << (d % 64); }
static void clear_digit(uint64_t *used, unsigned long d) { used[d / 64] &= ~(UINT64_C(1) << (d % 64)); }

static void search(record *r, nice_workspace *work, unsigned long node_limit, double deadline) {
    double start = nice_now();
    unsigned long b = r->base, length = r->length;
    const alphabet *a = r->alpha;
    r->status = "exhaustive";
    r->depths = allocate((size_t)length + 1, sizeof(*r->depths));
    mpz_init(r->best);
    if (a->min <= 0 || a->max >= (int64_t)b) { r->status = "invalid_alphabet"; return; }
    mpz_t lo, hi, repunit, endpoint, n, place;
    mpz_inits(lo, hi, repunit, endpoint, n, place, NULL);
    unsigned long square_length, cube_length;
    int exists = nice_bounds(lo, hi, b, &square_length, &cube_length);
    mpz_ui_pow_ui(repunit, b, length);
    mpz_sub_ui(repunit, repunit, 1); mpz_divexact_ui(repunit, repunit, b - 1);
    mpz_mul_ui(endpoint, repunit, (unsigned long)a->min);
    int length_obstruction = !exists || mpz_cmp(endpoint, hi) > 0;
    mpz_mul_ui(endpoint, repunit, (unsigned long)a->max);
    if (length_obstruction || mpz_cmp(endpoint, lo) < 0) {
        r->obstruction = "length_interval"; goto finish;
    }
    r->sums_defined = 1; r->modulus = b - 1;
    r->sum_lo = (uint64_t)a->min * length; r->sum_hi = (uint64_t)a->max * length;
    r->residues = allocate(r->modulus, sizeof(*r->residues));
    unsigned long target = (unsigned long)((wide)b * r->modulus / 2 % r->modulus);
    for (unsigned long s = 0; s < r->modulus; ++s)
        if ((wide)s * s * (s + 1) % r->modulus == target) r->residues[r->residue_count++] = s;
    if (!sums_intersect(r, r->sum_lo, r->sum_hi)) {
        r->obstruction = "digit_sum_congruence"; goto finish;
    }
    frame *frames = allocate((size_t)length + 1, sizeof(*frames));
    unsigned long *digits = allocate(length, sizeof(*digits));
    uint64_t *squares = allocate(length, sizeof(*squares));
    uint64_t *used = allocate((b + 63) / 64, sizeof(*used));
    unsigned long depth = 0; int entering = 1;
    mpz_set_ui(n, 0); mpz_set_ui(place, 1);
    for (;;) {
        frame *f = &frames[depth];
        if (entering) {
            /* Identical to Python: the cap is checked only on entering a
               suffix-valid child, before incrementing its node counter. */
            if (r->nodes >= node_limit) { r->status = "node_limit"; break; }
            if (!(r->nodes % 1024) && nice_now() >= deadline) { r->status = "time_limit"; break; }
            ++r->nodes; ++r->depths[depth]; f->next = 0;
            unsigned long left = length - depth;
            if (!sums_intersect(r, f->sum + (uint64_t)a->min * left,
                                  f->sum + (uint64_t)a->max * left)) goto leave;
            if (!left) {
                ++r->complete;
                nice_stats assessed = nice_assess(work, n, b);
                if (assessed.square_digits + assessed.cube_digits == b) {
                    ++r->valid;
                    if (!r->best_defined || assessed.distinct_digits > r->best_unique) {
                        r->best_defined = 1; r->best_unique = assessed.distinct_digits; mpz_set(r->best, n);
                    }
                    if (assessed.distinct_digits == b) {
                        r->solutions = resize(r->solutions, r->solution_count + 1, sizeof(*r->solutions));
                        r->solutions[r->solution_count++] = decimal(n);
                    }
                }
                goto leave;
            }
            entering = 0;
        }
        if (f->next == a->count) goto leave;
        unsigned long x = (unsigned long)a->v[f->next++];
        digits[depth] = x;
        uint64_t q = 0;
        for (unsigned long i = 0; i <= depth; ++i) q += (uint64_t)digits[i] * digits[depth - i];
        squares[depth] = q;
        wide cube_coefficient = 0;
        for (unsigned long i = 0; i <= depth; ++i) cube_coefficient += (wide)squares[i] * digits[depth - i];
        uint64_t value2 = q + f->carry2;
        wide value3 = cube_coefficient + f->carry3;
        unsigned long d2 = (unsigned long)(value2 % b), d3 = (unsigned long)(value3 % b);
        if (d2 == d3 || used_digit(used, d2) || used_digit(used, d3)) continue;
        set_digit(used, d2); set_digit(used, d3);
        frame *child = &frames[depth + 1];
        child->sum = f->sum + x; child->carry2 = value2 / b; child->carry3 = value3 / b;
        child->d2 = d2; child->d3 = d3;
        mpz_addmul_ui(n, place, x); mpz_mul_ui(place, place, b);
        ++depth; entering = 1; continue;
leave:
        if (!depth) break;
        clear_digit(used, frames[depth].d2); clear_digit(used, frames[depth].d3);
        --depth; mpz_divexact_ui(place, place, b); mpz_submul_ui(n, place, digits[depth]);
        entering = 0;
    }
    free(frames); free(digits); free(squares); free(used);
    r->elapsed_defined = 1; r->elapsed = nice_now() - start;
finish:
    mpz_clears(lo, hi, repunit, endpoint, n, place, NULL);
}

static void write_record(FILE *out, const record *r) {
    fprintf(out, "{\"base\":%lu,\"alphabet\":[", r->base);
    for (size_t i = 0; i < r->alpha->count; ++i) fprintf(out, "%s%" PRId64, i ? "," : "", r->alpha->v[i]);
    fprintf(out, "],\"input_digits\":%lu,\"nodes\":%" PRIu64 ",\"nodes_by_depth\":[", r->length, r->nodes);
    for (unsigned long i = 0; i <= r->length; ++i) fprintf(out, "%s%" PRIu64, i ? "," : "", r->depths[i]);
    fprintf(out, "],\"complete_prefixes\":%" PRIu64 ",\"length_valid\":%" PRIu64 ",\"solutions\":[", r->complete, r->valid);
    for (size_t i = 0; i < r->solution_count; ++i) { if (i) fputc(',', out); json_string(out, r->solutions[i]); }
    fputs("],\"status\":", out); json_string(out, r->status); fputs(",\"best\":", out);
    if (!r->best_defined) fputs("null", out);
    else gmp_fprintf(out, "{\"number\":\"%Zd\",\"unique_digits\":%zu,\"missing_count\":%zu}",
                     r->best, r->best_unique, (size_t)r->base - r->best_unique);
    if (r->sums_defined) {
        fputs(",\"allowed_digit_sums\":[", out);
        uint64_t value; int comma = 0;
        if (first_sum(r, r->sum_lo, &value)) while (value <= r->sum_hi) {
            fprintf(out, "%s%" PRIu64, comma ? "," : "", value); comma = 1;
            if (!first_sum(r, value + 1, &value)) break;
        }
        fputc(']', out);
    }
    if (r->obstruction) { fputs(",\"obstruction\":", out); json_string(out, r->obstruction); }
    if (r->elapsed_defined) fprintf(out, ",\"elapsed_seconds\":%.9f", r->elapsed);
    fputs("}\n", out);
    if (fflush(out) || ferror(out)) nice_die("cannot write dense-search output");
}

int main(int argc, char **argv) {
    options o = parse_options(argc, argv);
    double start = nice_now(), deadline = start + o.seconds;
    if (!isfinite(deadline)) nice_die("--seconds deadline is too large");
    FILE *out = fopen(o.output, "w");
    if (!out) nice_die("cannot open dense-search output file");
    nice_workspace work; nice_init(&work, o.max_base);
    uint64_t records = 0, exhaustive = 0, node_limited = 0, time_limited = 0;
    wide nodes = 0; unsigned long last_base = 0;
    solution *solutions = NULL; size_t solution_count = 0;
    for (unsigned long b = 2; b <= o.max_base; ++b) {
        if (b % 5 == 1 || b % 4 == 3) continue;
        for (size_t ai = 0; ai < o.alphabet_count; ++ai) {
            if (o.alphabets[ai].max >= (int64_t)b) continue;
            if (nice_now() >= deadline) break;
            record r = {.base = b, .length = (b - 2) / 5 + 1, .alpha = &o.alphabets[ai]};
            search(&r, &work, o.node_limit, deadline);
            write_record(out, &r);
            ++records; last_base = b; nodes += r.nodes;
            exhaustive += !strcmp(r.status, "exhaustive");
            node_limited += !strcmp(r.status, "node_limit");
            time_limited += !strcmp(r.status, "time_limit");
            for (size_t j = 0; j < r.solution_count; ++j) {
                solutions = resize(solutions, solution_count + 1, sizeof(*solutions));
                solutions[solution_count++] = (solution){b, r.solutions[j]};
            }
            free(r.solutions); free(r.residues); free(r.depths); mpz_clear(r.best);
        }
        if (nice_now() >= deadline) break;
    }
    if (fclose(out)) nice_die("cannot close dense-search output file");
    fputs("{\"parameters\":{\"mode\":\"dense\",\"denominator_max\":", stdout);
    printf("%lu,\"min_base\":%lu,\"snapshot\":", o.denominator_max, o.min_base); json_string(stdout, o.snapshot);
    printf(",\"max_base\":%lu,\"alphabets\":[", o.max_base);
    for (size_t i = 0; i < o.alphabet_count; ++i) { if (i) putchar(','); json_string(stdout, o.alphabets[i].raw); }
    printf("],\"node_limit\":%lu,\"seconds\":%.17g,\"output\":", o.node_limit, o.seconds); json_string(stdout, o.output);
    printf("},\"elapsed_seconds\":%.9f,\"records\":%" PRIu64 ",\"nodes\":", nice_now() - start, records);
    print_wide(stdout, nodes);
    printf(",\"exhaustive\":%" PRIu64 ",\"node_limited\":%" PRIu64 ",\"time_limited\":%" PRIu64 ",\"last_base\":", exhaustive, node_limited, time_limited);
    if (last_base) printf("%lu", last_base); else fputs("null", stdout);
    fputs(",\"solutions\":[", stdout);
    for (size_t i = 0; i < solution_count; ++i) {
        if (i) putchar(','); printf("[%lu,", solutions[i].base); json_string(stdout, solutions[i].number); putchar(']');
        free(solutions[i].number);
    }
    puts("]}");
    free(solutions); nice_clear(&work); clear_alphabets(&o);
    return EXIT_SUCCESS;
}
