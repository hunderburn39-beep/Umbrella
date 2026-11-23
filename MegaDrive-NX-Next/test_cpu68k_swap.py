"""68000 SWAP Dn instruction, condition flags and register selection."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(opcode, value, reg=0, ccr=0x1f):
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = opcode.to_bytes(2, "big")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.d[reg] = value
    cpu.ccr = ccr
    return cpu

class SwapTests(unittest.TestCase):
    def test_swap_halves(self):
        cpu = cpu_for(0x4840, 0x1234abcd)
        self.assertEqual(cpu.step().mnemonic, "SWAP Dn")
        self.assertEqual(cpu.d[0], 0xabcd1234)
        self.assertEqual(cpu.ccr, 0x18)

    def test_swap_zero(self):
        cpu = cpu_for(0x4840, 0)
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, 0x14)

    def test_swap_positive(self):
        cpu = cpu_for(0x4840, 0x00010000)
        cpu.step()
        self.assertEqual(cpu.d[0], 1)
        self.assertEqual(cpu.ccr, 0x10)

    def test_swap_register_seven(self):
        cpu = cpu_for(0x4847, 0xffff0001, reg=7)
        cpu.d[0] = 0x12345678
        cpu.step()
        self.assertEqual(cpu.d[7], 0x0001ffff)
        self.assertEqual(cpu.d[0], 0x12345678)
        self.assertEqual(cpu.ccr, 0x10)

    def test_swap_twice_restores_value(self):
        cpu = cpu_for(0x4840, 0xdeadbeef)
        cpu.step()
        cpu.pc = 0x100
        cpu.step()
        self.assertEqual(cpu.d[0], 0xdeadbeef)
        self.assertEqual(cpu.ccr, 0x18)

if __name__ == "__main__":
    unittest.main()
