import unittest
from bus import ReferenceBus

class ReferenceBusTests(unittest.TestCase):
    def setUp(self):
        self.bus = ReferenceBus(bytes.fromhex("12 34 56 78"))

    def test_cartridge_word(self):
        self.assertEqual(self.bus.read_word(0), 0x1234)
        self.assertEqual(self.bus.read_word(2), 0x5678)

    def test_ram_word(self):
        self.bus.write_word(0xff0010, 0xabcd)
        self.assertEqual(self.bus.read_word(0xff0010), 0xabcd)

    def test_ram_mirror(self):
        self.bus.write_word(0xe00010, 0x1234)
        self.assertEqual(self.bus.read_word(0xff0010), 0x1234)

    def test_ram_end_wrap(self):
        self.bus.write_word(0xe0fffe, 0xbeef)
        self.assertEqual(self.bus.read_word(0xfffffe), 0xbeef)

    def test_vdp_not_faked(self):
        with self.assertRaises(NotImplementedError):
            self.bus.write_word(0xc00004, 0x8144)
        with self.assertRaises(NotImplementedError):
            self.bus.read_word(0xc00004)

    def test_cartridge_write_not_faked(self):
        with self.assertRaises(NotImplementedError):
            self.bus.write_word(0, 0)

    def test_odd_address(self):
        with self.assertRaises(ValueError):
            self.bus.read_word(0xff0001)

    def test_bad_data(self):
        with self.assertRaises(ValueError):
            self.bus.write_word(0xff0000, 0x10000)

if __name__ == "__main__":
    unittest.main()
