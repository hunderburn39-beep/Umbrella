import unittest
from vram import VRAM
from cram import CRAM
from tiles import encode_tile
from planes import DiagnosticPlane, decode_attribute

class PlaneTests(unittest.TestCase):
    def setUp(self):
        self.vram, self.cram = VRAM(), CRAM()
        self.plane = DiagnosticPlane(self.vram, self.cram, 0xe000)
        encode_tile(self.vram, 1, [[(x + y) % 16 for x in range(8)] for y in range(8)])

    def test_attribute_fields(self):
        a = decode_attribute(0xe801)
        self.assertEqual((a.pattern, a.palette, a.hflip, a.vflip, a.priority),
                         (1, 3, True, False, True))

    def test_plane_tile_index(self):
        self.vram.write_word(0xe000, 1)
        self.assertEqual(self.plane.sample_index(1, 0), (1, 0, False))

    def test_horizontal_flip(self):
        self.vram.write_word(0xe000, 0x0801)
        self.assertEqual(self.plane.sample_index(0, 0)[0], 7)

    def test_vertical_flip(self):
        self.vram.write_word(0xe000, 0x1001)
        self.assertEqual(self.plane.sample_index(0, 0)[0], 7)

    def test_palette_and_priority(self):
        self.vram.write_word(0xe000, 0xa001)
        self.assertEqual(self.plane.sample_index(1, 0), (1, 1, True))

    def test_rgb(self):
        self.vram.write_word(0xe000, 0x2001)
        self.cram.write(17, 0x000e)
        self.assertEqual(self.plane.sample_rgb(1, 0), (255, 0, 0))

    def test_second_tile(self):
        self.vram.write_word(0xe002, 1)
        self.assertEqual(self.plane.sample_index(9, 0)[0], 1)

    def test_out_of_bounds(self):
        with self.assertRaises(ValueError):
            self.plane.sample_index(256, 0)
        with self.assertRaises(ValueError):
            self.plane.attribute(-1, 0)

    def test_invalid_table(self):
        with self.assertRaises(ValueError):
            DiagnosticPlane(self.vram, self.cram, 0xe001)

if __name__ == "__main__":
    unittest.main()
