#!/usr/bin/env python3
"""Read-only MegaDrive-NX boot/bus trace correlation. No simulated pins are changed."""
import argparse
import re
from pathlib import Path

ROW = re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{4})\s*(?:([0-9A-Fa-f]{2}))?\s*$")

def parse(path):
    rows = []
    for line in Path(path).read_text(errors="replace").splitlines():
        m = ROW.match(line)
        if m:
            idx, word, byte, data, flags = m.groups()
            rows.append((int(idx), int(word, 16), int(byte, 16), int(data, 16), None if flags is None else int(flags, 16)))
    return rows

def inspect(rom, bus):
    reads, events = parse(rom), parse(bus)
    print(f"ROM reads: {len(reads)}; CPU bus states: {len(events)}")
    if len(reads) >= 4:
        stack = (reads[0][3] << 16) | reads[1][3]
        pc = (reads[2][3] << 16) | reads[3][3]
        print(f"Reset vectors: SP=0x{stack:08X} PC=0x{pc:08X}")
    expected = []
    for i in range(len(reads) - 3):
        a, b, c, d = reads[i:i+4]
        if a[3] == 0x33FC and c[3] == 0x00C0 and d[3] == 0x0004:
            expected.append((a[2], b[3]))
    print("ROM instructions MOVE.W #imm,$C00004:")
    for address, value in expected:
        print(f"  at 0x{address:06X}: value 0x{value:04X}")
    vdp = [e for e in events if e[2] == 0xC00004]
    print(f"Observed CPU bus states at VDP control port: {len(vdp)}")
    for idx, word, addr, data, flags in vdp:
        print(f"  event {idx}: word=0x{word:06X} data=0x{data:04X} flags={flags!s}")
    if expected and vdp:
        matches = sorted({value for _, value in expected} & {e[3] for e in vdp})
        print("Matching ROM command / bus data: " + (", ".join(f"0x{x:04X}" for x in matches) if matches else "none"))
    print("LIMIT: sampled bus states do not prove DTACK, register latch, or completed writes.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("rom_trace")
    p.add_argument("cpu_trace")
    a = p.parse_args()
    inspect(a.rom_trace, a.cpu_trace)
