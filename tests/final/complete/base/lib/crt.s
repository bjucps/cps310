@ ATOS (ARMSim Toy OS) 2.0  [Level: C]
@ (c) 2014, BJU
@----------------------------------------------------
@ User-mode program bootstrapping code (a.k.a. "CRT")
@----------------------------------------------------
.equ    CONSOLE_BASE, 0x80000000

.global _start, putc, getc

.text

@ Master entry point for C-level programs
_start:
    @ Call user-mode entry point...
    bl      main
    
    @ ...then halt system
    swi     0


@ Put-char I/O routine (r0: char to print)
putc:
    mov     r1, #CONSOLE_BASE
    strb    r0, [r1]
    bx      lr

@ Poll for a non-zero char from memory-mapped I/O
getc:
    mov     r1, #CONSOLE_BASE
_poll:
    ldrb    r0, [r1, #4]
    cmp     r0, #0
    beq     _poll
    
    strb    r0, [r1]        @ Auto echo...
    bx      lr

.end
