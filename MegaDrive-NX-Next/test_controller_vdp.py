import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Request

class ControllerVDPTests(unittest.TestCase):
    def setUp(self):
        self.c = ReferenceBusController(bytes.fromhex("4e 71"))

    def test_register_staging(self):
        self.assertEqual(self.c.stage_vdp_control_word(0xc00004, 0x8144), "register-write")
        self.assertEqual(self.c.vdp.registers[1], 0x44)

    def test_word_bus_still_stalls(self):
        self.c.begin(Request(0xc00004, False, 0x8144))
        self.assertFalse(self.c.clock())
        self.assertEqual(self.c.finish(), (False, None))
        self.assertEqual(self.c.vdp.registers[1], 0)

    def test_no_side_channel_during_active_cycle(self):
        self.c.begin(Request(0, True))
        with self.assertRaises(RuntimeError):
            self.c.stage_vdp_control_word(0xc00004, 0x8144)

    def test_reject_other_ports(self):
        with self.assertRaises(ValueError):
            self.c.stage_vdp_control_word(0xc00000, 0x8144)

if __name__ == "__main__":
    unittest.main()
