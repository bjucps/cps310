#!/bin/bash

for srcfile in src/*.s; do
	exefile="${srcfile%.s}.exe"
	echo -n "Building '${exefile#src/}' from '$srcfile'..."
	build/driver.sh "$srcfile" && mv "$exefile" . && echo "OK" || echo "FAIL"
done
