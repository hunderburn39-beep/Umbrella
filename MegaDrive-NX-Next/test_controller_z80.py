import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Request
from z80_control import BUSREQ_ADDR, RESET_ADDR

class MainBusZ80IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.c = ReferenceBusController(bytes.fromhex("4e 71"))

    def grant(self):
        self.c.write_z80_control(RESET_ADDR, 0x0100)
        self.c.write_z80_control(BUSREQ_ADDR, 0x0100)
        self.c.observe_z80_grant(True)

    def test_control_and_ram_on_same_controller(self):
        self.c.write_z80_control(RESET_ADDR, 0x0100)
        self.c.write_z80_control(BUSREQ_ADDR, 0x0100)
        with self.assertRaises(PermissionError):
            self.c.read_z80_byte(0xa00000)
        self.c.observe_z80_grant(True)
        self.c.write_z80_byte(0xa00001, 0x5a)
        self.assertEqual(self.c.read_z80_byte(0xa02001), 0x5a)

    def test_release_revokes_access(self):
        self.grant()
        self.c.write_z80_control(BUSREQ_ADDR, 0)
        with self.assertRaises(PermissionError):
            self.c.read_z80_byte(0xa00000)

    def test_active_cycle_blocks_untimed_side_access(self):
        self.grant()
        self.c.begin(Request(0, True))
        with self.assertRaises(RuntimeError):
            self.c.read_z80_byte(0xa00000)
        with self.assertRaises(RuntimeError):
            self.c.write_z80_control(BUSREQ_ADDR, 0)
        self.assertTrue(self.c.clock())
        self.c.finish()
        self.c.write_z80_byte(0xa00000, 0x10)

    def test_word_cycle_still_does_not_fake_z80(self):
        self.grant()
        self.c.begin(Request(0xa00000, True))
        self.assertFalse(self.c.clock())
        self.assertEqual(self.c.finish(), (False, None))

    def test_invalid_control_address(self):
        with self.assertRaises(ValueError):
            self.c.write_z80_control(0xa10000, 0x0100)

if __name__ == "__main__":
    unittest.main()
