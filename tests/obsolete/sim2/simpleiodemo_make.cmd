
arm-none-eabi-gcc.exe -c simpleiodemo_asm.s -o simpleiodemo_asm.o  -nostdlib -fno-builtin -nostartfiles -nodefaultlibs  -mcpu=arm7tdmi

arm-none-eabi-gcc.exe -c simpleiodemo.c -o simpleiodemo.o  -nostdlib -fno-builtin -nostartfiles -nodefaultlibs  -mcpu=arm7tdmi

arm-none-eabi-ld -T simpleio_linker.ld -n -e main -o simpleiodemo.exe simpleiodemo_asm.o simpleiodemo.o 
arm-none-eabi-objdump -d simpleiodemo.exe > simpleiodemo.lst
