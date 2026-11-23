"""Untimed diagnostic bridge from explicit VDP events to 68000 IRQ levels.

This is not a VDP clock or an IRQ generator. The caller must supply a
validated event and explicitly request delivery. Level mappings are
reference conventions, not measured Genesis 3 VA2 pin timing.
"""
from dataclasses import dataclass
from cpu68k_reference import CPU68KReference

HBLANK = "hblank"
VBLANK = "vblank"
VDP_IRQ_LEVELS = {HBLANK: 4, VBLANK: 6}


@dataclass(frozen=True)
class DiagnosticIRQDelivery:
    event: str
    level: int
    enabled: bool
    accepted: bool


def deliver_vdp_event_reference(cpu: CPU68KReference, event: str,
                                *, enabled: bool) -> DiagnosticIRQDelivery:
    """Inject one explicitly asserted, externally qualified VDP IRQ event.

    The enabled flag is provided by the caller, not inferred from timing,
    VDP registers, FIFO, or scanline diagnostics. Masked events are not queued.
    """
    if event not in VDP_IRQ_LEVELS:
        raise ValueError("event must be 'hblank' or 'vblank'")
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be boolean")
    level = VDP_IRQ_LEVELS[event]
    accepted = cpu.service_autovector_irq_reference(level) if enabled else False
    return DiagnosticIRQDelivery(event, level, enabled, accepted)
