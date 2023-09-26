@@@ CpS 310 ArmSim Project: Prototype Test 3
@@@ (c) 2016, Bob Jones University
@@@------------------------------------------
@@@ Tests register-shifted-by-register modes

.global _start
.text
_start:
  mov	r0, #0xff
  mov	r1, #4
  mov	r2, r0, lsl r1
  mov	r3, r0, lsr r1
  mov	r4, r0, ror r1
  mov	r5, r4, asr r1
  swi 0
  