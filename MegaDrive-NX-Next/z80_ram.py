"""8 KiB Z80 RAM reference, mapped in the 68000's Z80 address aperture.

This is a storage and access-control test harness, not a Z80 CPU or VA2 ASIC.
"""
from dataclasses import dataclass, field
from z80_control import Z80Control

BASE = 0xA00000
SIZE = 0x2000
APERTURE_END = 0xA0FFFF

@dataclass
class Z80RAM:
    control: Z80Control
    data: bytearray = field(default_factory=lambda: bytearray(SIZE))

    def _offset(self, address: int) -> int:
        if not BASE <= address <= APERTURE_END:
            raise ValueError("outside Z80 aperture")
        if not self.control.bus_granted:
            raise PermissionError("Z80 bus not granted to 68000")
        # Only 8 KiB RAM mirrors are modeled; 0xA02000..0xA03FFF.
        # Other addresses in the aperture may be sound/bank registers.
        if not BASE <= address < BASE + 0x4000:
            raise NotImplementedError("Z80 peripheral or bank area not modeled")
        return (address - BASE) & (SIZE - 1)

    def read_byte(self, address: int) -> int:
        return self.data[self._offset(address)]

    def write_byte(self, address: int, value: int) -> None:
        if not 0 <= value <= 0xFF:
            raise ValueError("8-bit data required")
        self.data[self._offset(address)] = value

    def read_word(self, address: int) -> int:
        if address & 1:
            raise ValueError("unaligned word access")
        # This reference exposes a byte on the upper lane and leaves the
        # lower lane unmodeled; do not fabricate a physical bus value.
        raise NotImplementedError("Z80 RAM 68000 word-lane semantics unverified")
