"""Nominal-cycle scanline runner regression tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference
from cpu_vdp_cycle_runner import CPUVDPCycleReferenceRunner
from vdp_ports import VDPPorts


def setup(program):
    rom = bytearray(0x140)
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x100 + len(bytes.fromhex(program))] = bytes.fromhex(program)
    c = CPU68KReference(ReferenceBusController(bytes(rom)))
    c.reset()
    return c, VDPPorts()


class CycleRunnerTests(unittest.TestCase):
    def test_four_cycles_execute_one_nop(self):
        c, v = setup("4e71 4e71 4e71")
        r = CPUVDPCycleReferenceRunner(c, v, cycles_per_line=4)
        tick = r.tick_line()
        self.assertEqual([s.mnemonic for s in tick.instructions], ["NOP"])
        self.assertEqual(tick.charged_cycles, 4)
        self.assertEqual(c.pc, 0x102)

    def test_credit_carries_until_instruction_affordable(self):
        c, v = setup("4e75")
        c.a[7] = 0xff0010
        c.bus.memory.write_word(0xff0010, 0)
        c.bus.memory.write_word(0xff0012, 0x100)
        r = CPUVDPCycleReferenceRunner(c, v, cycles_per_line=4)
        for _ in range(3):
            self.assertFalse(r.tick_line().instructions)
        self.assertEqual(c.pc, 0x100)
        self.assertEqual(r.credit, 12)
        self.assertEqual(r.tick_line().instructions[0].mnemonic, "RTS")
        self.assertEqual(c.pc, 0x100)

    def test_stop_discards_credit(self):
        c, v = setup("4e72 2000 4e71")
        r = CPUVDPCycleReferenceRunner(c, v, cycles_per_line=12)
        tick = r.tick_line()
        self.assertEqual([s.mnemonic for s in tick.instructions], ["STOP"])
        self.assertTrue(tick.stopped)
        self.assertEqual(tick.remaining_credit, 0)
        self.assertFalse(r.tick_line().instructions)

    def test_unknown_opcode_does_not_advance_pc(self):
        c, v = setup("3080")
        r = CPUVDPCycleReferenceRunner(c, v, cycles_per_line=8)
        with self.assertRaises(NotImplementedError):
            r.tick_line()
        self.assertEqual(c.pc, 0x100)

    def test_invalid_cycle_budgets(self):
        c, v = setup("4e71")
        for n in (0, -1, True, 100001):
            with self.assertRaises(ValueError):
                CPUVDPCycleReferenceRunner(c, v, cycles_per_line=n)


if __name__ == "__main__":
    unittest.main()
