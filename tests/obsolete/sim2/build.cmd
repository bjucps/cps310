
call makeasm cmp
call makeasm branch

rem Build simpleiodemo
call simpleiodemo_make

rem Build armos
arm-none-eabi-gcc.exe -c armos_asm.s armos.c  -nostdlib -fno-builtin -nostartfiles -nodefaultlibs  -mcpu=arm7tdmi

rem Build basic I/O demos
call makec iodemo
call makec syscalldemo
call makec countdown

rem Build Additional tests

call makec_no_io locals 

call makec mersenne 
call makec_no_io mersenne
call makec quicksort 
call makec_no_io quicksort

:done