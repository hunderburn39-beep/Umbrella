"""68000 PEA pushes effective addresses as big-endian longwords."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(program):
    data = bytes.fromhex(program)
    rom = bytearray(0x100 + len(data))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = data
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.ccr = 0x1f
    return cpu

class PEATests(unittest.TestCase):
    def test_indirect_pushes_address_not_data(self):
        cpu = cpu_for("4850")
        cpu.a[0] = 0x12345678
        self.assertEqual(cpu.step().mnemonic, "PEA (An)")
        self.assertEqual(cpu.a[7], 0xff00fc)
        self.assertEqual(cpu.bus.memory.read_word(0xff00fc), 0x1234)
        self.assertEqual(cpu.bus.memory.read_word(0xff00fe), 0x5678)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_absolute_long_pushes_address(self):
        cpu = cpu_for("4879 00c0 0004")
        self.assertEqual(cpu.step().mnemonic, "PEA (abs.l)")
        self.assertEqual(cpu.bus.memory.read_word(0xff00fc), 0x00c0)
        self.assertEqual(cpu.bus.memory.read_word(0xff00fe), 0x0004)
        self.assertEqual(cpu.pc, 0x106)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_pea_a7_captures_original_stack_pointer(self):
        cpu = cpu_for("4857")
        original = cpu.a[7]
        cpu.step()
        self.assertEqual(cpu.a[7], original - 4)
        self.assertEqual(cpu.bus.memory.read_word(original - 4), original >> 16)
        self.assertEqual(cpu.bus.memory.read_word(original - 2), original & 0xffff)

    def test_pea_does_not_read_target_peripheral(self):
        cpu = cpu_for("4850")
        cpu.a[0] = 0xc00004
        cpu.step()
        self.assertEqual(cpu.bus.completed_vdp_reads, 0)
        self.assertEqual(cpu.bus.memory.read_word(0xff00fe), 4)

    def test_odd_stack_rejected(self):
        cpu = cpu_for("4850")
        cpu.a[7] = 0xff0101
        with self.assertRaisesRegex(ValueError, "unaligned stack pointer"):
            cpu.step()
        self.assertEqual(cpu.a[7], 0xff0101)

if __name__ == "__main__":
    unittest.main()
