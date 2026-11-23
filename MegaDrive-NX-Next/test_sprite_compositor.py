import unittest
from vram import VRAM
from cram import CRAM
from tiles import encode_tile
from planes import DiagnosticPlane
from compositor import DiagnosticCompositor

class SpriteCompositorTests(unittest.TestCase):
    def setUp(self):
        self.vram, self.cram = VRAM(), CRAM()
        self.a = DiagnosticPlane(self.vram, self.cram, 0xe000)
        self.b = DiagnosticPlane(self.vram, self.cram, 0xc000)
        self.sat = 0xd000
        for index, color in ((1, 1), (2, 2), (3, 3)):
            encode_tile(self.vram, index, [[color] * 8 for _ in range(8)])
        self.cram.write(1, 0x000e)
        self.cram.write(2, 0x00e0)
        self.cram.write(3, 0x0e00)
        self.sprite(0, 3, 0, 0, 0)

    def sprite(self, slot, pattern, attr_flags, link, x):
        base = self.sat + slot * 8
        for offset, word in enumerate((128, link, pattern | attr_flags, 128 + x)):
            self.vram.write_word(base + 2 * offset, word)

    def compositor(self):
        return DiagnosticCompositor(self.a, self.b, self.cram, sprite_table_base=self.sat)

    def test_sprite_over_low_planes(self):
        self.vram.write_word(0xe000, 1)
        self.vram.write_word(0xc000, 2)
        self.assertEqual(self.compositor().sample(0, 0), (0, 0, 255))

    def test_high_plane_over_low_sprite(self):
        self.vram.write_word(0xe000, 0x8001)
        self.assertEqual(self.compositor().sample(0, 0), (255, 0, 0))

    def test_high_sprite_over_high_plane(self):
        self.vram.write_word(0xe000, 0x8001)
        self.sprite(0, 3, 0x8000, 0, 0)
        self.assertEqual(self.compositor().sample(0, 0), (0, 0, 255))

    def test_transparent_sprite_exposes_plane(self):
        self.sprite(0, 0, 0, 0, 0)
        self.vram.write_word(0xe000, 1)
        self.assertEqual(self.compositor().sample(0, 0), (255, 0, 0))

    def test_sprite_outside_pixel(self):
        self.sprite(0, 3, 0, 0, 16)
        self.vram.write_word(0xe000, 1)
        self.assertEqual(self.compositor().sample(0, 0), (255, 0, 0))

    def test_earlier_sprite_wins_overlap(self):
        self.sprite(0, 3, 0, 1, 0)
        self.sprite(1, 2, 0, 0, 0)
        self.assertEqual(self.compositor().sample(0, 0), (0, 0, 255))

    def test_invalid_sat_base(self):
        with self.assertRaises(ValueError):
            DiagnosticCompositor(self.a, self.b, self.cram, sprite_table_base=0xd001)

if __name__ == "__main__":
    unittest.main()
