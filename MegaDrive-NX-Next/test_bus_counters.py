"""Acknowledged bus-transfer counters, not clock-cycle measurements."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Request


class BusCountersTests(unittest.TestCase):
    def test_rom_read_and_ram_write_are_counted_once(self):
        bus = ReferenceBusController(bytes.fromhex("1234"))
        self.assertEqual(bus.diagnostic_bus_counts(), (0, 0, 0, 0))
        bus.begin(Request(0, True))
        self.assertTrue(bus.clock())
        self.assertEqual(bus.finish(), (True, 0x1234))
        bus.begin(Request(0xff0000, False, 0xabcd))
        self.assertTrue(bus.clock())
        self.assertTrue(bus.finish()[0])
        self.assertEqual(bus.diagnostic_bus_counts(), (1, 1, 0, 0))

    def test_vdp_write_has_separate_subcounter(self):
        bus = ReferenceBusController(bytes.fromhex("4e71"))
        bus.begin(Request(0xc00004, False, 0x8f02))
        self.assertTrue(bus.clock_vdp_reference(ready=True))
        bus.finish()
        self.assertEqual(bus.diagnostic_bus_counts(), (0, 1, 0, 1))

    def test_unready_vdp_does_not_count(self):
        bus = ReferenceBusController(bytes.fromhex("4e71"))
        bus.begin(Request(0xc00004, False, 0x8f02))
        self.assertFalse(bus.clock_vdp_reference(ready=False))
        self.assertEqual(bus.diagnostic_bus_counts(), (0, 0, 0, 0))
        self.assertTrue(bus.clock_vdp_reference(ready=True))
        bus.finish()
        self.assertEqual(bus.diagnostic_bus_counts(), (0, 1, 0, 1))

    def test_repeated_ack_sample_not_double_counted(self):
        bus = ReferenceBusController(bytes.fromhex("1234"))
        bus.begin(Request(0, True))
        self.assertTrue(bus.clock())
        self.assertTrue(bus.clock())
        bus.finish()
        self.assertEqual(bus.diagnostic_bus_counts(), (1, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
