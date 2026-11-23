"""Reference Mega Drive 4bpp 8x8 tile decoder.

Each 8x8 pattern occupies 32 VRAM bytes, four packed pixels per 16-bit
word. Produces palette indices only, not RGB, layers or video timing.
"""
from vram import VRAM

TILE_BYTES = 32
TILE_SIDE = 8

def decode_tile(vram: VRAM, pattern_index: int) -> tuple[tuple[int, ...], ...]:
    if not isinstance(pattern_index, int) or not 0 <= pattern_index < 2048:
        raise ValueError("tile index must be 0..2047")
    base = pattern_index * TILE_BYTES
    rows = []
    for y in range(TILE_SIDE):
        row = []
        for xpair in range(4):
            byte = vram.read_byte(base + y * 4 + xpair)
            row.extend((byte >> 4, byte & 0x0f))
        rows.append(tuple(row))
    return tuple(rows)

def encode_tile(vram: VRAM, pattern_index: int, pixels) -> None:
    if not isinstance(pattern_index, int) or not 0 <= pattern_index < 2048:
        raise ValueError("tile index must be 0..2047")
    rows = [tuple(row) for row in pixels]
    if len(rows) != 8 or any(len(row) != 8 for row in rows):
        raise ValueError("tile must be 8x8")
    if any(not isinstance(pixel, int) or not 0 <= pixel <= 15
           for row in rows for pixel in row):
        raise ValueError("tile pixels must be 4-bit palette indices")
    base = pattern_index * TILE_BYTES
    for y, row in enumerate(rows):
        for pair in range(4):
            vram.write_byte(base + y * 4 + pair,
                            (row[pair * 2] << 4) | row[pair * 2 + 1])
