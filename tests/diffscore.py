#!/usr/bin/env python3
import difflib
import sys


def usage():
    print(f"usage: {sys.argv[0]} FILE_A FILE_B [PTS]")
    sys.exit(1)


try:
    file_a_name = sys.argv[1]
    file_b_name = sys.argv[2]
    points = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    with open(file_a_name, "rt") as fda:
        file_a = fda.read()
    with open(file_b_name, "rt") as fdb:
        file_b = fdb.read()
except (IndexError, ValueError):
    usage()
except OSError as e:
    print(e)
    print()
    usage()

sm = difflib.SequenceMatcher(a=file_a, b=file_b)
rat = sm.ratio()
print(f"{int(points * rat)} / {points} ({rat:.3f})")
