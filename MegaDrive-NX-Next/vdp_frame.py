"""Explicit untimed frame-level sprite diagnostics.

A caller supplies the SAT address, H32/H40 width and visible scanline count.
No clock, CPU bus activity, VDP register decoding or real hardware status read
is inferred. Re-evaluates sprite scanlines and accumulates diagnostic latches.
"""
from dataclasses import dataclass
from vdp_ports import VDPPorts
from sprite_scanline import evaluate_scanline

@dataclass(frozen=True)
class DiagnosticFrameResult:
    width: int
    height: int
    collision_lines: tuple[int, ...]
    sprite_overflow_lines: tuple[int, ...]
    cell_overflow_lines: tuple[int, ...]
    status_word: int

def evaluate_diagnostic_frame(
    vdp: VDPPorts, sat_base: int, width: int = 320, height: int = 224
) -> DiagnosticFrameResult:
    if width not in (256, 320):
        raise ValueError("width must be H32 (256) or H40 (320)")
    if height not in (224, 240):
        raise ValueError("height must be 224 or 240 visible lines")
    vdp.diagnostic_begin_frame()
    collision, sprite_overflow, cell_overflow = [], [], []
    for y in range(height):
        line = evaluate_scanline(vdp.vram, sat_base, y, width)
        vdp.diagnostic_observe_scanline(line)
        if line.collision:
            collision.append(y)
        if line.sprite_overflow:
            sprite_overflow.append(y)
        if line.cell_overflow:
            cell_overflow.append(y)
    return DiagnosticFrameResult(
        width, height, tuple(collision), tuple(sprite_overflow),
        tuple(cell_overflow), vdp.diagnostic_status_word()
    )
