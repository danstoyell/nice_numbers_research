CC ?= cc
CFLAGS ?= -O3 -std=c11 -Wall -Wextra
GMP_PREFIX ?= /opt/homebrew
ifneq ($(wildcard $(GMP_PREFIX)/include/gmp.h),)
CPPFLAGS += -I$(GMP_PREFIX)/include
LDFLAGS += -L$(GMP_PREFIX)/lib
endif
LDLIBS += -lgmp
PROGRAMS = build/nice build/constructions build/dense-search build/structured-outputs build/repdigits

.PHONY: all clean check benchmark
all: $(PROGRAMS)

build:
	mkdir -p build

build/nice: native/nice_cli.c native/nice.c native/nice.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) native/nice_cli.c native/nice.c $(LDFLAGS) $(LDLIBS) -o $@

build/constructions: native/constructions.c native/nice.c native/nice.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) native/constructions.c native/nice.c $(LDFLAGS) $(LDLIBS) -o $@

build/dense-search: native/dense_search.c native/nice.c native/nice.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) native/dense_search.c native/nice.c $(LDFLAGS) $(LDLIBS) -o $@

build/structured-outputs: native/structured_outputs.c native/nice.c native/nice.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) native/structured_outputs.c native/nice.c $(LDFLAGS) $(LDLIBS) -o $@

build/repdigits: native/repdigits.c native/nice.c native/nice.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) native/repdigits.c native/nice.c $(LDFLAGS) $(LDLIBS) -o $@

check: all
	python3 scripts/check_native.py

benchmark: all
	python3 scripts/benchmark_native.py

clean:
	rm -f $(PROGRAMS)
