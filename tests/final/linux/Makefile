.PHONY: all

APPS = hello \
	sieve \
	mersenne \
	quicksort

NO_INPUT_APPS = mersenne
NAPPS = $(patsubst %,%_noinput,$(NO_INPUT_APPS))

# requires a musl gcc cross-compiler toolchain (e.g., https://musl.cc/armv5l-linux-musleabi-cross.tgz)
CC = ./armv5l-linux-musleabi-cross/bin/armv5l-linux-musleabi-gcc
CFLAGS = -static -Os

all: $(APPS) $(NAPPS)

$(APPS):%:%.c
	$(CC) $(CFLAGS) -DINPUT -o $@ $^

$(NAPPS):%_noinput:%.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -rf $(APPS) $(NAPPS)
