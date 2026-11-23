"""68000 branch displacement base regression checks.

For 68000 Bcc/BSR, both byte and word displacements are relative
to the PC immediately after the opcode (the extension-word address).
"""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

def cpu_for(words):
    program = bytes.fromhex(words)
    rom = bytearray(0x100 + len(program))
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = program
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class BranchBaseTests(unittest.TestCase):
    def test_bra_word_relative_to_extension_address(self):
        cpu = cpu_for("6000 0006 7001 4e71 7207")
        cpu.step()
        self.assertEqual(cpu.pc, 0x108)
        cpu.step()
        self.assertEqual(cpu.d[1], 7)
        self.assertEqual(cpu.d[0], 0)

    def test_bra_short_relative_to_opcode_plus_two(self):
        cpu = cpu_for("6004 7001 4e71 7207")
        cpu.step()
        self.assertEqual(cpu.pc, 0x106)
        cpu.step()
        self.assertEqual(cpu.d[1], 7)

    def test_bsr_word_pushes_post_extension_return_pc(self):
        cpu = cpu_for("6100 0006 7001 4e71 4e75")
        cpu.step()
        self.assertEqual(cpu.pc, 0x108)
        self.assertEqual(cpu.a[7], 0xff00fc)
        self.assertEqual(cpu.bus.memory.read_word(0xff00fc), 0)
        self.assertEqual(cpu.bus.memory.read_word(0xff00fe), 0x104)
        cpu.step()
        self.assertEqual(cpu.pc, 0x104)

    def test_beq_word_not_taken_still_consumes_extension(self):
        cpu = cpu_for("7001 6700 0006 7207")
        cpu.step()
        cpu.step()
        self.assertEqual(cpu.pc, 0x106)
        cpu.step()
        self.assertEqual(cpu.d[1], 7)

if __name__ == "__main__":
    unittest.main()
