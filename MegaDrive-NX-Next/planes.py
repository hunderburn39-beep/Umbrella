"""Diagnostic Mega Drive name-table plane decoder and pixel sampler.

Uses conventional 16-bit tile attributes: pattern 0..10, H/V flip,
palette bits 13..14 and priority bit 15. This is not a scanline renderer:
no scrolling, window, sprite mixing, VDP timing or VA2 ASIC behavior.
"""
from dataclasses import dataclass
from vram import VRAM
from tiles import decode_tile
from cram import CRAM

@dataclass(frozen=True)
class TileAttribute:
    pattern: int
    palette: int
    hflip: bool
    vflip: bool
    priority: bool

def decode_attribute(word: int) -> TileAttribute:
    if not isinstance(word, int) or not 0 <= word <= 0xffff:
        raise ValueError("name-table entry must be 16-bit")
    return TileAttribute(
        pattern=word & 0x07ff,
        palette=(word >> 13) & 3,
        hflip=bool(word & 0x0800),
        vflip=bool(word & 0x1000),
        priority=bool(word & 0x8000),
    )

@dataclass
class DiagnosticPlane:
    vram: VRAM
    cram: CRAM
    table_base: int
    width_tiles: int = 32
    height_tiles: int = 32

    def __post_init__(self):
        if not 0 <= self.table_base <= 0xffff or self.table_base & 1:
            raise ValueError("table base must be even and in VRAM")
        if self.width_tiles not in (32, 64, 128):
            raise ValueError("unsupported plane width")
        if self.height_tiles not in (32, 64, 128):
            raise ValueError("unsupported plane height")
        if self.width_tiles * self.height_tiles * 2 > 0x10000:
            raise ValueError("name table exceeds VRAM")

    def attribute(self, tile_x: int, tile_y: int) -> TileAttribute:
        if not (0 <= tile_x < self.width_tiles and 0 <= tile_y < self.height_tiles):
            raise ValueError("tile coordinates outside plane")
        address = (self.table_base + 2 * (tile_y * self.width_tiles + tile_x)) & 0xffff
        return decode_attribute(self.vram.read_word(address))

    def sample_index(self, x: int, y: int) -> tuple[int, int, bool]:
        if not (0 <= x < self.width_tiles * 8 and 0 <= y < self.height_tiles * 8):
            raise ValueError("pixel coordinates outside plane")
        attr = self.attribute(x // 8, y // 8)
        px = 7 - x % 8 if attr.hflip else x % 8
        py = 7 - y % 8 if attr.vflip else y % 8
        return decode_tile(self.vram, attr.pattern)[py][px], attr.palette, attr.priority

    def sample_rgb(self, x: int, y: int) -> tuple[int, int, int]:
        index, palette, _priority = self.sample_index(x, y)
        return self.cram.rgb(palette * 16 + index)
