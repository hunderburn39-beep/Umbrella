import unittest
from vram import VRAM
from cram import CRAM
from tiles import encode_tile
from planes import DiagnosticPlane
from scroll import ScrollOffset, sample_scrolled
from compositor import DiagnosticCompositor

class ScrollTests(unittest.TestCase):
    def setUp(self):
        self.vram, self.cram = VRAM(), CRAM()
        self.a = DiagnosticPlane(self.vram, self.cram, 0xe000)
        self.b = DiagnosticPlane(self.vram, self.cram, 0xc000)
        encode_tile(self.vram, 1, [[1] * 8 for _ in range(8)])
        encode_tile(self.vram, 2, [[2] * 8 for _ in range(8)])
        self.cram.write(1, 0x000e)
        self.cram.write(2, 0x00e0)
        self.vram.write_word(0xe000, 1)
        self.vram.write_word(0xe002, 2)

    def test_horizontal_offset_changes_tile(self):
        self.assertEqual(sample_scrolled(self.a, 0, 0, ScrollOffset(8, 0))[0], 2)

    def test_vertical_offset_changes_tile(self):
        self.vram.write_word(0xe040, 2)
        self.assertEqual(sample_scrolled(self.a, 0, 0, ScrollOffset(0, 8))[0], 2)

    def test_horizontal_wrap(self):
        self.vram.write_word(0xe000 + 31 * 2, 2)
        self.assertEqual(sample_scrolled(self.a, 0, 0, ScrollOffset(-8, 0))[0], 2)

    def test_vertical_wrap(self):
        self.vram.write_word(0xe000 + 31 * 32 * 2, 2)
        self.assertEqual(sample_scrolled(self.a, 0, 0, ScrollOffset(0, -8))[0], 2)

    def test_independent_scroll(self):
        self.vram.write_word(0xc000, 1)
        c = DiagnosticCompositor(self.a, self.b, self.cram, scroll_a=ScrollOffset(8, 0))
        self.assertEqual(c.sample(0, 0), (0, 255, 0))

    def test_default_scroll_unchanged(self):
        c = DiagnosticCompositor(self.a, self.b, self.cram)
        self.assertEqual(c.sample(0, 0), (255, 0, 0))

    def test_invalid_scroll(self):
        with self.assertRaises(ValueError):
            ScrollOffset(1.5, 0)
        with self.assertRaises(ValueError):
            sample_scrolled(self.a, -1, 0, ScrollOffset())

if __name__ == "__main__":
    unittest.main()
