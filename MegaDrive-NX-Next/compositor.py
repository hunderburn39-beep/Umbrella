"""Untimed diagnostic Plane A/B compositor.

Resolves two name-table planes by transparency and per-tile priority.
Does not model scroll, window, sprites, backdrop register, shadow/highlight,
raster timing or the actual Genesis 3 VA2 ASIC.
"""
from dataclasses import dataclass
from planes import DiagnosticPlane
from cram import CRAM
from scroll import ScrollOffset, sample_scrolled
from sprites import linked_sprites, sprite_pixel

@dataclass
class DiagnosticCompositor:
    plane_a: DiagnosticPlane
    plane_b: DiagnosticPlane
    cram: CRAM
    backdrop_index: int = 0
    scroll_a: ScrollOffset = ScrollOffset()
    scroll_b: ScrollOffset = ScrollOffset()
    sprite_table_base: int | None = None

    def __post_init__(self):
        if not 0 <= self.backdrop_index < 64:
            raise ValueError("backdrop index must be 0..63")
        if self.sprite_table_base is not None and (not 0 <= self.sprite_table_base <= 0xffff or self.sprite_table_base % 8):
            raise ValueError("sprite table base must be 8-byte aligned")

    def sample(self, x: int, y: int) -> tuple[int, int, int]:
        a_index, a_palette, a_priority = sample_scrolled(self.plane_a, x, y, self.scroll_a)
        b_index, b_palette, b_priority = sample_scrolled(self.plane_b, x, y, self.scroll_b)
        # Simplified priority: high sprite > high A > high B >
        # low sprite > low A > low B > backdrop.
        # Earlier linked sprites win overlaps at the same priority.
        candidates = [
            (a_index, a_palette, 5 if a_priority else 2),
            (b_index, b_palette, 4 if b_priority else 1),
        ]
        if self.sprite_table_base is not None:
            sprites = linked_sprites(self.plane_a.vram, self.sprite_table_base)
            for sprite in reversed(sprites):
                pixel = sprite_pixel(self.plane_a.vram, sprite, x, y)
                if pixel is not None:
                    index, palette, priority = pixel
                    candidates.append((index, palette, 6 if priority else 3))
        visible = [item for item in candidates if item[0] != 0]
        if not visible:
            return self.cram.rgb(self.backdrop_index)
        index, palette, _ = max(visible, key=lambda item: item[2])
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
