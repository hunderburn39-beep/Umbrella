"""68000 ADDQ.B and SUBQ.B data register arithmetic."""
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

class QuickByteTests(unittest.TestCase):
    def test_addq_byte_preserves_upper_bits(self):
        cpu = cpu_for(0x5200, 0x12345601)
        self.assertEqual(cpu.step().mnemonic, "ADDQ.B #imm,Dn")
        self.assertEqual(cpu.d[0], 0x12345602)
        self.assertEqual(cpu.ccr, 0)

    def test_addq_byte_eight(self):
        cpu = cpu_for(0x5000, 0xf0)
        cpu.step()
        self.assertEqual(cpu.d[0], 0xf8)
        self.assertEqual(cpu.ccr, 0x08)

    def test_addq_byte_overflow(self):
        cpu = cpu_for(0x5200, 0x7f)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x80)
        self.assertEqual(cpu.ccr, 0x0a)

    def test_addq_byte_carry(self):
        cpu = cpu_for(0x5200, 0xff)
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, 0x15)

    def test_subq_byte_borrow(self):
        cpu = cpu_for(0x5300, 0)
        self.assertEqual(cpu.step().mnemonic, "SUBQ.B #imm,Dn")
        self.assertEqual(cpu.d[0], 0xff)
        self.assertEqual(cpu.ccr, 0x19)

    def test_subq_byte_signed_overflow(self):
        cpu = cpu_for(0x5300, 0x80)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x7f)
        self.assertEqual(cpu.ccr, 0x02)

    def test_subq_byte_zero(self):
        cpu = cpu_for(0x5300, 1)
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, 0x04)

if __name__ == "__main__":
    unittest.main()
