"""Testable 68000 reset-vector and cartridge-bus reference model.

This is a software reference harness, not a 315-6123 gate-level model.
68000 reset vectors are read big-endian from ROM bytes 0..7.
"""
from dataclasses import dataclass

ROM_BASE = 0x000000
ROM_LIMIT = 0x3fffff
VDP_BASE = 0xc00000
VDP_LIMIT = 0xdfffff

@dataclass(frozen=True)
class ResetVectors:
    initial_ssp: int
    initial_pc: int

def reset_vectors(rom: bytes) -> ResetVectors:
    if len(rom) < 8:
        raise ValueError("ROM too short for 68000 reset vectors")
    return ResetVectors(int.from_bytes(rom[0:4], "big"),
                        int.from_bytes(rom[4:8], "big"))

def read_rom_word(rom: bytes, byte_address: int) -> int:
    """Read a 16-bit big-endian word; reject unmapped or odd addresses."""
    if byte_address < ROM_BASE or byte_address > ROM_LIMIT - 1:
        raise ValueError("address outside cartridge ROM window")
    if byte_address & 1:
        raise ValueError("68000 word read must be aligned")
    if byte_address + 1 >= len(rom):
        raise ValueError("ROM data not present")
    return (rom[byte_address] << 8) | rom[byte_address + 1]

def decode_region(byte_address: int) -> str:
    if not 0 <= byte_address <= 0xffffff:
        raise ValueError("24-bit address required")
    if ROM_BASE <= byte_address <= ROM_LIMIT:
        return "cartridge"
    if 0xa00000 <= byte_address <= 0xa0ffff:
        return "z80-area"
    if 0xa10000 <= byte_address <= 0xa1ffff:
        return "io-control"
    if VDP_BASE <= byte_address <= VDP_LIMIT:
        return "vdp-candidate"
    if 0xe00000 <= byte_address <= 0xffffff:
        return "work-ram-mirror"
    return "unmapped-or-board-specific"

def boot_probe(rom: bytes) -> dict:
    vectors = reset_vectors(rom)
    if vectors.initial_ssp & 1:
        raise ValueError("odd initial SSP cannot support aligned 68000 stack operations")
    if not 0 <= vectors.initial_ssp <= 0xffffff:
        raise ValueError("initial SSP outside 24-bit reference bus")
    if vectors.initial_pc & 1:
        raise ValueError("odd initial PC cannot fetch aligned 68000 instructions")
    if vectors.initial_pc > ROM_LIMIT:
        raise ValueError("initial PC outside simplified cartridge window")
    opcode = read_rom_word(rom, vectors.initial_pc)
    return {"ssp": vectors.initial_ssp, "pc": vectors.initial_pc,
            "first_opcode": opcode, "pc_region": decode_region(vectors.initial_pc)}
