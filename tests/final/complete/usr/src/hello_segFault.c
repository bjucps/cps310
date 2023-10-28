/* ATOS (ARMSim Toy OS) 2.0
 * (c) 2014, BJU
 *--------------------------------
 * Demonstration user-mode program
 *------------------------------*/
#include <libc.h>

void main() {
    char name[64];
    unsigned int namelen;
    char c;
    
    puts("Please enter your name: ");
    namelen = gets(name, sizeof(name));
    
    if (namelen == sizeof(name) - 1) {
        puts("Hello, Person-Who-Has-Overly-Long-Name!\n");
    } else {
        name[namelen - 1] = '\0';   /* Eliminate '\r' */
        puts("Hello, ");
        puts(name);
        puts("!\n");
    }

    asm("mov r0, #0");
    asm("ldr r0, [r0]");
    
    do {
        puts("Do you like CpS 310 (y/n)? ");
        c = getc();
        putc('\n');
        
        if (c == 'y') {
            puts("Hey, me too!\n");
        } else if (c == 'n') {
            puts(":-(\n");
        } else {
            puts("Please answer (y)es or (n)o...\n\n");
        }
    } while ((c != 'n') && (c != 'y'));
}
