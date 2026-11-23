"""68000 bus-cycle handshake reference for Genesis 3 VA2 research.

A transaction completes only after an explicit active-low DTACK sample.
No VDP timing, ASIC gates, or automatic acknowledgements are fabricated.
"""
from dataclasses import dataclass
from enum import Enum

class Phase(Enum):
    IDLE = "idle"
    WAIT = "wait-for-dtack"
    ACKNOWLEDGED = "acknowledged"

@dataclass(frozen=True)
class Request:
    address: int
    read: bool
    data: int = 0
    upper: bool = True
    lower: bool = True

    def __post_init__(self):
        if not 0 <= self.address <= 0xffffff:
            raise ValueError("address outside 24-bit bus")
        if not 0 <= self.data <= 0xffff:
            raise ValueError("data outside 16-bit bus")
        if not (self.upper or self.lower):
            raise ValueError("at least one byte lane must be selected")
        if self.address & 1 and self.upper:
            raise ValueError("odd address cannot select upper byte lane")

class BusCycle:
    def __init__(self):
        self.phase = Phase.IDLE
        self.request = None
        self.samples = 0

    def start(self, request: Request):
        if self.phase is not Phase.IDLE:
            raise RuntimeError("previous bus cycle not released")
        self.request = request
        self.samples = 0
        self.phase = Phase.WAIT

    def sample(self, *, as_n: int, dtack_n: int, vdp_selected: int = 0):
        if any(x not in (0, 1) for x in (as_n, dtack_n, vdp_selected)):
            raise ValueError("signals must be binary")
        if self.phase is Phase.IDLE:
            raise RuntimeError("no active bus cycle")
        if as_n:
            raise RuntimeError("address strobe inactive during cycle")
        self.samples += 1
        if self.phase is Phase.ACKNOWLEDGED:
            return False
        if dtack_n == 0:
            self.phase = Phase.ACKNOWLEDGED
            return True
        return False

    def release(self):
        if self.phase is Phase.IDLE:
            raise RuntimeError("no bus cycle to release")
        was_acknowledged = self.phase is Phase.ACKNOWLEDGED
        self.phase = Phase.IDLE
        self.request = None
        return was_acknowledged
