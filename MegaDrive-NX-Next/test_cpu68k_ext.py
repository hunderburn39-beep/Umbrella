"""68000 EXT sign extension and CCR regression tests."""
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
    cpu.d[reg] = value
    cpu.ccr = 0x1f
    return cpu

class ExtTests(unittest.TestCase):
    def test_ext_word_negative_preserves_upper_word(self):
        cpu = cpu_for(0x4880, 0x12340080)
        self.assertEqual(cpu.step().mnemonic, "EXT.W Dn")
        self.assertEqual(cpu.d[0], 0x1234ff80)
        self.assertEqual(cpu.ccr, 0x18)

    def test_ext_word_positive(self):
        cpu = cpu_for(0x4880, 0xabcd007f)
        cpu.step()
        self.assertEqual(cpu.d[0], 0xabcd007f)
        self.assertEqual(cpu.ccr, 0x10)

    def test_ext_word_zero(self):
        cpu = cpu_for(0x4880, 0xffff0000)
        cpu.step()
        self.assertEqual(cpu.d[0], 0xffff0000)
        self.assertEqual(cpu.ccr, 0x14)

    def test_ext_long_negative(self):
        cpu = cpu_for(0x48c0, 0x00008000)
        self.assertEqual(cpu.step().mnemonic, "EXT.L Dn")
        self.assertEqual(cpu.d[0], 0xffff8000)
        self.assertEqual(cpu.ccr, 0x18)

    def test_ext_long_positive(self):
        cpu = cpu_for(0x48c0, 0xffff7fff)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x7fff)
        self.assertEqual(cpu.ccr, 0x10)

    def test_ext_long_zero_and_register_selection(self):
        cpu = cpu_for(0x48c5, 0x00000000, reg=5)
        cpu.d[0] = 0x12345678
        cpu.step()
        self.assertEqual(cpu.d[5], 0)
        self.assertEqual(cpu.d[0], 0x12345678)
        self.assertEqual(cpu.ccr, 0x14)

if __name__ == "__main__":
    unittest.main()
