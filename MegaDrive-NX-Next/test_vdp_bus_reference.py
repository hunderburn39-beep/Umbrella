import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Request
from vdp_address import VDPCommand

class VDPReferenceBusTests(unittest.TestCase):
    def setUp(self):
        self.c = ReferenceBusController(bytes.fromhex("4e71"))

    def test_control_write_waits_for_explicit_ready(self):
        self.c.begin(Request(0xc00004, False, 0x8144))
        self.assertFalse(self.c.clock_vdp_reference(ready=False))
        self.assertEqual(self.c.vdp.registers[1], 0)
        self.assertTrue(self.c.clock_vdp_reference(ready=True))
        self.assertEqual(self.c.finish(), (True, None))
        self.assertEqual(self.c.vdp.registers[1], 0x44)

    def test_data_write_with_active_command(self):
        self.c.vdp.active_command = VDPCommand(0x100, 1)
        self.c.begin(Request(0xc00000, False, 0x1234))
        self.assertTrue(self.c.clock_vdp_reference(ready=True))
        self.assertEqual(self.c.finish(), (True, None))
        self.assertEqual(self.c.vdp.vram.read_word(0x100), 0x1234)

    def test_data_read_with_active_command(self):
        self.c.vdp.vram.write_word(0x100, 0xabcd)
        self.c.vdp.active_command = VDPCommand(0x100, 0)
        self.c.begin(Request(0xc00000, True))
        self.assertTrue(self.c.clock_vdp_reference(ready=True))
        self.assertEqual(self.c.finish(), (True, 0xabcd))

    def test_no_fake_status_read(self):
        self.c.begin(Request(0xc00004, True))
        with self.assertRaises(NotImplementedError):
            self.c.clock_vdp_reference(ready=True)
        self.assertEqual(self.c.finish(), (False, None))

    def test_no_ack_for_unsupported_data_operation(self):
        self.c.begin(Request(0xc00000, True))
        with self.assertRaises(NotImplementedError):
            self.c.clock_vdp_reference(ready=True)
        self.assertEqual(self.c.finish(), (False, None))

    def test_no_side_effect_when_strobe_inactive(self):
        self.c.begin(Request(0xc00004, False, 0x8144))
        with self.assertRaises(RuntimeError):
            self.c.clock_vdp_reference(as_n=1, ready=True)
        self.assertEqual(self.c.vdp.registers[1], 0)
        self.assertEqual(self.c.finish(), (False, None))

    def test_normal_clock_still_does_not_ack_vdp(self):
        self.c.begin(Request(0xc00004, False, 0x8144))
        self.assertFalse(self.c.clock())
        self.assertEqual(self.c.finish(), (False, None))

    def test_reject_non_vdp_address(self):
        self.c.begin(Request(0, True))
        with self.assertRaises(ValueError):
            self.c.clock_vdp_reference(ready=True)
        self.assertEqual(self.c.finish(), (False, None))

    def test_second_sample_no_duplicate_write(self):
        self.c.begin(Request(0xc00004, False, 0x8144))
        self.assertTrue(self.c.clock_vdp_reference(ready=True))
        self.assertFalse(self.c.clock_vdp_reference(ready=True))
        self.assertEqual(self.c.finish(), (True, None))
        self.assertIsNone(self.c.vdp.pending_command)

if __name__ == "__main__":
    unittest.main()
