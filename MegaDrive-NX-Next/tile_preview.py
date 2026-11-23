"""Diagnostic tile-to-RGB conversion; not a Mega Drive scanline renderer."""
from tiles import decode_tile
from vdp_ports import VDPPorts

def tile_rgb(vdp: VDPPorts, pattern_index: int, palette: int = 0):
    if not 0 <= palette < 4:
        raise ValueError("palette must be 0..3")
    tile = decode_tile(vdp.vram, pattern_index)
    return tuple(tuple(vdp.cram.rgb(palette * 16 + pixel) for pixel in row)
                 for row in tile)

def tile_ppm(vdp: VDPPorts, pattern_index: int, palette: int = 0) -> bytes:
    """Portable binary PPM (P6), 8x8, dependency-free."""
    pixels = tile_rgb(vdp, pattern_index, palette)
    return b"P6\n8 8\n255\n" + bytes(channel for row in pixels for rgb in row for channel in rgb)
