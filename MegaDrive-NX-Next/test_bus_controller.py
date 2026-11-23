import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Request, Phase

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.c = ReferenceBusController(bytes.fromhex("12 34 56 78"))

    def test_rom_read(self):
        self.c.begin(Request(0, True))
        self.assertTrue(self.c.clock())
        self.assertEqual(self.c.finish(), (True, 0x1234))

    def test_ram_write_and_read(self):
        self.c.begin(Request(0xff0000, False, 0xabcd))
        self.assertTrue(self.c.clock())
        self.assertEqual(self.c.finish(), (True, None))
        self.c.begin(Request(0xe00000, True))
        self.assertTrue(self.c.clock())
        self.assertEqual(self.c.finish(), (True, 0xabcd))

    def test_vdp_stalls_without_ack(self):
        self.c.begin(Request(0xc00004, False, 0x8144))
        self.assertFalse(self.c.clock())
        self.assertFalse(self.c.clock())
        self.assertEqual(self.c.cycle.phase, Phase.WAIT)
        self.assertEqual(self.c.finish(), (False, None))

    def test_vdp_cannot_fake_ack(self):
        self.c.begin(Request(0xc00004, False, 0x8144))
        with self.assertRaises(NotImplementedError):
            self.c.clock(external_dtack_n=0)

    def test_io_cannot_fake_ack(self):
        self.c.begin(Request(0xa10000, True))
        with self.assertRaises(NotImplementedError):
            self.c.clock(external_dtack_n=0)

    def test_reject_byte_lanes(self):
        with self.assertRaises(NotImplementedError):
            self.c.begin(Request(1, True, upper=False, lower=True))

    def test_unmapped_does_not_ack(self):
        self.c.begin(Request(0x400000, True))
        self.assertFalse(self.c.clock())
        self.assertEqual(self.c.finish(), (False, None))

if __name__ == "__main__":
    unittest.main()
