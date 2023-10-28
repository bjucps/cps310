#!/bin/bash

# Capture "full" path to target module
INFILE="$(realpath "$1")"

# Set CWD to the directory holding this shell script
pushd "$(dirname $0)" >/dev/null

# Output files go in this directory
BASEFILE="$(basename "$INFILE")"
EXEFILE="${BASEFILE%.[sc]}.exe"
OBJFILE="obj/${EXEFILE%.exe}.o"
MAPFILE="${OBJFILE%.o}.map"
shift

# Make sure build directories exist
mkdir -p obj/sys 
mkdir -p obj/usr

# Step 1: build baseline ATOS (kernel/libc)
# ---------------------------------------------------------------------------------
if [ ! -f obj/sys/boot.o ] || [ sys/boot.s -nt obj/sys/boot.o ]; then
	arm-none-eabi-as -o obj/sys/boot.o sys/boot.s -mcpu=arm7tdmi
fi
if [ ! -f obj/sys/kernel.o ] || [ sys/kernel.c -nt obj/sys/kernel.o ]; then
	arm-none-eabi-gcc -c -o obj/sys/kernel.o -Iinc/ sys/kernel.c -nostdlib -fno-builtin -nostartfiles -nodefaultlibs -mcpu=arm7tdmi
fi

if [ ! -f obj/libc.a ] || [ lib/crt.s -nt obj/libc.a ] || [ lib/libc.c -nt obj/libc.a ]; then
	# Compile "libc"
	arm-none-eabi-as -o obj/usr/crt.o lib/crt.s -mcpu=arm7tdmi
	arm-none-eabi-gcc -c -o obj/usr/libc.o -Iinc/ lib/libc.c -nostdlib -fno-builtin -nostartfiles -nodefaultlibs  -mcpu=arm7tdmi

	# While we're at it, produce an archive of libc
	arm-none-eabi-ar r obj/libc.a obj/usr/crt.o obj/usr/libc.o >/dev/null
	arm-none-eabi-ar s obj/libc.a >/dev/null
fi

# Step 2: build whatever .C module was passed as $1, linking to libc.a
# --------------------------------------------------------------------

# Compile program module (pass our additional arguments, too, in case they specify a -Dxxxxx define)
arm-none-eabi-gcc -c -o "$OBJFILE" "$INFILE" "$@" -Iinc/ -nostdlib -fno-builtin -nostartfiles -nodefaultlibs  -mcpu=arm7tdmi

# Link all modules
arm-none-eabi-ld -Map "$MAPFILE" -nostdlib -T etc/linker.ld -N -o "$EXEFILE" obj/sys/boot.o obj/sys/kernel.o "$OBJFILE" obj/libc.a 

# Add in the compatibility manifest
arm-none-eabi-objcopy --add-section .armsim=etc/compat.txt --set-section-flags .armsim=noload "$EXEFILE"

# Restore CWD
popd >/dev/null
