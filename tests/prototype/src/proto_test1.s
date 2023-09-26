@@@ CpS 310 ArmSim Project: Prototype Test 1
@@@ (c) 2016, Bob Jones University
@@@------------------------------------------
@@@ Tests MOV instruction with basic addressing modes

.global _start
.text
_start:
  mov r0, #724
  mov r1, #0xa1000000
  mov r2, r0
  mov r2, r1, asr #2
  mov r2, r1, lsr #2
  mov r2, r1, lsl #1
  swi 0
  