import unittest
from vram import VRAM
from cram import CRAM
from planes import DiagnosticPlane
from tiles import encode_tile
from compositor import DiagnosticCompositor

class CompositorTests(unittest.TestCase):
    def setUp(self):
        self.vram, self.cram = VRAM(), CRAM()
        self.a = DiagnosticPlane(self.vram, self.cram, 0xe000)
        self.b = DiagnosticPlane(self.vram, self.cram, 0xc000)
        self.c = DiagnosticCompositor(self.a, self.b, self.cram)
        encode_tile(self.vram, 1, [[1] * 8 for _ in range(8)])
        encode_tile(self.vram, 2, [[2] * 8 for _ in range(8)])
        self.cram.write(1, 0x000e)
        self.cram.write(2, 0x00e0)

    def test_backdrop_when_both_transparent(self):
        self.assertEqual(self.c.sample(0, 0), (0, 0, 0))

    def test_b_when_a_transparent(self):
        self.vram.write_word(0xc000, 2)
        self.assertEqual(self.c.sample(0, 0), (0, 255, 0))

    def test_a_wins_equal_priority(self):
        self.vram.write_word(0xe000, 1)
        self.vram.write_word(0xc000, 2)
        self.assertEqual(self.c.sample(0, 0), (255, 0, 0))

    def test_b_high_beats_a_low(self):
        self.vram.write_word(0xe000, 1)
        self.vram.write_word(0xc000, 0x8002)
        self.assertEqual(self.c.sample(0, 0), (0, 255, 0))

    def test_a_high_beats_b_high(self):
        self.vram.write_word(0xe000, 0x8001)
        self.vram.write_word(0xc000, 0x8002)
        self.assertEqual(self.c.sample(0, 0), (255, 0, 0))

    def test_ppm_dimensions(self):
        image = self.c.ppm(8, 8)
        self.assertTrue(image.startswith(b"P6\n8 8\n255\n"))
        self.assertEqual(len(image), len(b"P6\n8 8\n255\n") + 192)

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            self.c.rgb_frame(257, 8)

if __name__ == "__main__":
    unittest.main()
