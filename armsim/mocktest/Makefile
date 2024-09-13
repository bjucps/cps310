all: mocktest

mocktest: mocktest.c askapi.h
	gcc -o mocktest -g mocktest.c -ldl

clean:
	rm -f mocktest
