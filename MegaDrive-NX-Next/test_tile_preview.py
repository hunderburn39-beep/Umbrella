import unittest
from vdp_ports import VDPPorts
from tiles import encode_tile
from tile_preview import tile_rgb, tile_ppm

class TilePreviewTests(unittest.TestCase):
    def setUp(self):
        self.vdp = VDPPorts()

    def test_red_pixel(self):
        self.vdp.cram.write(1, 0x000e)
        encode_tile(self.vdp.vram, 0, [[1] * 8 for _ in range(8)])
        self.assertEqual(tile_rgb(self.vdp, 0)[0][0], (255, 0, 0))

    def test_palette_bank(self):
        self.vdp.cram.write(17, 0x0e00)
        encode_tile(self.vdp.vram, 0, [[1] * 8 for _ in range(8)])
        self.assertEqual(tile_rgb(self.vdp, 0, 1)[0][0], (0, 0, 255))

    def test_ppm_header_and_size(self):
        ppm = tile_ppm(self.vdp, 0)
        self.assertTrue(ppm.startswith(b"P6\n8 8\n255\n"))
        self.assertEqual(len(ppm), len(b"P6\n8 8\n255\n") + 8 * 8 * 3)

    def test_invalid_palette(self):
        with self.assertRaises(ValueError):
            tile_rgb(self.vdp, 0, 4)

if __name__ == "__main__":
    unittest.main()
