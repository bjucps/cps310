@@@ CpS 310 ArmSim Project: Prototype Test 2
@@@ (c) 2016, Bob Jones University
@@@------------------------------------------
@@@ Tests ROR shift mode as well as data
@@@ processing instructions besides MOV

.global _start
.text
_start:
  mov r0, #724
  mov r1, #0xa1000000
  mov r2, r0, ror #4
  
  mvn r3, #1
  mov r4, #4
  add r5, r4, #3
  sub r5, r4, #3
  rsb r5, r4, #3
  
  and r2, r0, #0xff
  orr r2, r0, #0x12
  eor r2, r0, #732
  bic r2, r0, #0xff
  
  mov r2, #2
  mul r5, r1, r2
  
  swi 0
  