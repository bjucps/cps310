@ ATOS (ARMSim Toy OS) 2.0
@ (c) 2014, BJU
@---------------------------------------------------------
@ Exception vector table; bootstrap, ISR, and syscall code
@---------------------------------------------------------

.equ    CONSOLE_BASE,   0x80000000

.global kputc, kgetc, klock, kunlock, fiq_isr


@ Exception Vector Table (at address 0)
@--------------------------------------
.org    0x0000
.section .kernel.vectors
    b       do_reset    @ 00: RESET
    swi     0           @ 04: ?
    b       do_swi      @ 08: SWI
    swi     0           @ 0C: ?
    swi     0           @ 10: ?
    swi     0           @ 14: ?
    b       do_irq      @ 18: IRQ
    swi     0           @ 1C: FIQ


@ System reset handler/bootstrap
@-------------------------------
.section .kernel.text
do_reset:
    @ Set up SVC mode stack
    ldr     sp, =0x00007800
    
    @ Switch to IRQ mode
    mrs     r0, cpsr
    bic     r0, r0, #0x1f
    orr     r0, r0, #0x12
    msr     cpsr_c, r0
    
    @ Set up IRQ mode stack
    ldr     sp, =0x00008000

    @ Before switching to SYS to set up life for the user,
    @ initialize any kernel stuff
    bl      kernel_init
    
    @ Switch to SYS mode
    orr     r0, r0, #0x1f
    msr     cpsr_c, r0
    
    @ Set up SYS/USR stack
    ldr     sp, =0x0000c000
    
    @ Unmask interrupts
    mrs     r0, cpsr
    bic     r0, r0, #0xc0
    msr     cpsr_c, r0
    
    @ Jump to main program entry point
    b       _start


@ Syscall/trap handler
@---------------------
do_swi:
    @ Save register and return address
    push    {r4, lr}
    
    @ Immediately re-enable interrupts--we're cool with that'
    mrs     r4, cpsr
    bic     r4, r4, #0xc0
    msr     cpsr_c, r4

    @ Get SWI number
    ldr     r4, [lr, #-4]

    @ Make sure it is a SWI command
    bic     r4, r4, #0xf0ffffff
    mov     r4, r4, lsr #24
    cmp     r4, #0xf
    bne    _seg_fault

    @ If it is, then get the SWI number
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

_seg_fault:
    ldr     r0, =msg_seg_fault
    bl      panic

_do_read:
    bl      sys_read
    b       _return

_do_write:
    bl      sys_write
    b       _return

_return:
    @ Return to usermode
    pop     {r4, lr}
    movs    pc, lr

    
@ Interrupt service routine for IRQ
@----------------------------------
do_irq:
    sub     lr, lr, #4      @ Adjust for return from IRQ
    push    {r0-r12, lr}    @ Save all the things
    bl      console_isr     @ Invoke high-level ISR (praise the Lord for C)
    pop     {r0-r12, lr}    @ Restore state
    movs    pc, lr          @ Return from exception state (resume prior code)


@ Kernel I/O helpers
@-------------------

@ Put-char I/O routine (r0: char to print)
kputc:
    mov     r1, #CONSOLE_BASE
    strb    r0, [r1]
    bx      lr

@ Get-char I/O routine (returns r0 = char [0 means no char available])
kgetc:
    mov     r1, #CONSOLE_BASE
    ldrb    r0, [r1, #4]
    bx      lr

@ Kernel synchronization helpers
@-------------------------------

@ Mask interrupts
klock:
    mrs     r0, cpsr
    orr     r0, r0, #0xC0
    msr     cpsr_c, r0
    bx      lr

@ Unmask interrupts
kunlock:
    mrs     r0, cpsr
    bic     r0, r0, #0xC0
    msr     cpsr_c, r0
    bx      lr


@ String literals
@----------------
.section .kernel.rodata

msg_bad_syscall:    .asciz  "Bad syscall number."
msg_seg_fault:      .asciz  "Segmentation fault (invalid memory access)"


.end
