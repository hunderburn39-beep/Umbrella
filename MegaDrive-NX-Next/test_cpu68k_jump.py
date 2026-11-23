"""Reference 68000 unconditional JMP control-flow tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(hex_program):
    data = bytes.fromhex(hex_program)
    rom = bytearray(0x100 + len(data))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = data
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class JumpTests(unittest.TestCase):
    def test_absolute_long_jmp_skips_instruction(self):
        cpu = cpu_for("4ef9 0000 010c 7001 4e71 4e71 7207")
        self.assertEqual(cpu.step().mnemonic, "JMP")
        self.assertEqual(cpu.pc, 0x10c)
        cpu.step()
        self.assertEqual(cpu.d[1], 7)
        self.assertEqual(cpu.d[0], 0)

    def test_indirect_jmp_uses_address_register(self):
        cpu = cpu_for("207c 0000 010c 4ed0 7001 4e71 7207")
        cpu.run(2)
        self.assertEqual(cpu.pc, 0x10c)
        cpu.step()
        self.assertEqual(cpu.d[1], 7)
        self.assertEqual(cpu.d[0], 0)

    def test_absolute_jmp_rejects_odd_target(self):
        cpu = cpu_for("4ef9 0000 0101")
        with self.assertRaises(ValueError):
            cpu.step()

    def test_indirect_jmp_rejects_odd_target(self):
        cpu = cpu_for("207c 0000 0101 4ed0")
        cpu.step()
        with self.assertRaises(ValueError):
            cpu.step()

    def test_jump_does_not_change_stack(self):
        cpu = cpu_for("4ef9 0000 0106 4e71")
        original = cpu.a[7]
        cpu.step()
        self.assertEqual(cpu.a[7], original)

if __name__ == "__main__":
    unittest.main()
