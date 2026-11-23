import unittest
from vram import VRAM
from tiles import decode_tile, encode_tile

class TileTests(unittest.TestCase):
    def setUp(self):
        self.vram = VRAM()

    def test_empty_tile(self):
        self.assertEqual(decode_tile(self.vram, 0), ((0,) * 8,) * 8)

    def test_packed_nibbles(self):
        self.vram.write_byte(0, 0x1f)
        self.assertEqual(decode_tile(self.vram, 0)[0][:2], (1, 15))

    def test_roundtrip(self):
        pixels = tuple(tuple((x + y) % 16 for x in range(8)) for y in range(8))
        encode_tile(self.vram, 12, pixels)
        self.assertEqual(decode_tile(self.vram, 12), pixels)

    def test_last_tile(self):
        pixels = [[15] * 8 for _ in range(8)]
        encode_tile(self.vram, 2047, pixels)
        self.assertEqual(decode_tile(self.vram, 2047)[7][7], 15)

    def test_tile_isolation(self):
        encode_tile(self.vram, 1, [[3] * 8 for _ in range(8)])
        self.assertEqual(decode_tile(self.vram, 0)[0][0], 0)

    def test_invalid_index(self):
        with self.assertRaises(ValueError):
            decode_tile(self.vram, 2048)

    def test_invalid_pixels(self):
        with self.assertRaises(ValueError):
            encode_tile(self.vram, 0, [[16] * 8 for _ in range(8)])

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            encode_tile(self.vram, 0, [[1] * 8 for _ in range(7)])

if __name__ == "__main__":
    unittest.main()
