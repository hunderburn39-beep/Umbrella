import unittest
from z80_control import Z80Control, BUSREQ_ADDR, RESET_ADDR
from z80_ram import Z80RAM

class Z80RAMTests(unittest.TestCase):
    def setUp(self):
        self.control = Z80Control()
        self.ram = Z80RAM(self.control)

    def grant(self):
        self.control.write_word(RESET_ADDR, 0x0100)
        self.control.write_word(BUSREQ_ADDR, 0x0100)
        self.control.sample_bus_grant(True)

    def test_no_access_without_grant(self):
        with self.assertRaises(PermissionError):
            self.ram.read_byte(0xA00000)

    def test_read_write_with_grant(self):
        self.grant()
        self.ram.write_byte(0xA00010, 0x7F)
        self.assertEqual(self.ram.read_byte(0xA00010), 0x7F)

    def test_8kb_mirror(self):
        self.grant()
        self.ram.write_byte(0xA00010, 0xA5)
        self.assertEqual(self.ram.read_byte(0xA02010), 0xA5)

    def test_release_revokes_access(self):
        self.grant()
        self.control.write_word(BUSREQ_ADDR, 0)
        with self.assertRaises(PermissionError):
            self.ram.read_byte(0xA00010)

    def test_reset_revokes_grant(self):
        self.grant()
        self.control.write_word(RESET_ADDR, 0)
        with self.assertRaises(PermissionError):
            self.ram.read_byte(0xA00010)

    def test_other_z80_regions_not_fabricated(self):
        self.grant()
        with self.assertRaises(NotImplementedError):
            self.ram.read_byte(0xA04000)

    def test_invalid_value(self):
        self.grant()
        with self.assertRaises(ValueError):
            self.ram.write_byte(0xA00000, 256)

    def test_word_lane_not_invented(self):
        self.grant()
        with self.assertRaises(NotImplementedError):
            self.ram.read_word(0xA00000)

if __name__ == "__main__":
    unittest.main()
