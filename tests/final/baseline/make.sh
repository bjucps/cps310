#!/bin/bash

for srcfile in src/*.{s,c}; do
	exename="${srcfile%.[sc]}.exe"
	echo -n "Building '${exename#src/}' from '$srcfile'..."
	build/driver.sh "$srcfile" && mv "$exename" . && echo "OK" || echo "FAIL"
done
