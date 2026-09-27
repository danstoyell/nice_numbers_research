#define _POSIX_C_SOURCE 200809L
#include "nice.h"
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

void nice_die(const char *message) {
    fprintf(stderr, "%s\n", message);
    exit(EXIT_FAILURE);
}

unsigned long nice_parse_ulong(const char *text, unsigned long minimum,
                               unsigned long maximum, const char *name) {
    char *end;
    errno = 0;
    if (!text || !*text || *text == '-') nice_die(name);
    unsigned long value = strtoul(text, &end, 10);
    if (errno || *end || value < minimum || value > maximum) nice_die(name);
    return value;
}

double nice_now(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) nice_die("clock_gettime failed");
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

void nice_init(nice_workspace *work, unsigned long max_base) {
    if (max_base < 2 || max_base > NICE_MAX_BASE) nice_die("base outside supported resource limit");
    mpz_inits(work->square, work->cube, work->scratch, NULL);
    work->seen = calloc(max_base, sizeof(*work->seen));
    if (!work->seen) nice_die("cannot allocate digit workspace");
    work->capacity = max_base;
    work->epoch = 0;
}

void nice_clear(nice_workspace *work) {
    mpz_clears(work->square, work->cube, work->scratch, NULL);
    free(work->seen);
}

static void begin(nice_workspace *work, mpz_srcptr n, unsigned long base) {
    if (mpz_sgn(n) <= 0 || base < 2 || base > work->capacity) nice_die("invalid positive root or base");
    if (++work->epoch == 0) {
        memset(work->seen, 0, work->capacity * sizeof(*work->seen));
        work->epoch = 1;
    }
    mpz_mul(work->square, n, n);
}

nice_stats nice_assess(nice_workspace *work, mpz_srcptr n, unsigned long base) {
    begin(work, n, base);
    mpz_mul(work->cube, work->square, n);
    nice_stats result = {0, 0, 0};
    for (unsigned int power = 2; power <= 3; ++power) {
        mpz_set(work->scratch, power == 2 ? work->square : work->cube);
        size_t length = 0;
        do {
            unsigned long digit = mpz_tdiv_q_ui(work->scratch, work->scratch, base);
            if (work->seen[digit] != work->epoch) {
                work->seen[digit] = work->epoch;
                ++result.distinct_digits;
            }
            ++length;
        } while (mpz_sgn(work->scratch));
        if (power == 2) result.square_digits = length;
        else result.cube_digits = length;
    }
    return result;
}

int nice_check(nice_workspace *work, mpz_srcptr n, unsigned long base) {
    begin(work, n, base);
    size_t count = 0;
    for (unsigned int power = 2; power <= 3; ++power) {
        if (power == 3) mpz_mul(work->cube, work->square, n);
        mpz_set(work->scratch, power == 2 ? work->square : work->cube);
        do {
            unsigned long digit = mpz_tdiv_q_ui(work->scratch, work->scratch, base);
            if (work->seen[digit] == work->epoch) return 0;
            work->seen[digit] = work->epoch;
            ++count;
        } while (mpz_sgn(work->scratch));
    }
    return count == base;
}

int nice_sum_allowed(mpz_srcptr n, unsigned long base) {
    if (base < 2 || base > NICE_MAX_BASE) nice_die("invalid base for sum filter");
    unsigned long m = base-1;
    unsigned long r = mpz_fdiv_ui(n, m);
    __uint128_t value = (__uint128_t)r*r*(r+1);
    unsigned long target = (unsigned long)(((__uint128_t)base*m/2) % m);
    return value % m == target;
}

int nice_bounds(mpz_ptr lo, mpz_ptr hi, unsigned long base,
                unsigned long *square_digits, unsigned long *cube_digits) {
    if (base < 2 || base > NICE_MAX_BASE) nice_die("invalid base for bounds");
    if (base % 5 == 1) {
        mpz_set_ui(lo, 1); mpz_set_ui(hi, 0);
        *square_digits = *cube_digits = 0;
        return 0;
    }
    unsigned long q = (base-2)/5, r = (base-2)%5;
    *square_digits = 2*q+1+(r >= 2);
    *cube_digits = base-*square_digits;
    mpz_t value, bound;
    mpz_inits(value, bound, NULL);
    mpz_set_ui(lo, 1);
    for (unsigned long power = 2; power <= 3; ++power) {
        unsigned long length = power == 2 ? *square_digits : *cube_digits;
        mpz_ui_pow_ui(value, base, length-1);
        if (!mpz_root(bound, value, power)) mpz_add_ui(bound, bound, 1);
        if (mpz_cmp(bound, lo) > 0) mpz_set(lo, bound);
        mpz_ui_pow_ui(value, base, length);
        mpz_sub_ui(value, value, 1);
        mpz_root(bound, value, power);
        if (power == 2 || mpz_cmp(bound, hi) < 0) mpz_set(hi, bound);
    }
    mpz_clears(value, bound, NULL);
    return mpz_cmp(lo, hi) <= 0;
}
