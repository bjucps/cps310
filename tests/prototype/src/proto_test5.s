@@@ CpS 310 ArmSim Project: Prototype Test 5
@@@ (c) 2016, Bob Jones University
@@@------------------------------------------
@@@ More load/store addressing modes, and byte support

.global _start
.text
_start:
  mov r1, #0xfb0
  mov r2, #0x5000
  mov r3, #0x3000
  mov r4, #8
  
  str r1, [r2]
  str r1, [r2, #-4]          @ 4ffc
  str r1, [r2, -r4]          @ 4ff8
  str r1, [r2, r4]           @ 5008
  str r1, [r2, r4, asr #1]   @ 5004
  str r1, [r2, r4, lsl #2]   @ 5020
  strb r1, [r2, #12]         @ 500c
  
  ldr r5, [r2]
  ldr r6, [r2, #-4]          @ 4ffc
  ldr r7, [r2, -r4]          @ 4ff8
  ldr r8, [r2, r4]           @ 5008
  ldr r9, [r2, r4, asr #1]   @ 5004
  ldr r10, [r2, r4, lsl #2]  @ 5020
  ldrb r11, [r2, #12]        @ 500c
  
  ldr r1, [r2, #4] !         @ [r2 = ] 5004
  str r1, [r2], #-4          @ 5004 (r2 = 5000)
  
  swi 0

  
  
  