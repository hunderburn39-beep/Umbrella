"""Reset vector validation must be atomic and agree with the boot probe."""
import unittest
from boot_bus import boot_probe
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def make_rom(ssp=0xff0100, pc=0x100):
    rom = bytearray(0x102)
    rom[:4] = ssp.to_bytes(4, "big")
    rom[4:8] = pc.to_bytes(4, "big")
    rom[0x100:0x102] = bytes.fromhex("4e71")
    return bytes(rom)

class CPUResetVectorTests(unittest.TestCase):
    def test_valid_vectors_reset_cpu(self):
        cpu = CPU68KReference(ReferenceBusController(make_rom()))
        cpu.reset()
        self.assertEqual(cpu.pc, 0x100)
        self.assertEqual(cpu.a[7], 0xff0100)

    def test_odd_ssp_rejected_before_mutation(self):
        cpu = CPU68KReference(ReferenceBusController(make_rom(ssp=0xff0101)))
        cpu.pc = 0x200
        cpu.d[0] = 42
        with self.assertRaisesRegex(ValueError, "odd reset SSP"):
            cpu.reset()
        self.assertEqual(cpu.pc, 0x200)
        self.assertEqual(cpu.d[0], 42)

    def test_out_of_range_ssp_rejected(self):
        cpu = CPU68KReference(ReferenceBusController(make_rom(ssp=0x01000000)))
        with self.assertRaisesRegex(ValueError, "outside 24-bit"):
            cpu.reset()

    def test_odd_pc_rejected(self):
        cpu = CPU68KReference(ReferenceBusController(make_rom(pc=0x101)))
        with self.assertRaisesRegex(ValueError, "odd reset PC"):
            cpu.reset()

    def test_out_of_range_pc_rejected(self):
        cpu = CPU68KReference(ReferenceBusController(make_rom(pc=0x01000000)))
        with self.assertRaisesRegex(ValueError, "outside 24-bit"):
            cpu.reset()

    def test_boot_probe_agrees_on_invalid_ssp(self):
        rom = make_rom(ssp=0xff0101)
        with self.assertRaisesRegex(ValueError, "odd initial SSP"):
            boot_probe(rom)
        with self.assertRaisesRegex(ValueError, "odd reset SSP"):
            CPU68KReference(ReferenceBusController(rom)).reset()

if __name__ == "__main__":
    unittest.main()
