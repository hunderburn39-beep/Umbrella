"""Generate a self-contained diagnostic 64x64 PPM using Plane A/B.

Run from this directory: python demo_frame.py
This is a synthetic reference image, not ROM-driven video output.
"""
from pathlib import Path
from vram import VRAM
from cram import CRAM
from tiles import encode_tile
from planes import DiagnosticPlane
from compositor import DiagnosticCompositor

def make_demo() -> bytes:
    vram, cram = VRAM(), CRAM()
    cram.write(1, 0x000e)
    cram.write(2, 0x00e0)
    cram.write(3, 0x0e00)
    encode_tile(vram, 1, [[1 if x == y or x == 7 - y else 0 for x in range(8)] for y in range(8)])
    encode_tile(vram, 2, [[2 if (x + y) % 2 == 0 else 3 for x in range(8)] for y in range(8)])
    for y in range(8):
        for x in range(8):
            vram.write_word(0xc000 + 2 * (y * 32 + x), 2)
            vram.write_word(0xe000 + 2 * (y * 32 + x), 1)
    a = DiagnosticPlane(vram, cram, 0xe000)
    b = DiagnosticPlane(vram, cram, 0xc000)
    return DiagnosticCompositor(a, b, cram).ppm(64, 64)

if __name__ == "__main__":
    output = Path(__file__).with_name("diagnostic-frame.ppm")
    output.write_bytes(make_demo())
    print(f"Created {output}")
