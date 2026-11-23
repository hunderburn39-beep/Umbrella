"""MOVEA.W immediate and LEA address calculations preserve CCR."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(program):
    rom = bytearray(0x100 + len(program))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = bytes.fromhex(program)
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.ccr = 0x1f
    return cpu

class AddressOperationsTests(unittest.TestCase):
    def test_movea_word_negative_sign_extension(self):
        cpu = cpu_for("307c 8001")
        self.assertEqual(cpu.step().mnemonic, "MOVEA.W #imm,An")
        self.assertEqual(cpu.a[0], 0xffff8001)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_movea_word_positive(self):
        cpu = cpu_for("327c 7fff")
        cpu.step()
        self.assertEqual(cpu.a[1], 0x7fff)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_movea_word_zero(self):
        cpu = cpu_for("347c 0000")
        cpu.a[2] = 0xffffffff
        cpu.step()
        self.assertEqual(cpu.a[2], 0)

    def test_lea_absolute_long(self):
        cpu = cpu_for("41f9 00ff 0100")
        self.assertEqual(cpu.step().mnemonic, "LEA (abs.l),An")
        self.assertEqual(cpu.a[0], 0xff0100)
        self.assertEqual(cpu.pc, 0x106)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_lea_absolute_does_not_read_target(self):
        cpu = cpu_for("43f9 00c0 0004")
        cpu.step()
        self.assertEqual(cpu.a[1], 0xc00004)
        self.assertEqual(cpu.bus.completed_vdp_reads, 0)

    def test_lea_indirect_copies_address_not_memory(self):
        cpu = cpu_for("43d0")
        cpu.a[0] = 0xc00004
        self.assertEqual(cpu.step().mnemonic, "LEA (An),Am")
        self.assertEqual(cpu.a[1], 0xc00004)
        self.assertEqual(cpu.ccr, 0x1f)

    def test_lea_indirect_same_register(self):
        cpu = cpu_for("41d0")
        cpu.a[0] = 0xff0100
        cpu.step()
        self.assertEqual(cpu.a[0], 0xff0100)

if __name__ == "__main__":
    unittest.main()
