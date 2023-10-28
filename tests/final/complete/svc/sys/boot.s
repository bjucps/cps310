@ ATOS (ARMSim Toy OS) 2.0 [Level: B]
@ (c) 2014, BJU
@-------------------------------------------------
@ Exception vector table and low-level kernel code
@-------------------------------------------------

.equ    CONSOLE_BASE,   0x80000000

.global kgetc, kputc

.section .kernel.vectors

@ Exception Vector Table (at address 0)
@--------------------------------------
.org    0x0000
    swi     0
    swi     0
    b       swi_handler
    swi     0
    swi     0
    swi     0
    swi     0    @b       irq_handler
    swi     0    @b       fiq_handler


.section .kernel.text

@ Exception handlers
@-------------------
swi_handler:
    @ Save register and return address
    push    {r4, r5, lr}

    @ Get SWI number
    ldr     r4, [lr, #-4]
    bic     r4, r4, #0xff000000

    @ Is it read?
    cmp     r4, #1
    beq     _do_read

    @ Write?
    cmp     r4, #2
    beq     _do_write

    @ Unknown syscall!  Panic!
    ldr     r0, =msg_bad_syscall
    bl      panic

_do_read:
    bl      sys_read
    b       _return

_do_write:
    bl      sys_write
    b       _return

_return:
    @ Return to usermode
    pop     {r4, r5, lr}
    movs    pc, lr



@ Kernel I/O helpers
@-------------------

@ Put-char I/O routine (r0: char to print)
kputc:
    mov     r1, #CONSOLE_BASE
    strb    r0, [r1]
    bx      lr

@ Poll for a non-zero char from memory-mapped I/O
kgetc:
    mov     r1, #CONSOLE_BASE
_poll:
    ldrb    r0, [r1, #4]
    cmp     r0, #0
    beq     _poll

    strb    r0, [r1]        @ Auto echo...
    bx      lr



.section .kernel.rodata
msg_bad_syscall:    .asciz  "Bad syscall number."


.end
