"""Untimed diagnostic Plane A/B compositor.

Resolves two name-table planes by transparency and per-tile priority.
Does not model scroll, window, sprites, backdrop register, shadow/highlight,
raster timing or the actual Genesis 3 VA2 ASIC.
"""
from dataclasses import dataclass
from planes import DiagnosticPlane
from cram import CRAM

@dataclass
class DiagnosticCompositor:
    plane_a: DiagnosticPlane
    plane_b: DiagnosticPlane
    cram: CRAM
    backdrop_index: int = 0

    def __post_init__(self):
        if not 0 <= self.backdrop_index < 64:
            raise ValueError("backdrop index must be 0..63")

    def sample(self, x: int, y: int) -> tuple[int, int, int]:
        a_index, a_palette, a_priority = self.plane_a.sample_index(x, y)
        b_index, b_palette, b_priority = self.plane_b.sample_index(x, y)
        # Candidate display ordering for the conventional VDP:
        # A high > B high > A low > B low > backdrop.
        candidates = (
            (a_index, a_palette, a_priority, 1),
            (b_index, b_palette, b_priority, 0),
        )
        visible = [item for item in candidates if item[0] != 0]
        if not visible:
            return self.cram.rgb(self.backdrop_index)
        index, palette, _, _ = max(visible, key=lambda item: (item[2], item[3]))
        return self.cram.rgb(palette * 16 + index)

    def rgb_frame(self, width: int, height: int):
        if width <= 0 or height <= 0:
            raise ValueError("frame dimensions must be positive")
        if width > min(self.plane_a.width_tiles, self.plane_b.width_tiles) * 8:
            raise ValueError("width exceeds diagnostic plane")
        if height > min(self.plane_a.height_tiles, self.plane_b.height_tiles) * 8:
            raise ValueError("height exceeds diagnostic plane")
        return tuple(tuple(self.sample(x, y) for x in range(width))
                     for y in range(height))

    def ppm(self, width: int, height: int) -> bytes:
        frame = self.rgb_frame(width, height)
        header = f"P6\n{width} {height}\n255\n".encode("ascii")
        return header + bytes(channel for row in frame for rgb in row for channel in rgb)
