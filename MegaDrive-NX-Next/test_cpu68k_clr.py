"""CLR word and long preserve X and update Z/N/V/C."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def make_cpu(opcode, register=0):
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = opcode.to_bytes(2, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.d[register] = 0xdeadbeef
    cpu.ccr = 0x1b
    return cpu

class ClearRegisterTests(unittest.TestCase):
    def test_clear_byte_preserves_upper_24_bits(self):
        cpu = make_cpu(0x4200)
        self.assertEqual(cpu.step().mnemonic, "CLR.B Dn")
        self.assertEqual(cpu.d[0], 0xdeadbe00)
        self.assertEqual(cpu.ccr, 0x14)

    def test_clear_byte_on_d5(self):
        cpu = make_cpu(0x4205, register=5)
        cpu.step()
        self.assertEqual(cpu.d[5], 0xdeadbe00)
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.pc, 0x102)

    def test_clear_word_preserves_high_word(self):
        cpu = make_cpu(0x4240)
        self.assertEqual(cpu.step().mnemonic, "CLR.W Dn")
        self.assertEqual(cpu.d[0], 0xdead0000)
        self.assertEqual(cpu.ccr, 0x14)

    def test_clear_long_zeros_all_bits(self):
        cpu = make_cpu(0x4280)
        self.assertEqual(cpu.step().mnemonic, "CLR.L Dn")
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, 0x14)

    def test_clear_word_on_d7(self):
        cpu = make_cpu(0x4247, register=7)
        cpu.d[0] = 0x11223344
        cpu.step()
        self.assertEqual(cpu.d[7], 0xdead0000)
        self.assertEqual(cpu.d[0], 0x11223344)

    def test_clear_long_on_d3(self):
        cpu = make_cpu(0x4283, register=3)
        cpu.step()
        self.assertEqual(cpu.d[3], 0)
        self.assertEqual(cpu.pc, 0x102)

if __name__ == "__main__":
    unittest.main()
