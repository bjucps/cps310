/* ATOS (ARMSim Toy OS) 2.0
 * (c) 2014, BJU
 *------------------------------------------------------------
 * User-mode support library for C programmers (a.k.a. "libc")
 *----------------------------------------------------------*/
#include <libc.h>

/* User-mapping to read syscall (for one character) */
uchar getc() {
    uchar buff[1] = { 0 };
    read((uchar *)&buff, 1);
    return buff[0];
}

/* User-mapping to write syscall (for one character) */
void putc(uchar c) {
    uchar buff[1] = { c };
    write(buff, 1);
}

/* Write NUL-terminated string to console */
void puts(const uchar *s) {
    /* Find string length */
    size_t strlen = 0;
    while (s[strlen] != '\0') { ++strlen; }
    
    /* Invoke syscall */
    write(s, strlen);
}

/* Read '\r'-terminated string from console into buffer (or as many bytes as possible);
    ALWAYS NUL-terminate buffer...
    (Notice this is the same as the B-level version, and thus rather inefficient,
    making lots of perhaps-unnecessary syscalls.) */
size_t gets(uchar *buff, size_t size) {
    size_t count = 0;
    
    /* Pointer to last valid slot in buffer */
    uchar *end = buff + size - 1;
    uchar c = '\0';
    
    /* As long as we have space... */
    while (buff < end) {
        /* Read (syscall) into remaining buffer space */
        size_t rlen = read(buff, size);
        size -= rlen;
        count += rlen;

        /* Scan through received data for '\r' */
        while (rlen--) {
            if ((c = *buff++) == '\r') { break; }
        }
        
        /* Break if we found a '\r' */
        if (c == '\r') { break; }
    }
    
    /* Always NUL-terminate */
    *buff = '\0';
    
    /* If we ran out of space, burn chars (libcall) until we get '\r' */
    while (c != '\r') { c = getc(); }
    
    /* Return count (not counting NUL) */
    return count;
}


/* Convert NUL-terminated string to signed integer (very naively) */
int atoi(const uchar *str) {
    uchar c;
    int sign = 1, result = 0;
    
    /* Bail on NULL */
    if (!str) { return 0; }
    
    /* Handle negatives */
    if (*str == '-') {
        ++str;
        sign = -1;
    }
    
    /* For each valid digit... */
    while (((c = *str++) >= '0') && (c <= '9')) {
        /* Shift result one decimal digit and add... */
        result = (result * 10) + (c - '0');
    }
    
    return sign * result;
}

/*
    Internal division implementation.
    From http://discuss.joelonsoftware.com/default.asp?interview.11.401113.6

    returns <num> / <denom>
*/
static int divide(int num, int denom) {
  int a = 0, b = 0;
  int i = 31;
  
  /* Work from leftmost to rightmost bit in <num> */
  while (i >= 0) {
    /* Appends one bit from <num> to <a> */
    a = (a << 1) + ((num & (1 << i)) >> i);
    b = b << 1;
    
    if (a >= denom) {
      a -= denom;
      b++;
    }
    i--;
  }
  
  return b;
}

/* Convert <num> to base-10, NUL-terminated string;
    stores output in <result>, using no more than <size>-1
    chars so that it can ALWAYS NUL-terminate
    
    returns NULL if <result> is too small
    
    returns <result> otherwise */
uchar *itoa(int num, uchar *result, size_t size) {
    uchar buf[20] = { 0 };
    uchar *pos = buf, *writeptr = result;
    
    /* We insist on at least 3 chars of space */
    if (size < 3) { return NULL; }
    
    /* Negative -> minus-sign */
    if (num < 0) {
        *writeptr++ = '-';
        num = -num;
        --size;
    }
    
    if (num > 0) {
        /* Build number in reverse order (in <buf>) */
        while (num > 0) {
            unsigned int quotient, remainder;
            quotient = divide(num, 10);
            remainder = num - (quotient * 10);
            *pos++ = remainder + '0';
            num = quotient;
        }
        
        /* Verify we have enough room in <results> */
        if ((pos - buf) >= size) { return NULL; }
        
        /* Back up; <pos> now points at last char in <buf> */
        --pos;
        
        /* Now reverse/copy <buf> into <results> */
        while (pos >= buf) {
            *writeptr++ = *pos--;
        }
        *writeptr++ = '\0';
    } else {
        /* Number is zero */
        *writeptr++ = '0';
        *writeptr++ = '\0';
    }
    
    return result;
}

/* Read integer (string) from console; convenience... */
int geti() {
    uchar buf[64];
    gets(buf, sizeof(buf));
    return atoi(buf);
}

/* Write integer (string) to console; convenience... */
void puti(int num) {
    uchar buf[64];
    puts(itoa(num, buf, sizeof(buf)));
}
