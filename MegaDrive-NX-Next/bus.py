"""Reference bus transactions for Genesis 3 VA2 research.

This does not emulate 315-6123 timing. In particular, no fabricated VDP ACK.
"""
from dataclasses import dataclass, field
from boot_bus import decode_region, read_rom_word

@dataclass
class ReferenceBus:
    rom: bytes
    ram: bytearray = field(default_factory=lambda: bytearray(0x10000))
    def _check(self, addr):
        if not isinstance(addr, int) or not 0 <= addr <= 0xffffff:
            raise ValueError("address outside 24-bit bus")
        if addr & 1:
            raise ValueError("unaligned 68000 word access")
    def read_word(self, addr):
        self._check(addr)
        region = decode_region(addr)
        if region == "cartridge":
            return read_rom_word(self.rom, addr)
        if region == "work-ram-mirror":
            offset = addr & 0xffff
            return (self.ram[offset] << 8) | self.ram[(offset + 1) & 0xffff]
        raise NotImplementedError(f"read from {region}: chip behavior not modeled")
    def write_word(self, addr, value):
        self._check(addr)
        if not 0 <= value <= 0xffff:
            raise ValueError("16-bit data required")
        region = decode_region(addr)
        if region == "work-ram-mirror":
            offset = addr & 0xffff
            self.ram[offset] = value >> 8
            self.ram[(offset + 1) & 0xffff] = value & 0xff
            return
        raise NotImplementedError(f"write to {region}: chip behavior not modeled")
