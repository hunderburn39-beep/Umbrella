import unittest
from cpu68k_reference import CPU68KReference
from bus_controller import ReferenceBusController
from bus_cycle import Phase

def cpu(hexcode):
    data = bytes.fromhex(hexcode)
    rom = bytearray(0x100 + len(data))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = data
    result = CPU68KReference(ReferenceBusController(bytes(rom)))
    result.reset()
    return result

class SubroutineTests(unittest.TestCase):
    def test_absolute_jsr_pushes_return_address(self):
        c = cpu("4eb9 0000 010a 4e71 4e71 4e75")
        self.assertEqual(c.step().mnemonic, "JSR")
        self.assertEqual(c.pc, 0x10a)
        self.assertEqual(c.a[7], 0xfefffc)
        self.assertEqual(c.bus.memory.read_word(0xfefffc), 0)
        self.assertEqual(c.bus.memory.read_word(0xfefffe), 0x106)

    def test_rts_restores_pc_and_sp(self):
        c = cpu("4eb9 0000 010a 4e71 4e71 4e75")
        c.step()
        self.assertEqual(c.step().mnemonic, "RTS")
        self.assertEqual(c.pc, 0x106)
        self.assertEqual(c.a[7], 0xff0000)
        self.assertEqual(c.step().mnemonic, "NOP")

    def test_indirect_jsr(self):
        c = cpu("207c 0000 010e 4e90 4e71 4e71 4e71 4e75")
        c.step()
        self.assertEqual(c.step().mnemonic, "JSR")
        self.assertEqual(c.pc, 0x10e)

    def test_nested_calls(self):
        c = cpu("4eb9 0000 010c 4e71 4e71 4e71 4eb9 0000 0116 4e75 4e71 4e75")
        c.step()
        self.assertEqual(c.a[7], 0xfefffc)
        c.step()
        self.assertEqual(c.a[7], 0xfefff8)
        c.step()
        self.assertEqual(c.a[7], 0xfefffc)
        c.step()
        self.assertEqual(c.a[7], 0xff0000)
        self.assertEqual(c.pc, 0x106)

    def test_odd_jsr_target_does_not_push(self):
        c = cpu("4eb9 0000 0101")
        with self.assertRaises(ValueError):
            c.step()
        self.assertEqual(c.a[7], 0xff0000)

    def test_odd_stack_pointer_rejected(self):
        c = cpu("4eb9 0000 0108")
        c.a[7] = 0xff0001
        with self.assertRaises(ValueError):
            c.step()

    def test_stack_underflow_not_fabricated(self):
        c = cpu("4e75")
        with self.assertRaises(NotImplementedError):
            c.step()
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
