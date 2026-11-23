import unittest
from vdp_ports import VDPPorts
from bus_controller import ReferenceBusController
from bus_cycle import Request

class VDPTransferTests(unittest.TestCase):
    def setUp(self):
        self.v = VDPPorts()

    def test_write_auto_increment(self):
        self.v.write_control(0x8f02)
        self.v.write_control(0x4000)
        self.v.write_control(0)
        self.v.write_data(0x1234)
        self.v.write_data(0xabcd)
        self.assertEqual(self.v.vram.read_word(0), 0x1234)
        self.assertEqual(self.v.vram.read_word(2), 0xabcd)
        self.assertEqual(self.v.active_command.address, 4)

    def test_read_auto_increment(self):
        self.v.vram.write_word(0, 0x1234)
        self.v.vram.write_word(2, 0x5678)
        self.v.write_control(0x8f02)
        self.v.write_control(0)
        self.v.write_control(0)
        self.assertEqual(self.v.read_data(), 0x1234)
        self.assertEqual(self.v.read_data(), 0x5678)

    def test_zero_increment(self):
        self.v.write_control(0x4000)
        self.v.write_control(0)
        self.v.write_data(0x1234)
        self.v.write_data(0x5678)
        self.assertEqual(self.v.vram.read_word(0), 0x5678)

    def test_wrap(self):
        self.v.write_control(0x8f02)
        self.v.write_control(0x7fff)
        self.v.write_control(3)
        self.v.write_data(0xbeef)
        self.assertEqual(self.v.active_command.address, 1)

    def test_unsupported_command(self):
        self.v.write_control(0xc000)
        self.v.write_control(0)
        with self.assertRaises(NotImplementedError):
            self.v.write_data(0x1111)

    def test_bus_does_not_implicitly_write_vram(self):
        c = ReferenceBusController(bytes.fromhex("4e 71"))
        c.begin(Request(0xc00000, False, 0xaaaa))
        self.assertFalse(c.clock())
        c.finish()
        self.assertEqual(c.vdp.vram.read_word(0), 0)

if __name__ == "__main__":
    unittest.main()
