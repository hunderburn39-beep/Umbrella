"""TST.L absolute-long: read ordering, CCR and boundary tests."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def cpu_for(address=0xff0020):
    rom = bytearray(0x106)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = (0x4ab9).to_bytes(2, "big")
    rom[0x102:0x106] = address.to_bytes(4, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class TSTLongAbsoluteTests(unittest.TestCase):
    def test_zero_sets_z_preserves_x(self):
        cpu = cpu_for()
        cpu.ccr = 0x13
        self.assertEqual(cpu.step().mnemonic, "TST.L (abs.l)")
        self.assertEqual(cpu.ccr, 0x14)
        self.assertEqual(cpu.pc, 0x106)

    def test_negative_32bit_value_sets_n(self):
        cpu = cpu_for()
        cpu.bus.memory.write_word(0xff0020, 0x8000)
        cpu.bus.memory.write_word(0xff0022, 0x0001)
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0x08)
        self.assertEqual(cpu.bus.memory.read_word(0xff0020), 0x8000)
        self.assertEqual(cpu.bus.memory.read_word(0xff0022), 0x0001)

    def test_low_word_nonzero_is_not_zero(self):
        cpu = cpu_for()
        cpu.bus.memory.write_word(0xff0022, 1)
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0)

    def test_odd_address_rejected(self):
        cpu = cpu_for(0xff0021)
        with self.assertRaisesRegex(ValueError, "unaligned"):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_crosses_24bit_boundary_rejected(self):
        cpu = cpu_for(0xfffffe)
        with self.assertRaisesRegex(ValueError, "outside 24-bit"):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_vdp_without_ready_does_not_acknowledge(self):
        cpu = cpu_for(0xc00000)
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.completed_vdp_reads, 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
