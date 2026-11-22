#!/usr/bin/env python3
# Original Mega Drive diagnostic ROM. SPDX-License-Identifier: CC0-1.0
# Runs on the reconstructed 68000 and writes VDP CRAM from controller input.
import struct, sys
from pathlib import Path
rom=bytearray(32768)
def w(off,n): struct.pack_into(">H",rom,off,n)
def l(off,n): struct.pack_into(">I",rom,off,n)
def txt(off,n,s): rom[off:off+n]=s.encode("ascii").ljust(n,b" ")[:n]
for i in range(0,0x100,4): l(i,0x200)
l(0,0x00ffff00)
txt(0x100,16,"SEGA MEGA DRIVE")
txt(0x110,16,"(C) UMBRELLA2026")
txt(0x120,48,"UMBRELLA CHIP DIAGNOSTIC")
txt(0x150,48,"UMBRELLA CHIP DIAGNOSTIC")
txt(0x180,14,"GM UMB00001-00")
txt(0x190,16,"J")
l(0x1a0,0); l(0x1a4,len(rom)-1)
l(0x1a8,0xff0000); l(0x1ac,0xffffff)
txt(0x1f0,16,"JUE")
pc=0x200
def emit(*words):
    global pc
    for x in words: w(pc,x); pc+=2
def move_w(value,addr): emit(0x33fc,value,addr>>16,addr&65535)
def move_l(value,addr): emit(0x23fc,value>>16,value&65535,addr>>16,addr&65535)
def move_b(value,addr): emit(0x13fc,value,addr>>16,addr&65535)
emit(0x46fc,0x2700) # mask interrupts
move_l(0x53454741,0xa14000) # TMSS
for reg,val in enumerate([0x04,0x04,0x30,0x3c,0x07,0x6c,0,0,0,0,0xff,0,0x81,0x3f,0,2,1,0,0,0,0,0,0,0]):
    move_w(0x8000|(reg<<8)|val,0xc00004)
# V4.0: render a minimal, unambiguous plane-A tile via the real 68000->VDP path.
# VDP register 2 already sets plane A name table at VRAM 0xC000.
# VDP register 1 already enables display; register 16 selects 32x32 cells.
# Tile index 1 begins at VRAM 0x0020 (32 bytes). Each pixel uses palette index 1.
move_w(0x4020,0xc00004)  # VRAM write, address 0x0020
move_w(0x0000,0xc00004)
for _ in range(16):
    move_w(0x1111,0xc00000)  # 8 rows, 4 bytes each
# Fill the entire visible plane with tile 1, so scroll/offset cannot hide it.
move_w(0x4000,0xc00004)  # VRAM write, address 0xC000
move_w(0x0003,0xc00004)
for _ in range(32*32):
    move_w(0x0001,0xc00000)
# CRAM palette 0, colour 1: bright white.
move_w(0xc002,0xc00004)
move_w(0x0000,0xc00004)
move_w(0x0eee,0xc00000)
# Leave CRAM address 0 selected for the existing controller-driven colour loop.
# Diagnostic V2.3: probe the 68000->VDP handshake by avoiding a
# 32-bit MOVEL access across 0xC00004 and its 0xC00006 alias.
# Two standalone 16-bit control-port writes encode the same VDP command.
move_w(0xc000,0xc00004)
move_w(0x0000,0xc00004)
move_w(0x0800,0xc00000)
move_w(0x8144,0xc00004)
move_b(0x40,0xa10009) # TH output
move_b(0x40,0xa10003)
loop=pc
emit(0x7000) # moveq #0,d0
emit(0x1039,0x00a1,0x0003) # move.b pad,d0
emit(0x4600,0x0240,0x003f) # invert bits, mask six inputs
emit(0xd040,0x0040,0x0800) # double bits, combine blue component
# Repeat the same split in the colour-update loop.
move_w(0xc000,0xc00004)
move_w(0x0000,0xc00004)
emit(0x33c0,0x00c0,0x0000) # move.w d0,VDP data
disp=loop-(pc+2)
assert -128<=disp<0
emit(0x6000|(disp&255))
w(0x18e,sum(struct.unpack(">%dH"%((len(rom)-0x200)//2),rom[0x200:]))&65535)
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
(out/"diagnostic.bin").write_bytes(rom)
# Embed the ROM in the executable to avoid depending on SD writes or romfs.
(out/"diagnostic_rom.h").write_text("static const unsigned char diagnostic_rom[] = {\n"+",\n".join(",".join("0x%02x"%x for x in rom[i:i+32]) for i in range(0,len(rom),32))+"\n};\n")
