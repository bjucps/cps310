#!/bin/bash

if [ $# -lt 2 ]; then
	echo "usage: $(basename $0) ASH_PY ASK_DLL [(expected|actual)]"
	echo
	echo "('actual' is the default)"
	exit 1
fi

ASH_PY="$(realpath "$1")"
ASK_DLL="$(realpath "$2")"

if [ -z "$3" ] || [ "$3" = "actual" ]; then
	OUT_DIR="actual"
elif [ "$3" = "expected" ]; then
	OUT_DIR="expected"
	
	echo
	echo "*** OVERWRITING EXPECTED OUTPUT LOGS :: ARE YOU SURE ???"
	echo
	echo "(enter 'yes' to confirm)"
	read CONFIRM SLOP
	echo
	if [ "$CONFIRM" != "yes" ]; then
		echo "ABORTING..."
		exit 1
	else
		echo "OK chief, hope you have all the bugs worked out..."
	fi
	
else
	echo "Only 'expected' or 'actual' accepted for argument 3..."
	exit 1
fi

runsim () {
	local LOG_FILE EXE_BASE EXE_FILE="$1"
	shift
	
	EXE_BASE="$(basename "$EXE_FILE")"	
	LOG_FILE="$(dirname "$EXE_FILE")/$OUT_DIR/${EXE_BASE%.exe}.log"
	
	echo "Running $EXE_FILE (log: $LOG_FILE; options: ""$@"")"
	echo "---------------------------------------------------------------------"
	"$ASH_PY" -t "$LOG_FILE" "$@" "$ASK_DLL" "$EXE_FILE"
	echo	
}


pushd "$(dirname "$0")" >/dev/null

mkdir -p "base/$OUT_DIR"
runsim base/sieve.exe
runsim base/quicksort.exe
runsim base/mersenne_no_input.exe
runsim base/mersenne.exe -i _common/mersenne.input
runsim base/hello.exe -i _common/hello.input

mkdir -p "svc/$OUT_DIR"
runsim svc/sieve.exe -m
runsim svc/quicksort.exe -m
runsim svc/mersenne_no_input.exe -m
runsim svc/mersenne.exe -i _common/mersenne.input -m
runsim svc/hello.exe -i _common/hello.input -m

mkdir -p "irq/$OUT_DIR"
runsim irq/sieve.exe -m
runsim irq/quicksort.exe -m
runsim irq/mersenne_no_input.exe -m
runsim irq/mersenne.exe -i _common/mersenne.input -m
runsim irq/hello.exe -i _common/hello.input -m

mkdir -p "fiq/$OUT_DIR"
runsim fiq/hello_fiq.exe -f 999 -m -i _common/hello.input

mkdir -p "usr/$OUT_DIR"
runsim usr/hello_segFault.exe -r 64k -m -i _common/hello.input
runsim usr/quicksort_segFault.exe -r 64k -m 

popd >/dev/null
