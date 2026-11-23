#!/usr/bin/env python3
"""Analyse Switch 68000 CPU-side bus transitions (not an instruction trace)."""
import re
import sys
from pathlib import Path

PATTERN = re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{4})\s+([0-9A-Fa-f]{2})\s*$")

def analyse(path):
    rows = []
    for line in Path(path).read_text(errors="replace").splitlines():
        m = PATTERN.match(line)
        if m:
            seq, word, byte, data, flags = m.groups()
            rows.append((int(seq),int(word,16),int(byte,16),int(data,16),int(flags,16)))
    if not rows:
        raise ValueError("No CPU bus rows found")
    errors = []
    for seq, word, byte, data, flags in rows:
        if byte != 2*word:
            errors.append(f"Row {seq}: word/byte address mismatch")
        if flags & ~3:
            errors.append(f"Row {seq}: unknown flags 0x{flags:02X}")
    print(f"CPU bus address transitions: {len(rows)}")
    reads = sum(not (f & 1) for _,_,_,_,f in rows)
    writes = len(rows)-reads
    print(f"Read-address transitions: {reads}; write-address transitions: {writes}")
    for seq, word, byte, data, flags in rows:
        op = "WRITE" if flags & 1 else "READ "
        driven = "driven" if flags & 2 else "high-Z"
        region = ("ROM" if byte < 0x400000 else
                  "IO" if 0xA10000 <= byte <= 0xA1FFFF else
                  "VDP" if 0xC00000 <= byte <= 0xDFFFFF else
                  "RAM" if byte >= 0xFF0000 else "OTHER")
        if region in ("IO","VDP") or (flags & 1):
            print(f"{seq:02d} {op} byte=0x{byte:06X} data=0x{data:04X} {driven} {region}")
    if not any(0xC00000 <= byte <= 0xDFFFFF and flags & 1 for _,_,byte,_,flags in rows):
        print("No VDP write-address transition in captured sample; NOT proof of no VDP writes.")
    print("WARNING: distinct-address sampling omits repeated accesses and cannot prove CPU instruction execution.")
    print("WARNING: data is the CPU output bus, not the value returned on reads.")
    for error in errors:
        print("ERROR:",error)
    return 1 if errors else 0

if __name__ == "__main__":
    if len(sys.argv)!=2:
        print("Usage: python3 analyse_cpu_bus_trace.py cpu-bus-trace.txt")
        sys.exit(2)
    sys.exit(analyse(sys.argv[1]))
