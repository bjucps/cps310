#!/bin/bash

# Make all base (no mode support) tests
base/make.sh _common/hello.c -DINPUT
base/make.sh _common/sieve.c -DINPUT
base/make.sh _common/quicksort.c -DINPUT
base/make.sh _common/mersenne.c && mv "base/mersenne.exe" "base/mersenne_no_input.exe"
base/make.sh _common/mersenne.c -DINPUT

# Make all SVC tests
svc/make.sh _common/hello.c -DINPUT
svc/make.sh _common/sieve.c -DINPUT
svc/make.sh _common/quicksort.c -DINPUT
svc/make.sh _common/mersenne.c && mv "svc/mersenne.exe" "svc/mersenne_no_input.exe"
svc/make.sh _common/mersenne.c -DINPUT

# Make all IRQ tests
irq/make.sh _common/hello.c -DINPUT
irq/make.sh _common/sieve.c -DINPUT
irq/make.sh _common/quicksort.c -DINPUT
irq/make.sh _common/mersenne.c && mv "irq/mersenne.exe" "irq/mersenne_no_input.exe"
irq/make.sh _common/mersenne.c -DINPUT

# Make the FIQ test 
fiq/make.sh fiq/src/hello_fiq.c

# Make the USR tests
usr/make.sh usr/src/hello_segFault.c
usr/make.sh usr/src/quicksort_segFault.c

