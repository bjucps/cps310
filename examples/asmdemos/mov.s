.global _start
.text
_start:
mov r5, r3
mov r5, #0x0f
mov r5, #0xff000000
mov r5, r3, asr #4
.end
