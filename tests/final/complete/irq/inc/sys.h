/* ATOS (ARMSim Toy OS) 2.0
 * (c) 2014, BJU
 *---------------------------------
 * Definitions for kernel-mode code
 *-------------------------------*/

#ifndef ATOS_SYS_H
#define ATOS_SYS_H

/* How big should the console input ring buffer be */
#define CONSOLE_BUFFER_LEN (128)

/* Kernel bootstrap function */
void kernel_init();

/* Syscall handlers*/
unsigned int sys_read(char *buff, unsigned int size);
void sys_write(const char *buff, unsigned int size);

/* Utility get/put-character routines for console I/O */
char kgetc();
void kputc(char c);
void kputs(const char *);

/* Low-level interrupt-control routines */
void klock();
void kunlock();

/* In case of emergency, break kernel... */
void panic(const char *msg);


#endif
