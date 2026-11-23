"""Diagnostic sprite scanline evaluation for conventional MD H32/H40 modes.

Models ordered SAT evaluation, sprite-count and cell budgets, and overlapping
nontransparent sprite pixels. Not verified against Genesis 3 VA2 hardware.
No sprite masking, FIFO, VDP status register or cycle-accurate timing.
"""
from dataclasses import dataclass
from sprites import linked_sprites, sprite_pixel
from vram import VRAM

@dataclass(frozen=True)
class ScanlineResult:
    sprites: tuple
    sprite_overflow: bool
    cell_overflow: bool
    collision: bool

def evaluate_scanline(vram: VRAM, sat_base: int, y: int, width: int = 320) -> ScanlineResult:
    if width not in (256, 320):
        raise ValueError("width must be 256 (H32) or 320 (H40)")
    if not isinstance(y, int) or y < 0:
        raise ValueError("scanline must be nonnegative")
    sprite_limit = 16 if width == 256 else 20
    cell_limit = 32 if width == 256 else 40
    selected = []
    cells = 0
    sprite_overflow = False
    cell_overflow = False
    for sprite in linked_sprites(vram, sat_base):
        if not sprite.y <= y < sprite.y + sprite.height_tiles * 8:
            continue
        if len(selected) >= sprite_limit:
            sprite_overflow = True
            break
        if cells + sprite.width_tiles > cell_limit:
            cell_overflow = True
            break
        selected.append(sprite)
        cells += sprite.width_tiles
    occupied = set()
    collision = False
    for sprite in selected:
        start = max(0, sprite.x)
        stop = min(width, sprite.x + sprite.width_tiles * 8)
        for x in range(start, stop):
            if sprite_pixel(vram, sprite, x, y) is None:
                continue
            if x in occupied:
                collision = True
            occupied.add(x)
    return ScanlineResult(tuple(selected), sprite_overflow, cell_overflow, collision)
