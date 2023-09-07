@ Sums an array of numbers
.text
.global _start
_start:
   LDR R1,=Size    @ R1 is assigned the address of Size
   LDR R1,[R1]     @ R1 = Size 
   LDR R2,=Vec     @ R2 is assigned the address of Vec
   MOV R0,#0       @ R0 = 0 for sum of elements
LOOP: LDR R3,[R2]  @ R3 = Vec[i]
   ADD R0,R0,R3    @ R0 = R0 + Vec[i]
   ADD R2,R2,#4    @ R2 moves to the next element of Vec
   SUB R1,R1,#1    @ the counter for Size is decreased
   CMP R1,#0       @ if counter = 0, end of Vec
   BNE LOOP        @ else repeat the loop
   LDR R1,=Tot     @ R1 is assigned the address of Tot
   STR R0,[R1]     @ Tot = R0
   SWI 0x11        @ end execution
.data
.align @ Align on a word boundary
Size: .word 3
Vec: .word 3, -1, 2
Tot: .skip 4
.end
