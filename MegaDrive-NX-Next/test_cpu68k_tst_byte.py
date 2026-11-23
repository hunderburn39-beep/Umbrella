"""Byte-sized TST on data registers, without changing the upper bits."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def make_cpu(opcode):
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = opcode.to_bytes(2, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class TSTByteTests(unittest.TestCase):
    def test_zero_low_byte_ignores_upper_bits(self):
        cpu = make_cpu(0x4a00)
        cpu.d[0] = 0xdeadbe00
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 4)
        self.assertEqual(cpu.d[0], 0xdeadbe00)

    def test_negative_low_byte(self):
        cpu = make_cpu(0x4a03)
        cpu.d[3] = 0x00000080
        self.assertEqual(cpu.step().mnemonic, "TST.B Dn")
        self.assertEqual(cpu.ccr & 0x0f, 8)

    def test_positive_byte_ignores_negative_high_word(self):
        cpu = make_cpu(0x4a07)
        cpu.d[7] = 0x8000007f
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0)

    def test_preserves_extend_clears_overflow_and_carry(self):
        cpu = make_cpu(0x4a01)
        cpu.d[1] = 1
        cpu.ccr = 0x1f
        cpu.step()
        self.assertEqual(cpu.ccr, 0x10)

    def test_does_not_touch_other_registers(self):
        cpu = make_cpu(0x4a05)
        cpu.d[5] = 0x12345680
        cpu.d[0] = 0xaabbccdd
        cpu.step()
        self.assertEqual(cpu.d[5], 0x12345680)
        self.assertEqual(cpu.d[0], 0xaabbccdd)
        self.assertEqual(cpu.pc, 0x102)

if __name__ == "__main__":
    unittest.main()
