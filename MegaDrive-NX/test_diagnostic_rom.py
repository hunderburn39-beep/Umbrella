#!/usr/bin/env python3
"""Host-side checks for the embedded 68000 diagnostic ROM. No Switch hardware needed."""
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, str(root / "diagnostic.py"), tmp], check=True)
    data = (Path(tmp) / "diagnostic.bin").read_bytes()

assert len(data) == 32768, "Unexpected diagnostic ROM length"
be32 = lambda at: struct.unpack_from(">I", data, at)[0]
assert be32(0) == 0x00FFFF00, "68000 initial stack pointer mismatch"
assert be32(4) == 0x00000200, "68000 reset vector mismatch"
assert data[0x100:0x104] == b"SEGA", "Missing ROM header"
assert b"UMBRELLA CHIP DIAGNOSTIC" in data, "Missing test identification"
# MOVE.W immediate to absolute long VDP control port: 33 FC xx xx 00 C0 00 04
vdpcmds = []
for at in range(0x200, len(data) - 8, 2):
    if data[at:at+2] == b"\x33\xfc" and data[at+4:at+8] == b"\x00\xc0\x00\x04":
        vdpcmds.append((at, struct.unpack_from(">H", data, at + 2)[0]))
assert len(vdpcmds) >= 28, f"Expected VDP control commands; found {len(vdpcmds)}"
pairs = [(a[1], b[1]) for a, b in zip(vdpcmds, vdpcmds[1:])]
assert pairs.count((0xC000, 0x0000)) >= 2, "Split VDP CRAM address writes missing"
assert any(data[i:i+2] == b"\x33\xc0" and data[i+2:i+6] == b"\x00\xc0\x00\x00"
           for i in range(0x200, len(data)-6, 2)), "Controller-driven VDP data write missing"
# The generated ROM must also provide actual VRAM pixels, not just CRAM colours.
assert (0x4020, 0x0000) in pairs, "Missing VRAM tile-data address command"
assert (0x4000, 0x0003) in pairs, "Missing plane-A name-table address command"
assert (0xC002, 0x0000) in pairs, "Missing palette-index-1 CRAM address command"
def immediate_data_writes(value):
    pattern = b"\\x33\\xfc" + struct.pack(">H", value) + b"\\x00\\xc0\\x00\\x00"
    return data.count(pattern)
assert immediate_data_writes(0x1111) >= 16, "Missing 8x8 tile pixel data"
assert immediate_data_writes(0x0001) >= 1024, "Missing 32x32 plane-A name table"
assert immediate_data_writes(0x0EEE) >= 1, "Missing visible tile palette colour"
print("PASS: ROM size, 68000 vectors, header, VDP commands, VRAM tile, plane A and CRAM palette")
print("NOTE: static checks only; do not imply 68000/FC1004/VDP timing correctness.")
