@@@ CpS 310 ArmSim Project: Prototype Test 6
@@@ (c) 2016, Bob Jones University
@@@------------------------------------------
@@@ Demonstrates pc-relative addressing

.global _start
.text
_start:
  mov r0, pc
  ldr r0, [pc]
  ldr r0, [pc, #-8]
  swi 0
  