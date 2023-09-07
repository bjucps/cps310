@ Demonstrate adding A = B + C in ARM assembly
.global _start
.text
_start:
	ldr	r3, =0x42		@ should generate a mov-immediate
	ldr	r4, =0xdeadbeef		@ should generate a ldr-constant-pool
	ldr	r0, =B
	ldr	r1, =C
	ldr	r2, =A
	ldr	r0, [r0]
	ldr	r1, [r1]
	add	r0, r1, r2
	str	r0, [r2]
	swi	0

@.data
.align
A:	.word 	0
B:	.word	41
C:	.word	1
