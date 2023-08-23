#!/bin/sh

if [ -z "$1" ]; then
	echo "usage: $0 ASM_SRC_FILE_NO_EXTENT"
	exit 1
fi

arm-none-eabi-gcc -c "$1.s"
arm-none-eabi-objdump -d "$1.o" > "$1.lst"
