"""68000 aligned 32-bit stack reads at the 24-bit bus boundary."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def make_cpu():
    rom = bytearray(0x102)
    rom[:4] = (0xff0100).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x102] = bytes.fromhex("4e71")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    return cpu

class StackBoundaryTests(unittest.TestCase):
    def test_last_aligned_longword_is_readable(self):
        cpu = make_cpu()
        cpu.bus.memory.write_word(0xfffffc, 0x1234)
        cpu.bus.memory.write_word(0xfffffe, 0xabcd)
        cpu.a[7] = 0xfffffc
        self.assertEqual(cpu.pop_long(), 0x1234abcd)
        self.assertEqual(cpu.a[7], 0x01000000)
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

    def test_last_word_is_not_a_complete_longword(self):
        cpu = make_cpu()
        cpu.a[7] = 0xfffffe
        with self.assertRaisesRegex(NotImplementedError, "outside reference bus"):
            cpu.pop_long()
        self.assertEqual(cpu.a[7], 0xfffffe)

    def test_odd_stack_rejected(self):
        cpu = make_cpu()
        cpu.a[7] = 0xfffffd
        with self.assertRaisesRegex(ValueError, "unaligned"):
            cpu.pop_long()

    def test_negative_stack_rejected_without_bus_access(self):
        cpu = make_cpu()
        cpu.a[7] = -4
        with self.assertRaisesRegex(NotImplementedError, "outside reference bus"):
            cpu.pop_long()
        self.assertIs(cpu.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
