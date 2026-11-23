import unittest
from boot_bus import reset_vectors, read_rom_word, decode_region, boot_probe

class BootBusTests(unittest.TestCase):
    def setUp(self):
        self.rom = bytes.fromhex("00 ff 00 00 00 00 01 00") + bytes(0xf8) + bytes.fromhex("4e 71")

    def test_reset_vectors_big_endian(self):
        v = reset_vectors(self.rom)
        self.assertEqual(v.initial_ssp, 0xff0000)
        self.assertEqual(v.initial_pc, 0x100)

    def test_first_opcode(self):
        self.assertEqual(boot_probe(self.rom)["first_opcode"], 0x4e71)

    def test_address_regions(self):
        self.assertEqual(decode_region(0xc00004), "vdp-candidate")
        self.assertEqual(decode_region(0xa10000), "io-control")
        self.assertEqual(decode_region(0xe00000), "work-ram-mirror")
        self.assertEqual(decode_region(0x200), "cartridge")

    def test_short_rom(self):
        with self.assertRaises(ValueError):
            reset_vectors(b"abc")

    def test_odd_read(self):
        with self.assertRaises(ValueError):
            read_rom_word(self.rom, 1)

    def test_missing_rom_data(self):
        with self.assertRaises(ValueError):
            read_rom_word(self.rom, 0x200)

    def test_odd_pc_rejected(self):
        rom = bytes.fromhex("00 ff 00 00 00 00 00 01") + bytes(4)
        with self.assertRaisesRegex(ValueError, "odd initial PC"):
            boot_probe(rom)

    def test_odd_initial_ssp_rejected(self):
        rom = bytes.fromhex("00 ff 00 01 00 00 01 00") + bytes(0xf8) + bytes.fromhex("4e 71")
        with self.assertRaisesRegex(ValueError, "odd initial SSP"):
            boot_probe(rom)

    def test_initial_ssp_outside_24bit_bus_rejected(self):
        rom = bytes.fromhex("01 00 00 00 00 00 01 00") + bytes(0xf8) + bytes.fromhex("4e 71")
        with self.assertRaisesRegex(ValueError, "outside 24-bit"):
            boot_probe(rom)

    def test_outside_rom_pc_rejected(self):
        rom = bytes.fromhex("00 ff 00 00 00 40 00 00")
        with self.assertRaisesRegex(ValueError, "outside"):
            boot_probe(rom)

if __name__ == "__main__":
    unittest.main()
