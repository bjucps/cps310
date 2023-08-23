@ -------------------------------------------
@ File: simpleiodemo_asm.s
@ Desc: Defines ARM vector table and assembly routines
@       for exception handling (no SWI)
@ -------------------------------------------

.text
.global _start
_start:
@ -------------------------------------------
@ ARM Vector Table
@ -------------------------------------------
    b do_reset  @ RESET
    mov r0, r0  @ Undefined
    mov r0, r0  @ SWI
    mov r0, r0  @ Prefetch abort
    mov r0, r0  @ Data abort
    mov r0, r0  
    b handle_kbd_interrupt    @ IRQ

.org 0x100
handle_kbd_interrupt:
    sub lr, lr, #4
    stmfd sp!, {r0-r12, lr}
    bl handle_key_pressed
    ldmfd sp!, {r0-r12, lr}
    movs pc, lr      @ return to previously executing code

@ -------------------------------------------
@ do_reset
@ - exception handler for RESET
@ - executes when simulator begins running program
@ -------------------------------------------
do_reset:
    @ Set up stacks
    
    mov r2, #0xc0 | 0x12
    msr cpsr, r2    @ switch to IRQ mode with interrupts disabled
    ldr sp, =0x7ff0

    mov r2, #0xc0 | 0x13
    msr cpsr, r2    @ switch to Supervisor mode with interrupts disabled
    ldr sp, =0x78f0

    mov r2, #0xc0 | 0x1f
    msr cpsr, r2    @ switch to SYS mode with interrupts disabled
    ldr sp, =0x7000

    @ enable IRQ
    mrs r1, cpsr
    bic r1, r1, #0x80
    msr cpsr, r1
    
    @ Now, branch to main() function
    bl main  
    
    

