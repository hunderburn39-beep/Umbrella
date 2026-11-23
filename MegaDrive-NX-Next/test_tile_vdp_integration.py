import unittest
from vdp_ports import VDPPorts
from tiles import decode_tile

class TileVDPIntegrationTests(unittest.TestCase):
    def test_vdp_data_transfer_populates_tile(self):
        v = VDPPorts()
        v.write_control(0x8f02)
        v.write_control(0x4000)
        v.write_control(0x0000)
        for _ in range(16):
            v.write_data(0x1234)
        tile = decode_tile(v.vram, 0)
        self.assertEqual(tile, ((1, 2, 3, 4, 1, 2, 3, 4),) * 8)

    def test_tile_one_independent(self):
        v = VDPPorts()
        v.write_control(0x8f02)
        v.write_control(0x4020)
        v.write_control(0)
        for _ in range(16):
            v.write_data(0xffff)
        self.assertEqual(decode_tile(v.vram, 1)[0], (15,) * 8)
        self.assertEqual(decode_tile(v.vram, 0)[0], (0,) * 8)

if __name__ == "__main__":
    unittest.main()
