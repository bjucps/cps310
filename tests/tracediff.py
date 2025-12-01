#!/usr/bin/env python3
import csv
import os
import sys
from collections import namedtuple
from typing import Optional


def trace_iter(trace_log: str) -> iter:
    with open(trace_log, "rt", encoding="utf-8") as fd:
        buff = []
        for line in fd:
            buff.append(line.strip())
            if len(buff) == 3:
                record = buff[0].split() + buff[1].split() + buff[2].split()
                yield record
                buff.clear()
        if buff:
            raise Exception(f"{trace_log}: malformed log (ended with incomplete trace record)")


def nextish(iterable: iter) -> Optional[object]:
    try:
        return next(iterable)
    except StopIteration:
        return None


def compare_files(actual: str, expected: str) -> tuple[bool, str, float]:
    act_iter = trace_iter(actual)
    exp_iter = trace_iter(expected)
    
    acount = ecount = matched = 0
    status = 'ok'
    while True:
        if status == 'ok':
            arec, erec = nextish(act_iter), nextish(exp_iter)

            if erec and not arec:
                ecount += 1
                status = 'short'
            elif arec and not erec:
                acount += 1
                status = 'long'
            elif arec and erec:
                acount += 1
                ecount += 1
                if arec == erec:
                    matched += 1
                else:
                    status = 'mismatch'
            else:
                break
        elif status == 'long':
            arec = nextish(act_iter)
            if arec:
                acount += 1
            else:
                break
        elif status in ('short', 'mismatch'):
            erec = nextish(exp_iter)
            if erec:
                ecount += 1
            else:
                break
        else:
            raise NotImplementedError(status)

    if status == 'ok':
        return (True, "OK", 1.0)
    elif status == 'long':
        return (False, f"LONG @ expected {ecount}, got {acount} ({acount - ecount} extra)", ecount / acount)
    elif status == 'short':
        return (False, f"SHORT @ expected {ecount}, got {acount} ({ecount - acount} short)", acount / ecount)
    elif status == 'mismatch':
        return (False, f"MISMATCH @ {matched} cycles ({(matched / ecount)*100:.2f}% of {ecount})", matched / ecount)
    else:
        raise NotImplementedError(status)


def compare_dirs(actual: str, expected: str, smap_data: dict = None, ext: str = ".log") -> bool:
    afiles = set(f for f in os.listdir(actual) if f.endswith(ext))
    efiles = set(f for f in os.listdir(expected) if f.endswith(ext))
    jfiles = afiles | efiles

    all_ok = True
    rmap = {}
    for f in sorted(jfiles):
        apath = os.path.join(actual, f)
        epath = os.path.join(expected, f)

        if f in afiles and f in efiles:
            ok, msg, ratio = compare_files(apath, epath)
            rmap[f] = ratio
            print(f"{f}: {msg}")
            all_ok = all_ok and ok
        elif f in afiles:
            print(f"{f}: EXTRA (not in expected files)")
            rmap[f] = 0.0
        elif f in efiles:
            print(f"{f}: MISSING (not in actual files)")
            rmap[f] = 0.0

    if smap_data:
        print()
        score = 0
        outof = 0
        for f, ratio in rmap.items():
            try:
                points = smap_data[f]
            except KeyError:
                print(f"WARNING: no score map entry for '{f}'", file=sys.stderr)
            else:
                outof += points
                score += ratio * points
                print(f"{f:>24}: {ratio * points:5.1f} / {points:5.1f} ({ratio*100:5.2f}%)")
        print('-'*60)
        print(f"{'TOTAL':>24}: {score:5.1f} / {outof:5.1f} ({(score / outof) * 100:5.2f}%)")
            
    return all_ok
    

def main(argv):
    try:
        actual = argv[1]
        expected = argv[2]
        scoremap = argv[3] if len(argv) > 3 else None
    except IndexError:
        print(f"usage: {argv[0]} ACTUAL(LOG/DIR) EXPECTED(LOG/DIR) [SCOREMAP.CSV]", file=sys.stderr)
        sys.exit(2)

    if os.path.isdir(actual) and os.path.isdir(expected):
        smap_data = None
        if scoremap:
            smap_data = {} 
            with open(scoremap, "rt", encoding="utf-8") as fd:
                for row in csv.reader(fd):
                    smap_data[row[0]] = float(row[1])

        ok = compare_dirs(actual, expected, smap_data)
        sys.exit(0 if ok else 1)
    elif os.path.isfile(actual) and os.path.isfile(expected):
        if scoremap:
            print(f"WARNING: SCOREMAP.CSV provided, but ignored for single-file tests...", file=sys.stderr)
        ok, msg = compare_files(actual, expected)
        print(msg)
        sys.exit(0 if ok else 1)
    else:
        atype = "directory" if os.path.isdir(actual) else "file"
        etype = "directory" if os.path.isdir(expected) else "file"
        print(f"ERROR: '{actual}' is a {atype} but '{expected}' is a {etype}")
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)

