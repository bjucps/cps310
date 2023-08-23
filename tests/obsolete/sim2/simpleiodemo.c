int key_has_been_pressed = 0;
void handle_key_pressed() {
    key_has_been_pressed = 1;
}

void putchar(char c) {
    (*(char *)0x100000) = c;
}

void puts(char *buf) {
    while (*buf != '\0') {
        char ch = *buf;
        // output ch
        putchar(ch);

        buf++;
    }
    putchar('\n');
}

char getchar() 
{
    return *((char *)0x100001);

}

void readchars(char *buf, int buf_size) {
    int num_read = 0;
    char last_ch = ' ';

    while (last_ch != '\r' && num_read < buf_size) {
        while (key_has_been_pressed == 0) 
            ;
        key_has_been_pressed = 0;
        last_ch = getchar();
        putchar(last_ch);
        buf[num_read++] = last_ch;
    }
    buf[num_read] = '\0';
}

int main()
{
  char charbuf[80];
    

  puts("Enter some characters:"); 
  readchars(charbuf, sizeof(charbuf));

  puts("You entered:");
  puts(charbuf);
 
  asm("swi 0x11");
}