"""Conventional Mega Drive VDP two-word command decoding reference.

Only VRAM read/write command classification and register-15 auto-increment
are modeled. This is not Genesis 3 VA2 silicon timing, FIFO, or DMA.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class VDPCommand:
    address: int
    code: int

    @property
    def operation(self) -> str:
        if self.code == 0:
            return "vram-read"
        if self.code == 1:
            return "vram-write"
        return "unsupported"

def decode_command(first: int, second: int) -> VDPCommand:
    if not (0 <= first <= 0xffff and 0 <= second <= 0xffff):
        raise ValueError("two 16-bit command words required")
    address = (first & 0x3fff) | ((second & 0x0003) << 14)
    code = ((first >> 14) & 0x03) | ((second >> 2) & 0x3c)
    return VDPCommand(address, code)

def increment_address(address: int, increment: int) -> int:
    if not 0 <= address <= 0xffff or not 0 <= increment <= 0xff:
        raise ValueError("invalid address or increment")
    return (address + increment) & 0xffff
