#!/bin/sh
MYDIR="$(dirname $0)"

INFILE="$1"
OBJFILE="${INFILE%.[sc]}.o"
EXEFILE="${OBJFILE%.o}.exe"
shift

arm-none-eabi-gcc -g -c "$INFILE" -o "$OBJFILE" -nostdlib -fno-builtin -nostartfiles -nodefaultlibs -mcpu=arm7tdmi
arm-none-eabi-ld "$@" -g -T "$MYDIR/linker.ld" -n -e _start -o "$EXEFILE" "$OBJFILE"
arm-none-eabi-objcopy --add-section .armsim="$MYDIR/compat.txt" --set-section-flags .armsim=noload "$EXEFILE"
