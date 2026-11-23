import unittest
from vram import VRAM
from tiles import encode_tile
from sprites import read_sprite, linked_sprites, sprite_pixel

class SpriteTests(unittest.TestCase):
    def setUp(self):
        self.vram = VRAM()
        self.base = 0xd000
        encode_tile(self.vram, 1, [[1] * 8 for _ in range(8)])
        encode_tile(self.vram, 2, [[2] * 8 for _ in range(8)])
        self.write_entry(0, 128, 128, 0, 1)

    def write_entry(self, index, y, x, size_link, attr):
        addr = self.base + index * 8
        for offset, value in enumerate((y, size_link, attr, x)):
            self.vram.write_word(addr + offset * 2, value)

    def test_position_and_pattern(self):
        s = read_sprite(self.vram, self.base, 0)
        self.assertEqual((s.x, s.y, s.pattern), (0, 0, 1))

    def test_size_link_and_palette(self):
        self.write_entry(0, 136, 144, 0x0601, 0xa801)
        s = read_sprite(self.vram, self.base, 0)
        self.assertEqual((s.x, s.y, s.width_tiles, s.height_tiles, s.next_link), (16, 8, 2, 3, 1))
        self.assertEqual((s.palette, s.priority, s.hflip), (1, True, True))

    def test_visible_pixel(self):
        self.assertEqual(sprite_pixel(self.vram, read_sprite(self.vram, self.base, 0), 0, 0), (1, 0, False))

    def test_outside_sprite(self):
        self.assertIsNone(sprite_pixel(self.vram, read_sprite(self.vram, self.base, 0), 8, 0))

    def test_link_chain(self):
        self.write_entry(0, 128, 128, 1, 1)
        self.write_entry(1, 128, 136, 0, 2)
        self.assertEqual(len(linked_sprites(self.vram, self.base)), 2)

    def test_cycle_does_not_loop(self):
        self.write_entry(0, 128, 128, 1, 1)
        self.write_entry(1, 128, 136, 1, 2)
        self.assertEqual(len(linked_sprites(self.vram, self.base)), 2)

    def test_vertical_pattern_layout(self):
        self.write_entry(0, 128, 128, 0x0100, 1)
        s = read_sprite(self.vram, self.base, 0)
        self.assertEqual(sprite_pixel(self.vram, s, 0, 8), (2, 0, False))

    def test_invalid_index(self):
        with self.assertRaises(ValueError):
            read_sprite(self.vram, self.base, 80)

if __name__ == "__main__":
    unittest.main()
