"""68000 quick word arithmetic: carry, overflow, X, and upper register preservation."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(opcode, value, ccr=0):
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = opcode.to_bytes(2, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.d[0] = value
    cpu.ccr = ccr
    return cpu

class QuickWordTests(unittest.TestCase):
    def test_add_one(self):
        cpu = cpu_for(0x5240, 0xabcd0001)
        self.assertEqual(cpu.step().mnemonic, "ADDQ.W #imm,Dn")
        self.assertEqual(cpu.d[0], 0xabcd0002)
        self.assertEqual(cpu.ccr, 0)

    def test_add_eight_encoded_as_zero(self):
        cpu = cpu_for(0x5040, 0x00000001)
        cpu.step()
        self.assertEqual(cpu.d[0], 9)

    def test_add_wrap_sets_extend_carry_zero(self):
        cpu = cpu_for(0x5240, 0x1234ffff)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x12340000)
        self.assertEqual(cpu.ccr, 0x15)

    def test_add_signed_overflow(self):
        cpu = cpu_for(0x5240, 0x7fff)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x8000)
        self.assertEqual(cpu.ccr, 0x0a)

    def test_sub_one(self):
        cpu = cpu_for(0x5340, 0x12340002)
        self.assertEqual(cpu.step().mnemonic, "SUBQ.W #imm,Dn")
        self.assertEqual(cpu.d[0], 0x12340001)
        self.assertEqual(cpu.ccr, 0)

    def test_sub_borrow_sets_extend_carry_negative(self):
        cpu = cpu_for(0x5340, 0)
        cpu.step()
        self.assertEqual(cpu.d[0], 0xffff)
        self.assertEqual(cpu.ccr, 0x19)

    def test_sub_signed_overflow(self):
        cpu = cpu_for(0x5340, 0x8000)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x7fff)
        self.assertEqual(cpu.ccr, 0x02)

    def test_sub_eight_encoded_as_zero(self):
        cpu = cpu_for(0x5140, 9)
        cpu.step()
        self.assertEqual(cpu.d[0], 1)

if __name__ == "__main__":
    unittest.main()
