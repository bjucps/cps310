@ ATOS (ARMSim Toy OS) 2.0
@ (c) 2014-2016, BJU
@----------------------------------------------------
@ User-mode program bootstrapping code (a.k.a. "CRT")
@----------------------------------------------------

.global _start, write, read, clock

.text

@ Master entry point for C-level programs
_start:
    @ Call user-mode entry point...
    bl      main
    
    @ ...then halt system
    swi     0

@ Read-buffer syscall (r0=buff, r1=size; return r0=length)
read:
    swi     1
    bx      lr

@ Write-buffer syscall (r0=buff, r1=size)
write:
    swi     2
    bx      lr

@ Get-clock-ticks syscall (return r0=ticks)
clock:
    swi     3
    bx      lr

.end
