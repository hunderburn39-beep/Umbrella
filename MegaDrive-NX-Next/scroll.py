"""Diagnostic full-plane scroll offsets, independent for planes A and B.

This is a simple wrapped pixel offset. It does not implement HScroll table
modes, per-column VScroll, line scrolling, or VDP register interpretation.
"""
from dataclasses import dataclass
from planes import DiagnosticPlane

@dataclass(frozen=True)
class ScrollOffset:
    x: int = 0
    y: int = 0

    def __post_init__(self):
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            raise ValueError("scroll offsets must be integers")

def sample_scrolled(plane: DiagnosticPlane, x: int, y: int, scroll: ScrollOffset):
    if not isinstance(x, int) or not isinstance(y, int) or x < 0 or y < 0:
        raise ValueError("screen coordinates must be nonnegative integers")
    sx = (x + scroll.x) % (plane.width_tiles * 8)
    sy = (y + scroll.y) % (plane.height_tiles * 8)
    return plane.sample_index(sx, sy)
