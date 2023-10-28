/* ATOS (ARMSim Toy OS) 2.0
 * (c) 2014, BJU
 *---------------------------
 * High-level kernel routines
 *-------------------------*/
#include <sys.h>



/* Ring-buffer for console input data */
static char cons_buff[CONSOLE_BUFFER_LEN] = { 0 };              /* Backing store for buffer */
static volatile char *cons_head = cons_buff;                    /* Insertion point */
static volatile char *cons_tail = cons_buff;                    /* Extraction point */
static volatile unsigned int cons_room = CONSOLE_BUFFER_LEN;    /* Slots left */    

/* Kernel init routine */
void kernel_init() {
    /* The really important part--a boot message! */
    kputs("booting ATOS 2.0...\n\n");
}

/* High-level interrupt service routine (ISR) for console input events */
void console_isr() {
    char c;
    
    /* Pump out all data available (drain the hardware queue, if there is one) */
    while ((c = kgetc()) != 0) {
        /* First, echo it */
        kputc(c);
        
        /* Is there room in the buffer? */
        if (cons_room > 0) {
            /* Add it */
            *cons_head++ = c;
            --cons_room;
            
            /* Handle wraparound */
            if (cons_head >= (cons_buff + CONSOLE_BUFFER_LEN)) {
                cons_head = cons_buff;
            }
        } /* No--just ignore the new input.  Sorry... */
    }
}

/* Read-buffer syscall (if NO data is available,
   block until at least ONE byte is available; else, return
   whatever data IS available, up to <size> bytes)*/
unsigned int sys_read(char *buff, unsigned int size) {
    unsigned int count = 0;
    
    /* Wait for data to become available */
    while (cons_room == CONSOLE_BUFFER_LEN) {
        /* We have no official way to sleep; use SWI 0xFF hack */
        //asm("swi 0xff");
    }
    
    /* "Lock" the buffer by momentarily disabling interrupts */
    klock();
    
    /* Return as much as we can (up to <size> bytes) */
    while ((count < size) && (cons_room < CONSOLE_BUFFER_LEN)) {
        /* Grab byte; update counters */
        *buff++ = *cons_tail++;
        ++count;
        ++cons_room;
        
        /* Wrap tail pointer around ring */
        if (cons_tail >= (cons_buff + CONSOLE_BUFFER_LEN)) {
            cons_tail = cons_buff;
        }
    }
    
    /* Re-enable interrupts */
    kunlock();
    
    return count;
}

/* Write-buffer syscall (write all bytes to console) */
void sys_write(const char *buff, unsigned int size) {
    while (size--) {
        kputc(*buff++);
    }
}

/* Print a string to the console */
void kputs(const char *msg) {
    char c;
    while ((c = *msg++) != '\0') {
        kputc(c);
    }
}

/* The kernel is dying and taking the system with it... */
void panic(const char *msg) {
    kputs(msg);
    asm("swi 0");   /* Halt the simulator with a magic SWI instruction */
}
