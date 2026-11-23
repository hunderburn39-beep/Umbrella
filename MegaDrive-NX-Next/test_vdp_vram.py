import unittest
from vdp_ports import VDPPorts
from bus_controller import ReferenceBusController
from bus_cycle import Request

class VDPVRAMIntegrationTests(unittest.TestCase):
    def test_vram_attached_to_vdp(self):
        v = VDPPorts()
        v.diagnostic_vram_write(0x100, 0xdead)
        self.assertEqual(v.diagnostic_vram_read(0x100), 0xdead)

    def test_vdp_data_port_not_faked(self):
        v = VDPPorts()
        v.diagnostic_vram_write(0, 0x1234)
        with self.assertRaises(NotImplementedError):
            v.write_data(0xabcd)
        self.assertEqual(v.diagnostic_vram_read(0), 0x1234)

    def test_main_bus_does_not_write_vram_without_ack(self):
        c = ReferenceBusController(bytes.fromhex("4e 71"))
        c.begin(Request(0xc00000, False, 0x9999))
        self.assertFalse(c.clock())
        self.assertEqual(c.finish(), (False, None))
        self.assertEqual(c.vdp.diagnostic_vram_read(0), 0)

    def test_instances_do_not_share_vram(self):
        a, b = VDPPorts(), VDPPorts()
        a.diagnostic_vram_write(0, 0xabcd)
        self.assertEqual(b.diagnostic_vram_read(0), 0)

if __name__ == "__main__":
    unittest.main()
