"""68000 TST.L (An): big-endian reads, CCR and bounds checks."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def cpu_for():
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = bytes.fromhex("4a90")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.a[0] = 0xff0020
    return cpu

class TSTLongIndirectTests(unittest.TestCase):
    def test_zero_long_preserves_x(self):
        cpu = cpu_for()
        cpu.ccr = 0x13
        self.assertEqual(cpu.step().mnemonic, "TST.L (An)")
        self.assertEqual(cpu.ccr, 0x14)
        self.assertEqual(cpu.a[0], 0xff0020)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_negative_long_sets_n_without_modifying_ram(self):
        cpu = cpu_for()
        cpu.bus.memory.write_word(0xff0020, 0x8000)
        cpu.bus.memory.write_word(0xff0022, 0x0001)
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0x08)
        self.assertEqual(cpu.bus.memory.read_word(0xff0020), 0x8000)
        self.assertEqual(cpu.bus.memory.read_word(0xff0022), 0x0001)

    def test_low_word_nonzero_means_long_not_zero(self):
        cpu = cpu_for()
        cpu.bus.memory.write_word(0xff0022, 1)
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0)

    def test_odd_address_rejected_without_bus_cycle(self):
        cpu = cpu_for()
        cpu.a[0] = 0xff0021
        with self.assertRaisesRegex(ValueError, "unaligned"):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_long_crossing_address_space_rejected(self):
        cpu = cpu_for()
        cpu.a[0] = 0xfffffe
        with self.assertRaisesRegex(ValueError, "outside 24-bit"):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_unsupported_vdp_long_read_does_not_ack(self):
        cpu = cpu_for()
        cpu.a[0] = 0xc00000
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.completed_vdp_reads, 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
