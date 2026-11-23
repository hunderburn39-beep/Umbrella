"""68000 TST data-register instruction regression tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def make_cpu(words):
    data = bytes.fromhex(words)
    rom = bytearray(0x100 + len(data))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = data
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class TestRegisterTests(unittest.TestCase):
    def test_tst_word_zero(self):
        cpu = make_cpu("4a40")
        cpu.d[0] = 0x12340000
        self.assertEqual(cpu.step().mnemonic, "TST.W Dn")
        self.assertEqual(cpu.ccr & 0x0f, 0x04)
        self.assertEqual(cpu.d[0], 0x12340000)

    def test_tst_word_negative(self):
        cpu = make_cpu("4a41")
        cpu.d[1] = 0x00008000
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0x08)

    def test_tst_long_nonzero_positive(self):
        cpu = make_cpu("4a80")
        cpu.d[0] = 0x00010000
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0)

    def test_tst_long_negative(self):
        cpu = make_cpu("4a87")
        cpu.d[7] = 0x80000000
        cpu.step()
        self.assertEqual(cpu.ccr & 0x0f, 0x08)

    def test_tst_preserves_x_and_clears_vc(self):
        cpu = make_cpu("4a40")
        cpu.ccr = 0x13
        cpu.step()
        self.assertEqual(cpu.ccr, 0x14)

    def test_tst_then_beq_branches(self):
        cpu = make_cpu("4a40 6704 7201 4e71 7207")
        cpu.step()
        cpu.step()
        self.assertEqual(cpu.pc, 0x106)
        cpu.step()
        self.assertEqual(cpu.d[1], 0)

if __name__ == "__main__":
    unittest.main()
