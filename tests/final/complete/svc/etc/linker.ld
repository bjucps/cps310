PHDRS {
    kernel PT_LOAD AT(0x0000) ;
    program PT_LOAD AT(0x1000) ;
}

SECTIONS
{
    . = 0x0000;
    .kernel 0x0000 : {
	KEEP(*/boot.o(.kernel.vectors))
	*/boot.o
        */kernel.o
    } :kernel


    . = 0x1000;
    .text 0x1000 :  {
        *(.text .rodata)
    } :program
    .data : {
        *(.data .bss)
    } :program

}

ENTRY(_start)
