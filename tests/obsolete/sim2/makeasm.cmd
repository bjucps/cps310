set infile=%1

arm-none-eabi-gcc.exe -c %infile%.s   -nostdlib -fno-builtin -nostartfiles -nodefaultlibs  -mcpu=arm7tdmi

arm-none-eabi-ld %2 %3 %4 %5 %6 %7 %8 %9 -T linker_no_os.ld -n -e _start -o %1.exe %1.o