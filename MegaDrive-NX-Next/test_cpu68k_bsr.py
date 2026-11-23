"""BSR.s / BSR.w relative call and RTS regression tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference
from bus_cycle import Phase

def cpu(program):
    code = bytes.fromhex(program)
    rom = bytearray(0x100 + len(code))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = code
    result = CPU68KReference(ReferenceBusController(bytes(rom)))
    result.reset()
    return result

class BSRTests(unittest.TestCase):
    def test_short_call_and_return(self):
        c = cpu("6102 4e71 4e75")
        c.step()
        self.assertEqual(c.pc, 0x104)
        self.assertEqual(c.a[7], 0xfefffc)
        c.step()
        self.assertEqual(c.pc, 0x102)
        self.assertEqual(c.a[7], 0xff0000)

    def test_word_call_and_return(self):
        c = cpu("6100 0002 4e71 4e75")
        c.step()
        self.assertEqual(c.pc, 0x106)
        self.assertEqual(c.bus.memory.read_word(0xfefffe), 0x104)
        c.step()
        self.assertEqual(c.pc, 0x104)

    def test_negative_word_displacement(self):
        c = cpu("4e71 6100 fffc")
        c.step()
        c.step()
        self.assertEqual(c.pc, 0x100)
        self.assertEqual(c.a[7], 0xfefffc)

    def test_bsr_preserves_ccr(self):
        c = cpu("6102 4e71 4e75")
        c.ccr = 0x1f
        c.step()
        self.assertEqual(c.ccr, 0x1f)

    def test_odd_target_does_not_push(self):
        c = cpu("6101")
        with self.assertRaises(ValueError):
            c.step()
        self.assertEqual(c.a[7], 0xff0000)
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_stack_alignment_rejected(self):
        c = cpu("6102 4e71 4e75")
        c.a[7] = 0xff0001
        with self.assertRaises(ValueError):
            c.step()
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
