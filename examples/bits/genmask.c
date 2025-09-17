#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <errno.h>

void print_uint32(uint32_t n, char *opt_comment) {
	char bits[33] = { 0 };
	for (int i = 31; i >= 0; --i) {
		bits[i] = '0' + (n & 1);
		n >>= 1;
	}
	if (opt_comment) {
		printf("%s\t// %s\n", bits, opt_comment);
	} else {
		puts(bits);
	}	
}

uint32_t genmask(int bit, int width) {
#ifdef DEBUG
	uint32_t ones = 1 << width;
	print_uint32(ones, "(1 << width)");
	ones -= 1;
	print_uint32(ones, "(1 << width) - 1");
	int shift = (bit - width + 1);
	printf("%32d\t// (%d - %d + 1)\n", shift, bit, width);
	uint32_t mask = ones << shift;
	char msg[80] = { 0 };
	snprintf(msg, sizeof msg, "0x%08x << %d [OUTPUT]", ones, shift);
	print_uint32(mask, msg);
	return mask;
#else
	uint32_t ones = (1 << width) - 1;
	return ones << (bit - width + 1);
#endif
}

bool parse_uint32(char *str, uint32_t *out) {
	unsigned long tmp = 0;
	char *ep = NULL;
	errno = 0;
	tmp = strtoul(str, &ep, 10);
	if ((ep == str) || errno) {
		return false;
	}
	*out = (uint32_t)tmp;
	return true;
}

int main(int argc, char **argv) {
	uint32_t bit, width;

	if (argc < 3) {
usage:
		printf("usage: %s BIT WIDTH\n", argv[0]);
		return 1;
	}
	
	if (!parse_uint32(argv[1], &bit) || (bit > 31)) {
		printf("error: BIT is invalid ('%s'); must be integer in range [0-31]\n", argv[1]);
		goto usage;
	}
	if (!parse_uint32(argv[2], &width) || (width > 32)) {
		printf("error: WIDTH is invalid ('%s'); must be integer in range [0-31]\n", argv[2]);
		goto usage;
	}
	if (width > (bit + 1)) {
		printf("error: WIDTH must be < 1 + BIT (%d > (%d + 1))\n", width, bit);
		goto usage;
	}

	uint32_t mask = genmask(bit, width);
#ifndef DEBUG
	print_uint32(mask, NULL);
#endif

	return 0;
}
