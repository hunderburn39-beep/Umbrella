"""Deterministic CPU/VDP reference runner tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference
from cpu_vdp_runner import CPUVDPReferenceRunner
from vdp_ports import VDPPorts
from vdp_scanline_reference import VDPScanlineReference


def setup(program="4e72 2000 4e71 4e71"):
    rom = bytearray(0x140)
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[30 * 4:30 * 4 + 4] = (0x120).to_bytes(4, "big")
    rom[0x100:0x100 + len(bytes.fromhex(program))] = bytes.fromhex(program)
    rom[0x120:0x122] = bytes.fromhex("4e73")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    vdp = VDPPorts()
    return cpu, vdp


class RunnerTests(unittest.TestCase):
    def test_stop_blocks_instruction_budget_until_vblank(self):
        c, v = setup()
        v.registers[1] = 0x20
        r = CPUVDPReferenceRunner(c, v, instructions_per_line=2)
        first = r.tick_line()
        self.assertEqual([s.mnemonic for s in first.instructions], ["STOP"])
        self.assertTrue(first.stopped)
        for _ in range(223):
            self.assertFalse(r.tick_line().instructions)
        irq_line = r.tick_line()
        self.assertEqual(irq_line.line, 224)
        self.assertTrue(irq_line.irq_events[0].accepted)
        self.assertEqual([s.mnemonic for s in irq_line.instructions], ["RTE", "NOP"])
        self.assertEqual(c.pc, 0x106)
        self.assertEqual(c.a[7], 0xff0000)

    def test_zero_budget_advances_video_only(self):
        c, v = setup("4e71 4e71")
        r = CPUVDPReferenceRunner(c, v, instructions_per_line=0)
        self.assertFalse(r.tick_line().instructions)
        self.assertEqual(c.pc, 0x100)
        self.assertEqual(r.scheduler.line, 1)

    def test_budget_executes_exact_instruction_count(self):
        c, v = setup("4e71 4e71 4e71")
        r = CPUVDPReferenceRunner(c, v, instructions_per_line=2)
        self.assertEqual(len(r.tick_line().instructions), 2)
        self.assertEqual(c.pc, 0x104)

    def test_run_lines_count_and_frame_rollover(self):
        c, v = setup()
        r = CPUVDPReferenceRunner(c, v,
                                  scheduler=VDPScanlineReference(total_lines=225),
                                  instructions_per_line=0)
        self.assertEqual(len(r.run_lines(225)), 225)
        self.assertEqual((r.scheduler.frame, r.scheduler.line), (1, 0))

    def test_invalid_budgets_and_counts(self):
        c, v = setup()
        for budget in (-1, True, 10001):
            with self.assertRaises(ValueError):
                CPUVDPReferenceRunner(c, v, instructions_per_line=budget)
        r = CPUVDPReferenceRunner(c, v)
        for count in (-1, True, 100001):
            with self.assertRaises(ValueError):
                r.run_lines(count)


if __name__ == "__main__":
    unittest.main()
