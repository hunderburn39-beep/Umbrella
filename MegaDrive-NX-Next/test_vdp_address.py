import unittest
from vdp_address import decode_command, increment_address

class VDPAddressTests(unittest.TestCase):
    def test_vram_write_command(self):
        c = decode_command(0x4000, 0x0000)
        self.assertEqual((c.address, c.code, c.operation), (0, 1, "vram-write"))

    def test_vram_read_command(self):
        c = decode_command(0x0000, 0x0000)
        self.assertEqual((c.address, c.code, c.operation), (0, 0, "vram-read"))

    def test_address_upper_bits(self):
        self.assertEqual(decode_command(0x5234, 0x0002).address, 0x9234)

    def test_unsupported_cram_code(self):
        self.assertEqual(decode_command(0xc000, 0x0000).operation, "unsupported")

    def test_increment(self):
        self.assertEqual(increment_address(0x100, 2), 0x102)
        self.assertEqual(increment_address(0xffff, 2), 1)
        self.assertEqual(increment_address(0x100, 0), 0x100)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            decode_command(0x10000, 0)
        with self.assertRaises(ValueError):
            increment_address(0, 256)

if __name__ == "__main__":
    unittest.main()
