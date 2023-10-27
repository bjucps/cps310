#!/bin/sh
COMPAT="$(dirname $0)/compat.txt"

INFILE="$1"
OBJFILE="${INFILE%.[sc]}.o"
EXEFILE="${OBJFILE%.o}.exe"
shift

arm-none-eabi-gcc -c "$INFILE" -o "$OBJFILE" -nostdlib -fno-builtin -nostartfiles -nodefaultlibs -mcpu=arm7tdmi
arm-none-eabi-ld "$@" -nostdlib -Ttext=0x1000 -n -e _start -o "$EXEFILE" "$OBJFILE"
arm-none-eabi-objcopy --add-section .armsim="$COMPAT" --set-section-flags .armsim=noload "$EXEFILE"

