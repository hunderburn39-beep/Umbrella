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

    def test_rom_byte_lanes(self):
        for address, upper, lower, expected in [(0, True, False, 0x1200), (1, False, True, 0x34), (2, True, False, 0x5600), (3, False, True, 0x78)]:
            with self.subTest(address=address):
                self.c.begin(Request(address, True, upper=upper, lower=lower))
                self.assertTrue(self.c.clock())
                self.assertEqual(self.c.finish(), (True, expected))

    def test_ram_byte_lanes_preserve_other_byte(self):
        self.c.memory.write_word(0xff0000, 0xabcd)
        for address, data, upper, lower, expected in [(0xff0000, 0x1200, True, False, 0x12cd), (0xff0001, 0x0034, False, True, 0x1234)]:
            self.c.begin(Request(address, False, data, upper=upper, lower=lower))
            self.assertTrue(self.c.clock())
            self.assertEqual(self.c.finish(), (True, None))
            self.assertEqual(self.c.memory.read_word(0xe00000), expected)

    def test_reject_unmodeled_peripheral_byte_lanes(self):
        with self.assertRaises(NotImplementedError):
            self.c.begin(Request(0xa10001, True, upper=False, lower=True))

    def test_unmapped_does_not_ack(self):
        self.c.begin(Request(0x400000, True))
        self.assertFalse(self.c.clock())
        self.assertEqual(self.c.finish(), (False, None))

if __name__ == "__main__":
    unittest.main()
