"""Scanline-granularity VDP IRQ scheduler for synthetic boot diagnostics.

Not a pixel clock, dot timing, horizontal counter, or VA2 ASIC model.
Each tick represents one externally advanced scanline boundary.
"""
from dataclasses import dataclass
from vdp_irq_bridge import deliver_vdp_event_reference

@dataclass(frozen=True)
class ScanlineTick:
    frame: int
    line: int
    events: tuple
    next_frame: int
    next_line: int


class VDPScanlineReference:
    def __init__(self, *, visible_lines=224, total_lines=262):
        if visible_lines not in (224, 240):
            raise ValueError("visible_lines must be 224 or 240")
        if not isinstance(total_lines, int) or total_lines <= visible_lines:
            raise ValueError("total_lines must exceed visible_lines")
        self.visible_lines = visible_lines
        self.total_lines = total_lines
        self.frame = 0
        self.line = 0
        self.h_counter = 0

    def tick(self, cpu, vdp) -> ScanlineTick:
        """Advance one synthetic scanline and inject eligible IRQ events.

        Register 0 bit 4 enables H interrupts, register 1 bit 5 enables
        V interrupts, register 10 is the H counter reload value. These
        are software reference conventions; edge timing is not modeled.
        """
        current_frame, current_line = self.frame, self.line
        events = []
        if current_line < self.visible_lines:
            if self.h_counter == 0:
                if vdp.registers[0] & 0x10:
                    events.append(deliver_vdp_event_reference(cpu, "hblank", enabled=True))
                self.h_counter = vdp.registers[10]
            else:
                self.h_counter -= 1
        elif current_line == self.visible_lines:
            if vdp.registers[1] & 0x20:
                events.append(deliver_vdp_event_reference(cpu, "vblank", enabled=True))
        self.line += 1
        if self.line >= self.total_lines:
            self.line = 0
            self.frame += 1
            self.h_counter = 0
        return ScanlineTick(current_frame, current_line, tuple(events), self.frame, self.line)
