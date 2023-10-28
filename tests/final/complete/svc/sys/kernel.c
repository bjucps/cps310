/* ATOS (ARMSim Toy OS) 2.0  [Level: B]
 * (c) 2014, BJU
 *---------------------------
 * High-level kernel routines
 *-------------------------*/
#include <sys.h>

/* Read-buffer syscall (in this version of the OS, always returns at most 1 byte) */
unsigned int sys_read(char *buff, unsigned int size) {
    if (size > 0) {
        *buff = kgetc();
        return 1;
    } else { return 0; }
}

/* Write-buffer syscall */
void sys_write(const char *buff, unsigned int size) {
    while (size--) {
        kputc(*buff++);
    }
}

/* The kernel is dying and taking the system with it... */
void panic(const char *msg) {
    char c;
    while ((c = *msg++) != '\0') {
        kputc(c);
    }
    asm("swi 0");
}
