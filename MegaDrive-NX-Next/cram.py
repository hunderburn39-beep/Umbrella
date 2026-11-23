"""Conventional Mega Drive 64-entry CRAM palette reference.

Stores 9-bit RGB (3 bits per channel), not analog video output or
Genesis 3 VA2 DAC accuracy. Byte scaling is a diagnostic approximation.
"""
from dataclasses import dataclass, field

ENTRY_COUNT = 64

@dataclass
class CRAM:
    words: list[int] = field(default_factory=lambda: [0] * ENTRY_COUNT)

    def write(self, index: int, word: int) -> None:
        if not 0 <= index < ENTRY_COUNT:
            raise ValueError("CRAM index must be 0..63")
        if not 0 <= word <= 0xffff:
            raise ValueError("CRAM word must be 16-bit")
        self.words[index] = word & 0x0eee

    def read(self, index: int) -> int:
        if not 0 <= index < ENTRY_COUNT:
            raise ValueError("CRAM index must be 0..63")
        return self.words[index]

    def rgb(self, index: int) -> tuple[int, int, int]:
        word = self.read(index)
        red = (word >> 1) & 7
        green = (word >> 5) & 7
        blue = (word >> 9) & 7
        return tuple(round(channel * 255 / 7) for channel in (red, green, blue))

    def clear(self) -> None:
        self.words[:] = [0] * ENTRY_COUNT
