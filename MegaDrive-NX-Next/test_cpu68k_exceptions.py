"""68000 supervisor TRAP/RTE short-frame reference tests."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference


def cpu(program, handler="4e73", vector=32, target=0x120):
    rom = bytearray(0x140)
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[vector * 4:vector * 4 + 4] = target.to_bytes(4, "big")
    code = bytes.fromhex(program)
    rom[0x100:0x100 + len(code)] = code
    rom[0x120:0x120 + len(bytes.fromhex(handler))] = bytes.fromhex(handler)
    c = CPU68KReference(ReferenceBusController(bytes(rom)))
    c.reset()
    return c


class TrapRteTests(unittest.TestCase):
    def test_trap_zero_stacks_sr_and_pc(self):
        c = cpu("4e40 4e71")
        c.ccr = 0x04
        self.assertEqual(c.step().mnemonic, "TRAP")
        self.assertEqual(c.pc, 0x120)
        self.assertEqual(c.a[7], 0xfefffa)
        self.assertEqual(c.bus.memory.read_word(0xfefffa), 0x2704)
        self.assertEqual(c.bus.memory.read_word(0xfefffc), 0)
        self.assertEqual(c.bus.memory.read_word(0xfefffe), 0x102)
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_rte_restores_pc_sr_and_sp(self):
        c = cpu("4e40 4e71")
        c.ccr = 0x18
        c.step()
        self.assertEqual(c.step().mnemonic, "RTE")
        self.assertEqual(c.pc, 0x102)
        self.assertEqual(c.sr, 0x2718)
        self.assertEqual(c.a[7], 0xff0000)
        self.assertEqual(c.step().mnemonic, "NOP")

    def test_trap_three_uses_vector_35(self):
        c = cpu("4e43", vector=35)
        c.step()
        self.assertEqual(c.pc, 0x120)

    def test_odd_handler_rejected_without_stack_mutation(self):
        c = cpu("4e40", target=0x121)
        with self.assertRaises(ValueError):
            c.step()
        self.assertEqual(c.a[7], 0xff0000)
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_rte_rejects_user_mode_frame(self):
        c = cpu("4e73")
        c.a[7] = 0xff0020
        c.bus.memory.write_word(0xff0020, 0x0000)
        c.bus.memory.write_word(0xff0022, 0x0000)
        c.bus.memory.write_word(0xff0024, 0x0102)
        with self.assertRaises(NotImplementedError):
            c.step()
        self.assertEqual(c.a[7], 0xff0020)


if __name__ == "__main__":
    unittest.main()
