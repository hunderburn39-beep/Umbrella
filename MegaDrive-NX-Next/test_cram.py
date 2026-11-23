import unittest
from cram import CRAM

class CRAMTests(unittest.TestCase):
    def setUp(self):
        self.cram = CRAM()

    def test_64_entries(self):
        self.assertEqual(len(self.cram.words), 64)

    def test_black(self):
        self.assertEqual(self.cram.rgb(0), (0, 0, 0))

    def test_red(self):
        self.cram.write(1, 0x000e)
        self.assertEqual(self.cram.rgb(1), (255, 0, 0))

    def test_green(self):
        self.cram.write(1, 0x00e0)
        self.assertEqual(self.cram.rgb(1), (0, 255, 0))

    def test_blue(self):
        self.cram.write(1, 0x0e00)
        self.assertEqual(self.cram.rgb(1), (0, 0, 255))

    def test_white(self):
        self.cram.write(1, 0x0eee)
        self.assertEqual(self.cram.rgb(1), (255, 255, 255))

    def test_reserved_bits_masked(self):
        self.cram.write(1, 0xffff)
        self.assertEqual(self.cram.read(1), 0x0eee)

    def test_out_of_bounds(self):
        with self.assertRaises(ValueError):
            self.cram.write(64, 0)
        with self.assertRaises(ValueError):
            self.cram.read(-1)

    def test_clear(self):
        self.cram.write(1, 0x000e)
        self.cram.clear()
        self.assertEqual(self.cram.read(1), 0)

if __name__ == "__main__":
    unittest.main()
