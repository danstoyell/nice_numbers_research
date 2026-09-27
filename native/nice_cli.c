#include "nice.h"
#include <stdlib.h>
#include <string.h>

static size_t print_digits(FILE *out, mpz_srcptr n, unsigned long base) {
    size_t capacity = mpz_sizeinbase(n, 2)+1, length = 0;
    unsigned long *digits = malloc(capacity * sizeof(*digits));
    if (!digits) nice_die("cannot allocate output digits");
    mpz_t value;
    mpz_init_set(value, n);
    do { digits[length++] = mpz_tdiv_q_ui(value, value, base); }
    while (mpz_sgn(value));
    fputc('[', out);
    for (size_t i = length; i > 0; --i) fprintf(out, "%s%lu", i == length ? "" : ",", digits[i-1]);
    fputc(']', out);
    free(digits); mpz_clear(value);
    return length;
}

int main(int argc, char **argv) {
    if (argc == 3 && !strcmp(argv[1], "bounds")) {
        unsigned long base = nice_parse_ulong(argv[2], 2, NICE_MAX_BASE, "invalid base");
        mpz_t lo, hi, count; mpz_inits(lo, hi, count, NULL);
        unsigned long s, c;
        printf("{\"base\":%lu,\"intervals\":[", base);
        if (nice_bounds(lo, hi, base, &s, &c)) {
            mpz_sub(count, hi, lo); mpz_add_ui(count, count, 1);
            gmp_printf("{\"lo\":%Zd,\"hi\":%Zd,\"square_digits\":%lu,\"cube_digits\":%lu,\"count\":%Zd}", lo, hi, s, c, count);
        }
        puts("]}"); mpz_clears(lo, hi, count, NULL); return 0;
    }
    if (argc != 4 || strcmp(argv[1], "verify")) nice_die("usage: nice verify N BASE | nice bounds BASE");
    unsigned long base = nice_parse_ulong(argv[3], 2, NICE_MAX_BASE, "invalid base");
    mpz_t n; mpz_init(n);
    if (mpz_set_str(n, argv[2], 10) || mpz_sgn(n) <= 0) nice_die("invalid positive integer");
    nice_workspace work; nice_init(&work, base);
    nice_stats stats = nice_assess(&work, n, base);
    gmp_printf("{\"n\":\"%Zd\",\"base\":%lu,\"square\":\"%Zd\",\"cube\":\"%Zd\",\"square_digits\":", n, base, work.square, work.cube);
    print_digits(stdout, work.square, base);
    printf(",\"cube_digits\":"); print_digits(stdout, work.cube, base);
    printf(",\"digit_count\":%zu,\"distinct_digits\":%zu,\"nice\":%s,\"digit_sum_congruence\":%s}\n",
           stats.square_digits+stats.cube_digits, stats.distinct_digits,
           stats.square_digits+stats.cube_digits == base && stats.distinct_digits == base ? "true" : "false",
           nice_sum_allowed(n, base) ? "true" : "false");
    nice_clear(&work); mpz_clear(n); return 0;
}
