@@@ PRINT STRINGS, CHARACTERS, INTEGERS TO STDOUT
.equ SWI_PrChr,0x00 @ Write an ASCII char to Stdout
.equ SWI_PrStr, 0x69 @ Write a null-ending string
.equ SWI_PrInt,0x6b @ Write an Integer
.equ Stdout, 1 @ Set output mode to be Output View
.equ SWI_Exit, 0x11 @ Stop execution
.global _start
.text
_start:
@ print a string to Stdout
mov R0,#Stdout @ mode is Stdout
ldr R1, =Message1 @ load address of Message1
swi SWI_PrStr @ display message to Stdout
@ print a new line as a string to Stdout
mov R0,#Stdout @ mode is Stdout
ldr r1, =EOL @ end of line
swi SWI_PrStr
@ print a character to the screen
mov R0, #'A @ R0 = char to print
swi SWI_PrChr
@ print a blank character (from data)
ldr r0,=Blank
ldrb r0,[r0] @ R0 = char to print = blank
swi SWI_PrChr
@ print a second character to Stdout
mov R0, #'B @ R0 = char to print
swi SWI_PrChr
@ print a new line as a character to Stdout
ldr r0,=NewL
ldrb r0,[r0] @ R0 = char to print = new line
swi SWI_PrChr
@ print an integer to Stdout
mov R0,#Stdout @ mode is Output view
mov r1, #42 @ integer to print
swi SWI_PrInt
@ print a new line as a string to Stdout
mov R0,#Stdout @ mode is Output view
ldr r1, =EOL @ end of line
swi SWI_PrStr
swi SWI_Exit @ stop executing: end of program
.data
Message1: .asciz "Hello World!"
EOL: .asciz "\n"
NewL: .ascii "\n"
Blank: .ascii " "
.end
