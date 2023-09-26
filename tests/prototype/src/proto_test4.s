@@@ CpS 310 ArmSim Project: Prototype Test 4
@@@ (c) 2016, Bob Jones University
@@@------------------------------------------
@@@ Baseline/minimal load/store support

.global _start
.text
_start:
  mov r1, #0xfb0
  mov r2, #0x5000
  mov r3, #0x3000
  mov r4, #8
  
  str r1, [r2]
  str r1, [r2, #-4]     @ 4ffc
  
  ldr r5, [r2]
  ldr r6, [r2, #-4]     @ 4ffc
  
  swi 0

  
  
  