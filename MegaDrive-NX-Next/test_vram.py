import unittest
from vram import VRAM, VRAM_SIZE

class VRAMTests(unittest.TestCase):
    def setUp(self):
        self.vram = VRAM()

    def test_size(self):
        self.assertEqual(len(self.vram.data), VRAM_SIZE)

    def test_word_roundtrip(self):
        self.vram.write_word(0x0100, 0x1234)
        self.assertEqual(self.vram.read_word(0x0100), 0x1234)
        self.assertEqual(self.vram.read_byte(0x0100), 0x12)
        self.assertEqual(self.vram.read_byte(0x0101), 0x34)

    def test_boundary_wrap(self):
        self.vram.write_word(0xffff, 0xabcd)
        self.assertEqual(self.vram.read_byte(0xffff), 0xab)
        self.assertEqual(self.vram.read_byte(0), 0xcd)
        self.assertEqual(self.vram.read_word(0xffff), 0xabcd)

    def test_invalid_address(self):
        with self.assertRaises(ValueError):
            self.vram.read_word(0x10000)
        with self.assertRaises(ValueError):
            self.vram.write_byte(-1, 0)

    def test_invalid_value(self):
        with self.assertRaises(ValueError):
            self.vram.write_word(0, 0x10000)
        with self.assertRaises(ValueError):
            self.vram.write_byte(0, 256)

    def test_clear(self):
        self.vram.write_word(0x1234, 0xbeef)
        self.vram.clear()
        self.assertEqual(self.vram.read_word(0x1234), 0)

    def test_instances_isolated(self):
        self.vram.write_byte(0, 0xaa)
        self.assertEqual(VRAM().read_byte(0), 0)

if __name__ == "__main__":
    unittest.main()
