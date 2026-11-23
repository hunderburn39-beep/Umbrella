"""Diagnostic Mega Drive sprite attribute table (SAT) decoder.

Conventional four-word/8-byte SAT entries with 128-pixel coordinate bias.
Samples one linked sprite chain. Not a scanline-accurate sprite engine:
no per-line limits, collisions, masking, or VA2 ASIC timing.
"""
from dataclasses import dataclass
from vram import VRAM
from tiles import decode_tile

@dataclass(frozen=True)
class Sprite:
    x: int
    y: int
    width_tiles: int
    height_tiles: int
    next_link: int
    pattern: int
    palette: int
    hflip: bool
    vflip: bool
    priority: bool

def read_sprite(vram: VRAM, table_base: int, index: int) -> Sprite:
    if not isinstance(index, int) or not 0 <= index < 80:
        raise ValueError("sprite index must be 0..79")
    if not isinstance(table_base, int) or not 0 <= table_base <= 0xffff or table_base % 8:
        raise ValueError("SAT base must be 8-byte aligned")
    offset = (table_base + index * 8) & 0xffff
    yword = vram.read_word(offset)
    size_link = vram.read_word((offset + 2) & 0xffff)
    attr = vram.read_word((offset + 4) & 0xffff)
    xword = vram.read_word((offset + 6) & 0xffff)
    return Sprite(
        x=(xword & 0x1ff) - 128,
        y=(yword & 0x1ff) - 128,
        width_tiles=((size_link >> 10) & 3) + 1,
        height_tiles=((size_link >> 8) & 3) + 1,
        next_link=size_link & 0x7f,
        pattern=attr & 0x7ff,
        palette=(attr >> 13) & 3,
        hflip=bool(attr & 0x0800),
        vflip=bool(attr & 0x1000),
        priority=bool(attr & 0x8000),
    )

def linked_sprites(vram: VRAM, table_base: int, limit: int = 80):
    if not 1 <= limit <= 80:
        raise ValueError("invalid sprite traversal limit")
    index = 0
    seen = set()
    result = []
    while index not in seen and len(result) < limit:
        seen.add(index)
        sprite = read_sprite(vram, table_base, index)
        result.append(sprite)
        if sprite.next_link == 0:
            break
        if sprite.next_link >= 80:
            raise ValueError("SAT link outside 80-entry reference table")
        index = sprite.next_link
    return tuple(result)

def sprite_pixel(vram: VRAM, sprite: Sprite, x: int, y: int):
    """Return (palette index, palette bank, priority) or None for transparent."""
    sx, sy = x - sprite.x, y - sprite.y
    width, height = sprite.width_tiles * 8, sprite.height_tiles * 8
    if not (0 <= sx < width and 0 <= sy < height):
        return None
    if sprite.hflip:
        sx = width - 1 - sx
    if sprite.vflip:
        sy = height - 1 - sy
    # Conventional sprites advance patterns vertically within a column.
    tile_index = (sprite.pattern + (sx // 8) * sprite.height_tiles + sy // 8) & 0x7ff
    pixel = decode_tile(vram, tile_index)[sy % 8][sx % 8]
    return None if pixel == 0 else (pixel, sprite.palette, sprite.priority)
