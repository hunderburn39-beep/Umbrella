"""Nominal-cycle CPU/VDP scheduler for synthetic reference tests.

One scanline adds a fixed, caller-chosen cycle budget. Unused credits carry
forward only while the CPU is running. STOP discards credits; IRQ exception
entry is not charged, and physical VDP/CPU timing is not represented.
"""
from dataclasses import dataclass
from cpu68k_cycle_estimates import estimate_instruction_cycles
from vdp_scanline_reference import VDPScanlineReference


@dataclass(frozen=True)
class CycleScheduledLine:
    frame: int
    line: int
    irq_events: tuple
    instructions: tuple
    charged_cycles: int
    remaining_credit: int
    stopped: bool


class CPUVDPCycleReferenceRunner:
    def __init__(self, cpu, vdp, *, scheduler=None, cycles_per_line=8):
        if (type(cycles_per_line) is not int or
                not 1 <= cycles_per_line <= 100000):
            raise ValueError("cycles_per_line must be 1..100000")
        self.cpu = cpu
        self.vdp = vdp
        self.scheduler = scheduler if scheduler is not None else VDPScanlineReference()
        self.cycles_per_line = cycles_per_line
        self.credit = 0

    def tick_line(self) -> CycleScheduledLine:
        tick = self.scheduler.tick(self.cpu, self.vdp)
        self.credit = self.credit + self.cycles_per_line if not self.cpu.stopped else 0
        if self.cpu.stopped:
            self.credit = 0
        executed = []
        charged = 0
        while not self.cpu.stopped and self.credit >= 4:
            # Diagnostic peek bypasses the transaction controller so it does
            # not fabricate an extra CPU bus transfer or affect ACK counters.
            # Instruction fetch itself still uses the bus in cpu.step().
            opcode = self.cpu.bus.memory.read_word(self.cpu.pc & 0xffffff)
            cost = estimate_instruction_cycles(type("Opcode", (), {"opcode": opcode})())
            if cost > self.credit:
                break
            result = self.cpu.step()
            executed.append(result)
            self.credit -= cost
            charged += cost
        if self.cpu.stopped:
            self.credit = 0
        return CycleScheduledLine(tick.frame, tick.line, tick.events,
                                  tuple(executed), charged, self.credit,
                                  self.cpu.stopped)

    def run_lines(self, count):
        if type(count) is not int or not 0 <= count <= 100000:
            raise ValueError("count must be 0..100000")
        return tuple(self.tick_line() for _ in range(count))
