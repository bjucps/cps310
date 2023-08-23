#include "io.h"

int main()
{     
    putc('a');
    putc('Z');
  
    asm("swi 0x11");
}