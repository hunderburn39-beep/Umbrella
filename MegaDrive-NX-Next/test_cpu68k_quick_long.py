"""32-bit quick arithmetic flags and register selection."""
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
    return cpu

class QuickLongTests(unittest.TestCase):
    def test_add_one(self):
        cpu = cpu_for(0x5280, 0x10000)
        self.assertEqual(cpu.step().mnemonic, "ADDQ.L #imm,Dn")
        self.assertEqual(cpu.d[0], 0x10001)
        self.assertEqual(cpu.ccr, 0)

    def test_add_eight(self):
        cpu = cpu_for(0x5080, 9)
        cpu.step()
        self.assertEqual(cpu.d[0], 17)

    def test_add_wrap_sets_xzc(self):
        cpu = cpu_for(0x5280, 0xffffffff)
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, 0x15)

    def test_add_overflow(self):
        cpu = cpu_for(0x5280, 0x7fffffff)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x80000000)
        self.assertEqual(cpu.ccr, 0x0a)

    def test_sub_one(self):
        cpu = cpu_for(0x5380, 5)
        self.assertEqual(cpu.step().mnemonic, "SUBQ.L #imm,Dn")
        self.assertEqual(cpu.d[0], 4)

    def test_sub_borrow(self):
        cpu = cpu_for(0x5380, 0)
        cpu.step()
        self.assertEqual(cpu.d[0], 0xffffffff)
        self.assertEqual(cpu.ccr, 0x19)

    def test_sub_overflow(self):
        cpu = cpu_for(0x5380, 0x80000000)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x7fffffff)
        self.assertEqual(cpu.ccr, 0x02)

    def test_register_seven(self):
        cpu = cpu_for(0x5287, 0x12345678, reg=7)
        cpu.step()
        self.assertEqual(cpu.d[7], 0x12345679)
        self.assertEqual(cpu.d[0], 0)

if __name__ == "__main__":
    unittest.main()
