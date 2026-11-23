"""TST.W (An) reference bus and CCR regression checks."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def make_cpu():
    rom = bytearray(0x104)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = bytes.fromhex("4a50 4a51")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class TSTIndirectTests(unittest.TestCase):
    def test_zero_ram_word_sets_z_and_preserves_x(self):
        cpu = make_cpu()
        cpu.a[0] = 0xff0020
        cpu.ccr = 0x13
        self.assertEqual(cpu.step().mnemonic, "TST.W (An)")
        self.assertEqual(cpu.ccr, 0x14)
        self.assertEqual(cpu.a[0], 0xff0020)
        self.assertEqual(cpu.bus.memory.read_word(0xff0020), 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_negative_ram_word_sets_n(self):
        cpu = make_cpu()
        cpu.a[0] = 0xff0020
        cpu.bus.memory.write_word(0xff0020, 0x8000)
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0x08)
        self.assertEqual(cpu.bus.memory.read_word(0xff0020), 0x8000)

    def test_other_address_register(self):
        cpu = make_cpu()
        cpu.a[0] = 0xff0020
        cpu.a[1] = 0xff0030
        cpu.bus.memory.write_word(0xff0030, 0x0001)
        cpu.pc = 0x102
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0)

    def test_odd_address_rejected(self):
        cpu = make_cpu()
        cpu.a[0] = 0xff0021
        with self.assertRaises(ValueError):
            cpu.step()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_vdp_data_port_requires_external_ready(self):
        cpu = make_cpu()
        cpu.a[0] = 0xc00000
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(cpu.bus.completed_vdp_reads, 0)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
