#!/bin/bash

# Capture "full" path to target module
INFILE="$(realpath "$1")"

# Set CWD to the directory holding this shell script
pushd "$(dirname $0)" >/dev/null

# Output files go in directory holding this shell script
BASEFILE="$(basename "$INFILE")"
EXEFILE="${BASEFILE%.[sc]}.exe"
OBJFILE="obj/${EXEFILE%.exe}.o"
MAPFILE="${OBJFILE%.o}.map"
shift

# Make sure build directory exists
mkdir -p obj 

# Step 1: build baseline ATOS (toy OS; basically just libc at this point) if needed
# ---------------------------------------------------------------------------------
if [ ! -f obj/libc.a ]; then
	# Compile/assemble libc sources
	arm-none-eabi-gcc -g -c -o obj/libc.o -Iinc/ lib/libc.c -nostdlib -fno-builtin -nostartfiles -nodefaultlibs  -mcpu=arm7tdmi
	arm-none-eabi-as -g -o obj/crt.o lib/crt.s

	# Produce an archive of libc
	arm-none-eabi-ar r obj/libc.a obj/crt.o obj/libc.o >/dev/null
	arm-none-eabi-ar s obj/libc.a >/dev/null
fi

# Step 2: build whatever .C module was passed as $1, linking to libc.a
# --------------------------------------------------------------------

# Compile program module (pass our additional arguments, too, in case they specify a -Dxxxxx define)
arm-none-eabi-gcc -g -c -o "$OBJFILE" "$INFILE" "$@" -Iinc/ -nostdlib -fno-builtin -nostartfiles -nodefaultlibs  -mcpu=arm7tdmi

# Link all modules
arm-none-eabi-ld -g -Map "$MAPFILE" -nostdlib -Ttext 0x1000 -N -o "$EXEFILE" "$OBJFILE" obj/libc.a

# Add in the compatibility manifest
arm-none-eabi-objcopy --add-section .armsim=etc/compat.txt --set-section-flags .armsim=noload "$EXEFILE"

# Restore CWD
popd >/dev/null
