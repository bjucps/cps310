/* Linux port of ATOS 2.0 sample program for ArmSim binfmt_misc extra
 * (c) 2023, BJU
 *--------------------------------
 * Demonstration user-mode program
 *------------------------------*/
#include <stdio.h>
#include <string.h>


size_t mygets(char *buff, size_t size) {
    size_t count = 0;
    
    /* Pointer to last valid slot in buffer */
    char *end = buff + size - 1;
    char c;
    
    /* As long as we have space... */
    while (buff < end) {
        /* Read and store character */
        c = getchar();
        *buff++ = c;
        ++count;
        
        /* Break if it was a NL */
        if (c == '\n') { break; }
    }
    
    /* Always NUL-terminate */
    *buff = '\0';
    
    /* If we ran out of space, burn chars until we get '\n' */
    while (c != '\n') { c = getchar(); }
    
    /* Return count (not counting NUL) */
    return count;
}

void myputs(char *s) {
	while (*s) {
		putchar(*s++);
	}
	fflush(stdout);
}

int main() {
    char name[64];
    unsigned int namelen;
    char c;
    
    myputs("Please enter your name: ");
	namelen = mygets(name, sizeof name);
    
    if (namelen == sizeof(name) - 1) {
        myputs("Hello, Person-Who-Has-Overly-Long-Name!\n");
    } else {
        name[namelen - 1] = '\0';   /* Eliminate '\n' */
        myputs("Hello, ");
        myputs(name);
        myputs("!\n");
    }
    
    do {
        myputs("Do you like CpS 310 (y/n)? ");
        c = getchar();
        putchar('\n');
        
        if (c == 'y') {
            myputs("Hey, me too!\n");
        } else if (c == 'n') {
            myputs(":-(\n");
        } else {
            myputs("Please answer (y)es or (n)o...\n\n");
        }
    } while ((c != 'n') && (c != 'y'));

	return 0;
}
