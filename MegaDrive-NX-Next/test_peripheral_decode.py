import unittest
from peripheral_decode import Device, select, io_register_name

class PeripheralDecodeTests(unittest.TestCase):
    def test_cartridge(self):
        self.assertEqual(select(0x3ffffe).device, Device.CARTRIDGE)
    def test_z80(self):
        self.assertEqual(select(0xa00000).device, Device.Z80)
    def test_io(self):
        self.assertEqual(select(0xa10002).device, Device.IO)
    def test_vdp(self):
        self.assertEqual(select(0xc00004).device, Device.VDP)
    def test_ram_mirror(self):
        self.assertEqual(select(0xe00010).offset, select(0xff0010).offset)
    def test_unknown(self):
        self.assertEqual(select(0x400000).device, Device.UNKNOWN)
    def test_io_registers(self):
        self.assertEqual(io_register_name(0xa10000), "VERSION")
        self.assertEqual(io_register_name(0xa11100), "Z80_BUSREQ")
        self.assertEqual(io_register_name(0xa11200), "Z80_RESET")
        self.assertIsNone(io_register_name(0xa10020))
    def test_byte_lane(self):
        s = select(0xa10003, upper=False, lower=True)
        self.assertTrue(s.lower)
        with self.assertRaises(ValueError):
            select(0xa10003, upper=True, lower=False)
    def test_invalid_address(self):
        with self.assertRaises(ValueError):
            select(0x1000000)
    def test_no_lane(self):
        with self.assertRaises(ValueError):
            select(0x100, upper=False, lower=False)

if __name__ == "__main__":
    unittest.main()
