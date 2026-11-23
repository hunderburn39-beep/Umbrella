"""Diagnostic VDP status latch, not a verified hardware status register.

Conventional Mega Drive status word: bit 5 sprite collision, bit 6
sprite overflow. This model does not fabricate timing-dependent flags.
Latches persist until explicitly cleared at diagnostic frame start.
"""
from dataclasses import dataclass
from sprite_scanline import ScanlineResult

SPRITE_COLLISION = 0x0020
SPRITE_OVERFLOW = 0x0040

@dataclass
class DiagnosticVDPStatus:
    collision: bool = False
    overflow: bool = False

    def observe(self, result: ScanlineResult) -> None:
        self.collision |= result.collision
        self.overflow |= result.sprite_overflow or result.cell_overflow

    def word(self) -> int:
        return (SPRITE_COLLISION if self.collision else 0) | (
            SPRITE_OVERFLOW if self.overflow else 0
        )

    def begin_frame(self) -> None:
        self.collision = False
        self.overflow = False
