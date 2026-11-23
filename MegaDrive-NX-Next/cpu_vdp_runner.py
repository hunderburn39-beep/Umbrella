"""Deterministic instruction-budget CPU/VDP runner for reference diagnostics.

No 68000 cycle accounting is inferred: each scanline receives a caller-
provided instruction budget. STOP consumes no instructions until a scanline
IRQ is accepted. This is a scheduling harness, not a hardware clock.
"""
from dataclasses import dataclass
from vdp_scanline_reference import VDPScanlineReference


@dataclass(frozen=True)
class ScheduledLine:
    frame: int
    line: int
    irq_events: tuple
    instructions: tuple
    stopped: bool


class CPUVDPReferenceRunner:
    def __init__(self, cpu, vdp, *, scheduler=None, instructions_per_line=1):
        if isinstance(instructions_per_line, bool) or not isinstance(instructions_per_line, int) or not 0 <= instructions_per_line <= 10000:
            raise ValueError("instructions_per_line must be 0..10000")
        self.cpu = cpu
        self.vdp = vdp
        self.scheduler = scheduler if scheduler is not None else VDPScanlineReference()
        self.instructions_per_line = instructions_per_line

    def tick_line(self) -> ScheduledLine:
        """Service synthetic line events, then run up to the instruction budget."""
        tick = self.scheduler.tick(self.cpu, self.vdp)
        executed = []
        for _ in range(self.instructions_per_line):
            if self.cpu.stopped:
                break
            executed.append(self.cpu.step())
        return ScheduledLine(tick.frame, tick.line, tick.events,
                             tuple(executed), self.cpu.stopped)

    def run_lines(self, count: int) -> tuple:
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 100000:
            raise ValueError("count must be 0..100000")
        return tuple(self.tick_line() for _ in range(count))
