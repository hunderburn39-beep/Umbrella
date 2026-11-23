import unittest
from vram import VRAM
from tiles import encode_tile
from sprite_scanline import evaluate_scanline

class SpriteScanlineTests(unittest.TestCase):
    def setUp(self):
        self.vram = VRAM()
        self.base = 0xd000
        encode_tile(self.vram, 1, [[1] * 8 for _ in range(8)])

    def entry(self, index, x=0, y=0, width=1, height=1, next_link=0, pattern=1):
        addr = self.base + index * 8
        size = ((width - 1) << 10) | ((height - 1) << 8) | next_link
        for n, word in enumerate((y + 128, size, pattern, x + 128)):
            self.vram.write_word(addr + 2 * n, word)

    def chain(self, count, width=1, x_step=0):
        for index in range(count):
            self.entry(index, x=index * x_step, width=width,
                       next_link=index + 1 if index + 1 < count else 0)

    def test_single_visible(self):
        self.entry(0)
        result = evaluate_scanline(self.vram, self.base, 0)
        self.assertEqual(len(result.sprites), 1)
        self.assertFalse(result.collision)

    def test_off_line(self):
        self.entry(0, y=8)
        self.assertEqual(len(evaluate_scanline(self.vram, self.base, 0).sprites), 0)

    def test_overlapping_opaque_pixels_collide(self):
        self.chain(2)
        self.assertTrue(evaluate_scanline(self.vram, self.base, 0).collision)

    def test_separated_sprites_no_collision(self):
        self.chain(2, x_step=8)
        self.assertFalse(evaluate_scanline(self.vram, self.base, 0).collision)

    def test_transparent_pixels_no_collision(self):
        encode_tile(self.vram, 2, [[0] * 8 for _ in range(8)])
        self.entry(0, next_link=1)
        self.entry(1, pattern=2)
        self.assertFalse(evaluate_scanline(self.vram, self.base, 0).collision)

    def test_h32_sprite_count_limit(self):
        self.chain(17)
        result = evaluate_scanline(self.vram, self.base, 0, 256)
        self.assertEqual(len(result.sprites), 16)
        self.assertTrue(result.sprite_overflow)

    def test_h40_sprite_count_limit(self):
        self.chain(21)
        result = evaluate_scanline(self.vram, self.base, 0, 320)
        self.assertEqual(len(result.sprites), 20)
        self.assertTrue(result.sprite_overflow)

    def test_h32_cell_budget(self):
        self.chain(9, width=4)
        result = evaluate_scanline(self.vram, self.base, 0, 256)
        self.assertEqual(len(result.sprites), 8)
        self.assertTrue(result.cell_overflow)

    def test_invalid_width(self):
        with self.assertRaises(ValueError):
            evaluate_scanline(self.vram, self.base, 0, 300)

if __name__ == "__main__":
    unittest.main()
