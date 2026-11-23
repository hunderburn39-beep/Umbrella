#!/usr/bin/env python3
"""Correlate observed 68000 bus transitions with cartridge reads.

These are bus samples, not proof of instruction execution or PC retirement.
"""
import argparse
import re
from pathlib import Path

CPU_ROW = re.compile(r"^\s*(\d+)\s+([0-9a-fA-F]{6})\s+([0-9a-fA-F]{6})\s+([0-9a-fA-F]{4})\s+([0-9a-fA-F]{2})\s*$")
ROM_ROW = re.compile(r"^\s*(\d+)\s+([0-9a-fA-F]{6})\s+([0-9a-fA-F]{6})\s+([0-9a-fA-F]{4})\s*$")


def parse(path, pattern):
    rows = []
    for line in Path(path).read_text(errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            seq, word, byte, *rest = match.groups()
            word, byte = int(word, 16), int(byte, 16)
            if word * 2 != byte:
                raise ValueError(f"{path}: row {seq}: inconsistent word/byte address")
            rows.append((int(seq), byte, *[int(value, 16) for value in rest]))
    return rows


def analyse(cpu_path, rom_path):
    cpu = parse(cpu_path, CPU_ROW)
    rom = parse(rom_path, ROM_ROW)
    print(f"CPU bus samples: {len(cpu)} / 64")
    print(f"Cartridge reads: {len(rom)} / 32")
    if not cpu:
        print("CPU bus: no address transitions recorded; inspect reset, clocks and arbitration.")
    if not rom:
        print("Cartridge: no reads recorded; inspect chip enable and ROM mapping.")
    cpu_reads = {addr for _, addr, _, flags in cpu if not (flags & 1)}
    rom_addrs = {addr for _, addr, _ in rom}
    shared = sorted(cpu_reads & rom_addrs)
    print(f"Matching CPU-read and ROM-read byte addresses: {len(shared)}")
    if shared:
        print("First matching addresses:", ", ".join(f"{addr:06X}" for addr in shared[:12]))
    elif cpu and rom:
        print("No matching addresses in these limited samples; this does NOT prove a wiring fault.")
    for label, address in (
        ("Reset PC vector", 0x000004),
        ("Startup code", 0x006BAC),
        ("I/O version register", 0xA10000),
        ("TMSS register", 0xA14000),
        ("VDP data port", 0xC00000),
        ("VDP control port", 0xC00004),
    ):
        # The 68000 bus trace is word addressed; byte access at an odd
        # address can be represented by its containing even word address.
        samples = [(data, flags) for _, addr, data, flags in cpu if addr == address]
        reads = sum(not (flags & 1) for _, flags in samples)
        writes = sum(bool(flags & 1) for _, flags in samples)
        print(f"{label} [{address:06X}]: CPU reads={reads}, writes={writes}")
    print("LIMIT: sample count is capped; absence from the trace is not proof of absence on hardware.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cpu_trace")
    parser.add_argument("rom_trace")
    args = parser.parse_args()
    raise SystemExit(analyse(args.cpu_trace, args.rom_trace))
