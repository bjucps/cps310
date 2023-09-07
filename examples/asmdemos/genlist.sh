#!/bin/sh

while [ "$#" -gt 0 ]; do
	src_file="$1"
	shift

	case "$src_file" in
	*.s)
		obj_file="${src_file%.s}.o"
		dump_args="-d"
		;;
	*.c)
		obj_file="${src_file%.c}.o"
		dump_args="--source"
		;;
	esac

	lst_file="${obj_file%.o}.lst"
	echo -n "$src_file -> $lst_file ... "
	arm-none-eabi-gcc -g -c -o "$obj_file" "$src_file" && \
		arm-none-eabi-objdump $dump_args "$obj_file" >"$lst_file" && \
		echo "OK" || echo "FAIL"
done

