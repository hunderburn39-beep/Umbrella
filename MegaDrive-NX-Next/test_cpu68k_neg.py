"""68000 NEG register arithmetic, flags and operand sizing."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(opcode, value):
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = opcode.to_bytes(2, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.d[0] = value
    return cpu

class NegRegisterTests(unittest.TestCase):
    def test_neg_byte_preserves_upper_bits(self):
        cpu = cpu_for(0x4400, 0x12345601)
        self.assertEqual(cpu.step().mnemonic, "NEG.B Dn")
        self.assertEqual(cpu.d[0], 0x123456ff)
        self.assertEqual(cpu.ccr, 0x19)

    def test_neg_word_preserves_upper_bits(self):
        cpu = cpu_for(0x4440, 0x12340001)
        self.assertEqual(cpu.step().mnemonic, "NEG.W Dn")
        self.assertEqual(cpu.d[0], 0x1234ffff)
        self.assertEqual(cpu.ccr, 0x19)

    def test_neg_long(self):
        cpu = cpu_for(0x4480, 2)
        self.assertEqual(cpu.step().mnemonic, "NEG.L Dn")
        self.assertEqual(cpu.d[0], 0xfffffffe)
        self.assertEqual(cpu.ccr, 0x19)

    def test_zero_clears_all_flags(self):
        cpu = cpu_for(0x4480, 0)
        cpu.ccr = 0x1f
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, 0x04)

    def test_byte_signed_overflow(self):
        cpu = cpu_for(0x4400, 0x80)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x80)
        self.assertEqual(cpu.ccr, 0x1b)

    def test_word_signed_overflow(self):
        cpu = cpu_for(0x4440, 0x8000)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x8000)
        self.assertEqual(cpu.ccr, 0x1b)

    def test_long_signed_overflow(self):
        cpu = cpu_for(0x4480, 0x80000000)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x80000000)
        self.assertEqual(cpu.ccr, 0x1b)

if __name__ == "__main__":
    unittest.main()
