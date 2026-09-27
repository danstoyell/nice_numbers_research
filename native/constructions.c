/* Exact GMP port of scripts/constructions.py.
 * Generation order, conditional Counter keys, first-wins best-score ties,
 * and cross-family duplicate counting intentionally match the Python oracle.
 */
#include <stdio.h> /* GMP's FILE-based declarations need this before gmp.h. */
#include "nice.h"
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

enum family {
    TWO_PLUS, TWO_MINUS, NEAR_POWER, STRETCH_69, ARITHMETIC, RATIONAL,
    FAMILY_COUNT
};

static const char *const family_names[FAMILY_COUNT] = {
    "two_blocks_plus", "two_blocks_minus", "near_power", "stretch_69",
    "arithmetic_digits", "rational_fraction"
};

typedef struct {
    long max_base, coefficient_max, denominator_max;
    const char *output;
} options;

typedef struct {
    unsigned long long generated, modular, length_valid;
} counters;

typedef struct {
    unsigned long base;
    size_t distinct;
    enum family family;
    char *number;
} best_record;

typedef struct {
    unsigned long base;
    mpz_t number;
} solution;

typedef struct {
    options args;
    nice_workspace work;
    counters counts[FAMILY_COUNT];
    enum family family_order[FAMILY_COUNT];
    size_t family_count;
    size_t current_best[FAMILY_COUNT];
    best_record *best;
    size_t best_count, best_capacity;
    solution *solutions;
    size_t solution_count, solution_capacity;
    double elapsed;
} search;

static void *grow_array(void *old, size_t *capacity, size_t element_size) {
    size_t next = *capacity ? *capacity * 2 : 16;
    if (next < *capacity || next > SIZE_MAX / element_size)
        nice_die("construction result allocation is too large");
    void *result = realloc(old, next * element_size);
    if (!result) nice_die("cannot allocate construction results");
    *capacity = next;
    return result;
}

static char *decimal_copy(mpz_srcptr value) {
    size_t length = mpz_sizeinbase(value, 10);
    if (length > SIZE_MAX - 2) nice_die("integer string is too large");
    char *result = malloc(length + 2);
    if (!result) nice_die("cannot allocate integer string");
    mpz_get_str(result, 10, value);
    return result;
}

static void increment(unsigned long long *counter) {
    if (*counter == ULLONG_MAX) nice_die("construction count overflow");
    ++*counter;
}

static unsigned long gcd_ulong(unsigned long a, unsigned long b) {
    while (b) {
        unsigned long remainder = a % b;
        a = b;
        b = remainder;
    }
    return a;
}

static void remember_solution(search *state, unsigned long base,
                              mpz_srcptr number) {
    for (size_t i = 0; i < state->solution_count; ++i) {
        if (state->solutions[i].base == base &&
            mpz_cmp(state->solutions[i].number, number) == 0)
            return;
    }
    if (state->solution_count == state->solution_capacity)
        state->solutions = grow_array(state->solutions,
                                     &state->solution_capacity,
                                     sizeof(*state->solutions));
    solution *entry = &state->solutions[state->solution_count++];
    entry->base = base;
    mpz_init_set(entry->number, number);
}

static void assess_candidate(search *state, enum family family,
                             mpz_srcptr number, unsigned long base) {
    counters *count = &state->counts[family];
    if (!count->generated)
        state->family_order[state->family_count++] = family;
    increment(&count->generated);
    if (mpz_sgn(number) <= 0 || !nice_sum_allowed(number, base)) return;
    increment(&count->modular);
    nice_stats stats = nice_assess(&state->work, number, base);
    if (stats.square_digits + stats.cube_digits != base) return;
    increment(&count->length_valid);

    size_t index = state->current_best[family];
    if (index == SIZE_MAX) {
        if (state->best_count == state->best_capacity)
            state->best = grow_array(state->best, &state->best_capacity,
                                    sizeof(*state->best));
        index = state->best_count++;
        state->current_best[family] = index;
        state->best[index] = (best_record){
            .base = base, .distinct = stats.distinct_digits,
            .family = family, .number = decimal_copy(number)
        };
    } else if (stats.distinct_digits > state->best[index].distinct) {
        free(state->best[index].number);
        state->best[index].number = decimal_copy(number);
        state->best[index].distinct = stats.distinct_digits;
    }
    if (stats.distinct_digits == base)
        remember_solution(state, base, number);
}

static void generate_base(search *state, unsigned long base) {
    const unsigned long k = (base - 2) / 5;
    const unsigned long modulus = base - 1;
    long limit = state->args.coefficient_max;
    if (limit > (long)modulus) limit = (long)modulus;
    for (size_t i = 0; i < FAMILY_COUNT; ++i)
        state->current_best[i] = SIZE_MAX;

    mpz_t power, scale, anchor, candidate, repunit, weighted, shift;
    mpz_inits(power, scale, anchor, candidate, repunit, weighted, shift, NULL);
    mpz_ui_pow_ui(power, base, k);
    mpz_mul_ui(scale, power, base);

    /* Python interleaves plus/minus candidates for each (a,c). */
    for (long a = 1; a <= limit; ++a) {
        mpz_mul_ui(anchor, power, (unsigned long)a);
        for (long c = 1; c <= limit; ++c) {
            mpz_add_ui(candidate, anchor, (unsigned long)c);
            assess_candidate(state, TWO_PLUS, candidate, base);
            if (a >= 2) {
                mpz_sub_ui(candidate, anchor, (unsigned long)c);
                assess_candidate(state, TWO_MINUS, candidate, base);
            }
        }
    }
    for (long c = 1; c <= limit; ++c) {
        mpz_sub_ui(candidate, scale, (unsigned long)c);
        assess_candidate(state, NEAR_POWER, candidate, base);
    }
    mpz_mul_ui(candidate, power, 6);
    mpz_add_ui(candidate, candidate, 9);
    assess_candidate(state, STRETCH_69, candidate, base);

    if (k) {
        /* U=sum b^j, V=sum j*b^j. Using these exact identities avoids
         * rebuilding each AP integer, without changing its generation order. */
        mpz_sub_ui(repunit, scale, 1);
        mpz_divexact_ui(repunit, repunit, modulus);
        mpz_mul_ui(weighted, scale, k * modulus - 1);
        mpz_add_ui(weighted, weighted, base);
        mpz_divexact_ui(weighted, weighted, modulus);
        mpz_divexact_ui(weighted, weighted, modulus);

        /* Python parses -(b-1)//k as floor(-(b-1)/k), not truncation
         * toward zero. The extra negative step may have an empty a range. */
        long first_step = -(long)((modulus + k - 1) / k);
        long last_step = (long)(modulus / k);
        for (long step = first_step; step <= last_step; ++step) {
            long delta = (long)k * step;
            long lo = delta < 0 ? -delta : 0;
            long hi = (long)modulus - delta;
            if (hi > (long)modulus) hi = (long)modulus;
            if (lo > hi) continue;
            mpz_mul_si(shift, weighted, step);
            mpz_mul_ui(candidate, repunit, (unsigned long)lo);
            mpz_add(candidate, candidate, shift);
            for (long a = lo; a <= hi; ++a) {
                if (a + delta != 0)
                    assess_candidate(state, ARITHMETIC, candidate, base);
                mpz_add(candidate, candidate, repunit);
            }
        }
    }

    if (state->args.denominator_max >= 2) {
        for (unsigned long den = 2;
             den <= (unsigned long)state->args.denominator_max; ++den) {
            for (unsigned long num = 1; num < den; ++num) {
                if (gcd_ulong(num, den) != 1) continue;
                mpz_mul_ui(anchor, scale, num);
                mpz_fdiv_q_ui(anchor, anchor, den);
                mpz_sub_ui(candidate, anchor, 2);
                for (int offset = -2; offset <= 2; ++offset) {
                    assess_candidate(state, RATIONAL, candidate, base);
                    mpz_add_ui(candidate, candidate, 1);
                }
            }
        }
    }
    mpz_clears(power, scale, anchor, candidate, repunit, weighted, shift, NULL);
}

static void json_string(FILE *out, const char *value) {
    fputc('"', out);
    for (const unsigned char *p = (const unsigned char *)value; *p; ++p) {
        switch (*p) {
        case '"': fputs("\\\"", out); break;
        case '\\': fputs("\\\\", out); break;
        case '\b': fputs("\\b", out); break;
        case '\f': fputs("\\f", out); break;
        case '\n': fputs("\\n", out); break;
        case '\r': fputs("\\r", out); break;
        case '\t': fputs("\\t", out); break;
        default:
            if (*p < 0x20) fprintf(out, "\\u%04x", (unsigned int)*p);
            else fputc(*p, out);
        }
    }
    fputc('"', out);
}

static int compare_solutions(const void *left, const void *right) {
    const solution *a = left, *b = right;
    if (a->base != b->base) return a->base < b->base ? -1 : 1;
    return mpz_cmp(a->number, b->number);
}

static void write_results(FILE *out, const search *state, int full) {
    fputs("{\n  \"parameters\": {\n", out);
    fprintf(out, "    \"max_base\": %ld,\n    \"coefficient_max\": %ld,\n"
                 "    \"denominator_max\": %ld,\n    \"output\": ",
            state->args.max_base, state->args.coefficient_max,
            state->args.denominator_max);
    json_string(out, state->args.output);
    fputs("\n  },\n", out);
    if (full) {
        fputs("  \"checked_bases\": [", out);
        int comma = 0;
        for (long base = 2; base <= state->args.max_base; ++base) {
            if (base % 5 == 1 || base % 4 == 3) continue;
            fprintf(out, "%s%ld", comma ? ", " : "", base);
            comma = 1;
        }
        fputs("],\n", out);
    }
    fprintf(out, "  \"elapsed_seconds\": %.9f,\n  \"counts\": {", state->elapsed);
    for (size_t i = 0; i < state->family_count; ++i) {
        enum family family = state->family_order[i];
        const counters *count = &state->counts[family];
        fputs(i ? ",\n    " : "\n    ", out);
        json_string(out, family_names[family]);
        fprintf(out, ": {\"generated\": %llu", count->generated);
        if (count->modular)
            fprintf(out, ", \"modular_survivors\": %llu", count->modular);
        if (count->length_valid)
            fprintf(out, ", \"length_valid_modular_survivors\": %llu", count->length_valid);
        fputc('}', out);
    }
    fputs(state->family_count ? "\n  },\n" : "},\n", out);
    fputs("  \"solutions\": [", out);
    for (size_t i = 0; i < state->solution_count; ++i) {
        const solution *entry = &state->solutions[i];
        fprintf(out, "%s{\"base\": %lu, \"number\": \"", i ? ", " : "", entry->base);
        mpz_out_str(out, 10, entry->number);
        fputs("\"}", out);
    }
    fputs("],\n", out);
    if (full) {
        fputs("  \"best_by_family_and_base\": [", out);
        for (size_t i = 0; i < state->best_count; ++i) {
            const best_record *entry = &state->best[i];
            fprintf(out, "%s{\"number\": ", i ? ",\n    " : "\n    ");
            json_string(out, entry->number);
            fprintf(out, ", \"base\": %lu, \"unique_digits\": %zu, "
                         "\"missing_count\": %zu, \"family\": ",
                    entry->base, entry->distinct,
                    (size_t)entry->base - entry->distinct);
            json_string(out, family_names[entry->family]);
            fputc('}', out);
        }
        fputs(state->best_count ? "\n  ],\n" : "],\n", out);
    }
    fputs("  \"caveat\": \"Finite structured families only; duplicate candidates "
          "across families count repeatedly.\"\n}\n", out);
}

static void usage(FILE *out, const char *program) {
    fprintf(out, "usage: %s [--max-base N] [--coefficient-max N] "
                 "[--denominator-max N] [--output FILE]\n"
                 "Exact GMP port of scripts/constructions.py.\n"
                 "Defaults: 300, 24, 64, results/native-constructions.json.\n"
                 "Maximum supported base: %lu. Empty negative ranges are allowed.\n",
            program, NICE_MAX_BASE);
}

static long parse_long_option(const char *text, const char *name) {
    char *end;
    errno = 0;
    long value = strtol(text, &end, 10);
    if (end == text || errno == ERANGE) {
        fprintf(stderr, "invalid integer for %s: %s\n", name, text);
        exit(2);
    }
    while (isspace((unsigned char)*end)) ++end;
    if (*end) {
        fprintf(stderr, "invalid integer for %s: %s\n", name, text);
        exit(2);
    }
    return value;
}

static options parse_options(int argc, char **argv) {
    options result = {300, 24, 64, "results/native-constructions.json"};
    for (int i = 1; i < argc; ++i) {
        const char *arg = argv[i];
        if (!strcmp(arg, "-h") || !strcmp(arg, "--help")) {
            usage(stdout, argv[0]);
            exit(0);
        }
        if (!strcmp(arg, "--") && i + 1 == argc) break;
        const char *equal = strchr(arg, '=');
        size_t length = equal ? (size_t)(equal - arg) : strlen(arg);
        enum { OPT_BASE, OPT_COEFFICIENT, OPT_DENOMINATOR, OPT_OUTPUT } option;
        if (length == 10 && !strncmp(arg, "--max-base", length)) option = OPT_BASE;
        else if (length == 17 && !strncmp(arg, "--coefficient-max", length)) option = OPT_COEFFICIENT;
        else if (length == 17 && !strncmp(arg, "--denominator-max", length)) option = OPT_DENOMINATOR;
        else if (length == 8 && !strncmp(arg, "--output", length)) option = OPT_OUTPUT;
        else {
            fprintf(stderr, "unrecognized argument: %s\n", arg);
            usage(stderr, argv[0]);
            exit(2);
        }
        const char *value = equal ? equal + 1 : (++i < argc ? argv[i] : NULL);
        if (!value) {
            fprintf(stderr, "missing value for %s\n", arg);
            exit(2);
        }
        if (option == OPT_OUTPUT) result.output = value;
        else {
            long number = parse_long_option(value, arg);
            if (option == OPT_BASE) result.max_base = number;
            else if (option == OPT_COEFFICIENT) result.coefficient_max = number;
            else result.denominator_max = number;
        }
    }
    if (result.max_base > (long)NICE_MAX_BASE)
        nice_die("max-base exceeds the shared resource limit of 1000000");
    return result;
}

int main(int argc, char **argv) {
    search state = {0};
    state.args = parse_options(argc, argv);
    unsigned long capacity = state.args.max_base > 45 ?
        (unsigned long)state.args.max_base : 45;
    nice_init(&state.work, capacity);

    mpz_t regression;
    mpz_init_set_ui(regression, 69);
    nice_stats check = nice_assess(&state.work, regression, 10);
    if (check.square_digits + check.cube_digits != 10 || check.distinct_digits != 10)
        nice_die("known nice-number regression failed");
    mpz_set_str(regression, "330169542960890", 10);
    check = nice_assess(&state.work, regression, 45);
    if (check.square_digits + check.cube_digits != 45 || check.distinct_digits != 44)
        nice_die("known near-miss regression failed");
    mpz_clear(regression);

    double start = nice_now();
    for (long base = 2; base <= state.args.max_base; ++base) {
        if (base % 5 == 1 || base % 4 == 3) continue;
        generate_base(&state, (unsigned long)base);
        if (base % 25 == 0) {
            printf("completed base %ld\n", base);
            fflush(stdout);
        }
    }
    state.elapsed = nice_now() - start;
    if (state.solution_count > 1)
        qsort(state.solutions, state.solution_count, sizeof(*state.solutions), compare_solutions);
    FILE *out = fopen(state.args.output, "w");
    if (!out) {
        perror(state.args.output);
        return EXIT_FAILURE;
    }
    write_results(out, &state, 1);
    int failed = ferror(out);
    if (fclose(out) || failed) nice_die("cannot write construction results");
    write_results(stdout, &state, 0);
    for (size_t i = 0; i < state.best_count; ++i) free(state.best[i].number);
    for (size_t i = 0; i < state.solution_count; ++i) mpz_clear(state.solutions[i].number);
    free(state.best);
    free(state.solutions);
    nice_clear(&state.work);
    return EXIT_SUCCESS;
}
