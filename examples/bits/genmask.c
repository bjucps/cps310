#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <errno.h>

uint32_t genmask(int bit, int width) {
    uint32_t ones = (1 << width) - 1;
    return ones << (bit - width + 1);
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
	char bits[33] = { 0 };
	for (int i = 31; i >= 0; --i) {
		bits[i] = '0' + (mask & 1);
		mask >>= 1;
	}
	puts(bits);

	return 0;
}
