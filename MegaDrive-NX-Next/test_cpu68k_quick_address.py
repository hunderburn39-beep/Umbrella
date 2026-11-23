"""68000 quick arithmetic on address registers never changes CCR."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(opcode, value, reg=0):
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = opcode.to_bytes(2, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.a[reg] = value
    cpu.ccr = 0x1f
    return cpu

class QuickAddressTests(unittest.TestCase):
    def test_addq_word_uses_full_32_bit_address(self):
        cpu = cpu_for(0x5248, 0x0000ffff)
        self.assertEqual(cpu.step().mnemonic, "ADDQ.W #imm,An")
        self.assertEqual(cpu.a[0], 0x00010000)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_addq_long_eight(self):
        cpu = cpu_for(0x5088, 0x100)
        self.assertEqual(cpu.step().mnemonic, "ADDQ.L #imm,An")
        self.assertEqual(cpu.a[0], 0x108)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_subq_word_does_not_truncate_address(self):
        cpu = cpu_for(0x5348, 0x00010000)
        self.assertEqual(cpu.step().mnemonic, "SUBQ.W #imm,An")
        self.assertEqual(cpu.a[0], 0x0000ffff)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_subq_long_wraps_32_bits(self):
        cpu = cpu_for(0x5388, 0)
        self.assertEqual(cpu.step().mnemonic, "SUBQ.L #imm,An")
        self.assertEqual(cpu.a[0], 0xffffffff)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_a7_uses_address_register_semantics(self):
        cpu = cpu_for(0x524f, 0xff0100, reg=7)
        cpu.step()
        self.assertEqual(cpu.a[7], 0xff0101)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_subq_eight_from_a3(self):
        cpu = cpu_for(0x518b, 0x1000, reg=3)
        cpu.step()
        self.assertEqual(cpu.a[3], 0xff8)
        self.assertEqual(cpu.ccr, 0x1f)

if __name__ == "__main__":
    unittest.main()
