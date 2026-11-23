"""TST.W absolute-long 68000 reference bus regression checks."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def make_cpu(address=0xff0020):
    rom = bytearray(0x106)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = (0x4a79).to_bytes(2, "big")
    rom[0x102:0x106] = address.to_bytes(4, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class TSTAbsoluteTests(unittest.TestCase):
    def test_zero_ram_sets_zero_flag_and_preserves_extend(self):
        cpu = make_cpu()
        cpu.ccr = 0x13
        self.assertEqual(cpu.step().mnemonic, "TST.W (abs.l)")
        self.assertEqual(cpu.ccr, 0x14)
        self.assertEqual(cpu.pc, 0x106)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_negative_ram_sets_negative_flag(self):
        cpu = make_cpu()
        cpu.bus.memory.write_word(0xff0020, 0x8001)
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0x08)
        self.assertEqual(cpu.bus.memory.read_word(0xff0020), 0x8001)

    def test_positive_ram_clears_nzvc(self):
        cpu = make_cpu()
        cpu.bus.memory.write_word(0xff0020, 1)
        cpu.ccr = 0x1f
        cpu.step()
        self.assertEqual(cpu.ccr, 0x10)

    def test_odd_absolute_address_is_rejected(self):
        cpu = make_cpu(0xff0021)
        with self.assertRaises(ValueError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_vdp_port_stalls_without_external_readiness(self):
        cpu = make_cpu(0xc00000)
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.completed_vdp_reads, 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_out_of_range_address_is_rejected(self):
        cpu = make_cpu(0x01000000)
        with self.assertRaisesRegex(ValueError, "outside 24-bit"):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
