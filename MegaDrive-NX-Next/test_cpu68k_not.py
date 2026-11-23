"""68000 NOT data register operations and CCR preservation."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(opcode, value, ccr=0x1f):
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = opcode.to_bytes(2, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.d[0] = value
    cpu.ccr = ccr
    return cpu

class NotRegisterTests(unittest.TestCase):
    def test_not_byte_preserves_upper_bits(self):
        cpu = cpu_for(0x4600, 0x1234560f)
        self.assertEqual(cpu.step().mnemonic, "NOT.B Dn")
        self.assertEqual(cpu.d[0], 0x123456f0)
        self.assertEqual(cpu.ccr, 0x18)

    def test_not_word_preserves_upper_bits(self):
        cpu = cpu_for(0x4640, 0x123400ff)
        self.assertEqual(cpu.step().mnemonic, "NOT.W Dn")
        self.assertEqual(cpu.d[0], 0x1234ff00)
        self.assertEqual(cpu.ccr, 0x18)

    def test_not_long(self):
        cpu = cpu_for(0x4680, 0x00000000)
        self.assertEqual(cpu.step().mnemonic, "NOT.L Dn")
        self.assertEqual(cpu.d[0], 0xffffffff)
        self.assertEqual(cpu.ccr, 0x18)

    def test_not_byte_zero_result(self):
        cpu = cpu_for(0x4600, 0xabcdefFF)
        cpu.step()
        self.assertEqual(cpu.d[0], 0xabcdef00)
        self.assertEqual(cpu.ccr, 0x14)

    def test_not_word_zero_result(self):
        cpu = cpu_for(0x4640, 0xffff)
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, 0x14)

    def test_not_long_zero_result(self):
        cpu = cpu_for(0x4680, 0xffffffff)
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, 0x14)

if __name__ == "__main__":
    unittest.main()
