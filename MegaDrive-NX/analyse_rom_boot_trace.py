#!/usr/bin/env python3
"""Analyse MegaDrive-NX cartridge-read trace; reads do not prove CPU execution."""
import re
import sys
from pathlib import Path

def analyse(path):
    rows = []
    for line in Path(path).read_text(errors="replace").splitlines():
        m = re.match(r"^\s*(\d+)\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{4})\s*$", line)
        if m:
            seq, word, byte, value = m.groups()
            rows.append((int(seq), int(word,16), int(byte,16), int(value,16)))
    if not rows:
        raise ValueError("No cartridge read rows found")
    errors = []
    for seq, word, byte, value in rows:
        if word * 2 != byte:
            errors.append(f"Row {seq}: word/byte address mismatch")
    first = {byte: value for _, _, byte, value in rows[:4]}
    if all(a in first for a in (0,2,4,6)):
        sp = (first[0] << 16) | first[2]
        pc = (first[4] << 16) | first[6]
        print(f"Initial SP: 0x{sp:08X}; initial PC: 0x{pc:08X}")
        if pc & 1: errors.append("Initial PC is odd")
        if not (0xFF0000 <= sp <= 0xFFFFFF): errors.append("Initial SP outside usual 68000 work RAM")
    else:
        print("Incomplete initial vector reads")
    sequential = sum(rows[i][2] == rows[i-1][2]+2 for i in range(1,len(rows)))
    print(f"Captured reads: {len(rows)}; adjacent sequential reads: {sequential}")
    words = {byte: value for _, _, byte, value in rows}
    tmss = [0x23FC,0x5345,0x4741,0x00A1,0x4000]
    found = [hex(a) for a in words if all(words.get(a+2*i)==w for i,w in enumerate(tmss))]
    print("TMSS SEGA instruction found at:", ", ".join(found) if found else "not in captured words")
    print("IMPORTANT: ROM read trace is not an instruction-execution or write trace.")
    print("NEXT: capture PC/instruction boundaries, A10001 reads, A14000 writes, C00004/C00000 writes.")
    for error in errors: print("ERROR:", error)
    return 1 if errors else 0

if __name__ == "__main__":
    if len(sys.argv)!=2:
        print("Usage: python3 analyse_rom_boot_trace.py rom-boot-trace.txt")
        sys.exit(2)
    sys.exit(analyse(sys.argv[1]))
