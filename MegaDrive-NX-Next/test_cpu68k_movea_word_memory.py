"""MOVEA.W memory forms sign extend without touching CCR."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(program):
    rom = bytearray(0x100 + len(bytes.fromhex(program)))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = bytes.fromhex(program)
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.ccr = 0x1f
    return cpu

class MoveAWordMemoryTests(unittest.TestCase):
    def test_indirect_negative_sign_extension(self):
        cpu = cpu_for("3050")
        cpu.a[0] = 0xff0100
        cpu.bus.memory.ram[0x100:0x102] = bytes.fromhex("8001")
        self.assertEqual(cpu.step().mnemonic, "MOVEA.W (An),Am")
        self.assertEqual(cpu.a[0], 0xffff8001)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_indirect_positive_other_destination(self):
        cpu = cpu_for("3250")
        cpu.a[0] = 0xff0200
        cpu.bus.memory.ram[0x200:0x202] = bytes.fromhex("7fff")
        cpu.step()
        self.assertEqual(cpu.a[1], 0x7fff)
        self.assertEqual(cpu.a[0], 0xff0200)

    def test_absolute_long_negative(self):
        cpu = cpu_for("3079 00ff 0100")
        cpu.bus.memory.ram[0x100:0x102] = bytes.fromhex("ffff")
        self.assertEqual(cpu.step().mnemonic, "MOVEA.W (abs.l),An")
        self.assertEqual(cpu.a[0], 0xffffffff)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_absolute_long_positive(self):
        cpu = cpu_for("3479 00ff 0100")
        cpu.bus.memory.ram[0x100:0x102] = bytes.fromhex("1234")
        cpu.step()
        self.assertEqual(cpu.a[2], 0x1234)

    def test_unaligned_indirect_does_not_modify_address(self):
        cpu = cpu_for("3050")
        cpu.a[0] = 0xff0101
        with self.assertRaisesRegex(ValueError, "unaligned"):
            cpu.step()
        self.assertEqual(cpu.a[0], 0xff0101)

if __name__ == "__main__":
    unittest.main()
