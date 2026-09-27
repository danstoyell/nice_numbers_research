#ifndef NICE_H
#define NICE_H
#include <gmp.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#define NICE_MAX_BASE 1000000UL

typedef struct {
    mpz_t square, cube, scratch;
    uint32_t *seen;
    uint32_t epoch;
    unsigned long capacity;
} nice_workspace;

typedef struct {
    size_t square_digits, cube_digits, distinct_digits;
} nice_stats;

void nice_init(nice_workspace *work, unsigned long max_base);
void nice_clear(nice_workspace *work);
nice_stats nice_assess(nice_workspace *work, mpz_srcptr n, unsigned long base);
int nice_check(nice_workspace *work, mpz_srcptr n, unsigned long base);
int nice_bounds(mpz_ptr lo, mpz_ptr hi, unsigned long base,
                unsigned long *square_digits, unsigned long *cube_digits);
int nice_sum_allowed(mpz_srcptr n, unsigned long base);
unsigned long nice_parse_ulong(const char *text, unsigned long minimum,
                               unsigned long maximum, const char *name);
double nice_now(void);
void nice_die(const char *message);
#endif
