"""64 KiB VDP VRAM storage reference.

Models address wrapping and 16-bit words only. Does not claim ASIC
timing, FIFO, VDP byte swapping, DMA, or renderer behavior.
"""
from dataclasses import dataclass, field

VRAM_SIZE = 0x10000

@dataclass
class VRAM:
    data: bytearray = field(default_factory=lambda: bytearray(VRAM_SIZE))

    @staticmethod
    def _address(address: int) -> int:
        if not isinstance(address, int) or not 0 <= address <= 0xffff:
            raise ValueError("VRAM address must be 16-bit")
        return address

    def read_byte(self, address: int) -> int:
        return self.data[self._address(address)]

    def write_byte(self, address: int, value: int) -> None:
        self._address(address)
        if not 0 <= value <= 0xff:
            raise ValueError("VRAM byte must be 8-bit")
        self.data[address] = value

    def read_word(self, address: int) -> int:
        index = self._address(address)
        return (self.data[index] << 8) | self.data[(index + 1) & 0xffff]

    def write_word(self, address: int, value: int) -> None:
        index = self._address(address)
        if not 0 <= value <= 0xffff:
            raise ValueError("VRAM word must be 16-bit")
        self.data[index] = value >> 8
        self.data[(index + 1) & 0xffff] = value & 0xff

    def clear(self) -> None:
        self.data[:] = bytes(VRAM_SIZE)
