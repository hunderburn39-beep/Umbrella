import unittest
from z80_control import Z80Control, BUSREQ_ADDR, RESET_ADDR

class Z80ControlTests(unittest.TestCase):
    def test_initial_reset(self):
        c = Z80Control()
        self.assertTrue(c.reset_asserted)
        self.assertFalse(c.bus_granted)

    def test_release_reset(self):
        c = Z80Control()
        c.write_word(RESET_ADDR, 0x0100)
        self.assertFalse(c.reset_asserted)

    def test_request_not_automatically_granted(self):
        c = Z80Control()
        c.write_word(RESET_ADDR, 0x0100)
        c.write_word(BUSREQ_ADDR, 0x0100)
        self.assertTrue(c.bus_requested)
        self.assertFalse(c.bus_granted)
        self.assertEqual(c.read_busreq_status(), 0x0100)

    def test_explicit_grant(self):
        c = Z80Control()
        c.write_word(RESET_ADDR, 0x0100)
        c.write_word(BUSREQ_ADDR, 0x0100)
        c.sample_bus_grant(True)
        self.assertTrue(c.can_68k_access_z80_ram())
        self.assertEqual(c.read_busreq_status(), 0)

    def test_request_release_clears_grant(self):
        c = Z80Control()
        c.write_word(RESET_ADDR, 0x0100)
        c.write_word(BUSREQ_ADDR, 0x0100)
        c.sample_bus_grant(True)
        c.write_word(BUSREQ_ADDR, 0)
        self.assertFalse(c.bus_granted)

    def test_reset_clears_grant(self):
        c = Z80Control()
        c.write_word(RESET_ADDR, 0x0100)
        c.write_word(BUSREQ_ADDR, 0x0100)
        c.sample_bus_grant(True)
        c.write_word(RESET_ADDR, 0)
        self.assertTrue(c.reset_asserted)
        self.assertFalse(c.bus_granted)

    def test_grant_without_request_rejected(self):
        with self.assertRaises(ValueError):
            Z80Control().sample_bus_grant(True)

    def test_invalid_address(self):
        with self.assertRaises(ValueError):
            Z80Control().write_word(0xA10000, 0x0100)

    def test_reset_allows_reference_access(self):
        self.assertTrue(Z80Control().can_68k_access_z80_ram())

if __name__ == "__main__":
    unittest.main()
