"""Reference Z80 bus request and reset control state machine.

Software-visible register conventions only. This is not measured Genesis 3
VA2 arbitration timing or a Z80/315-6123 execution model.
"""
from dataclasses import dataclass

BUSREQ_ADDR = 0xA11100
RESET_ADDR = 0xA11200

@dataclass
class Z80Control:
    bus_requested: bool = False
    bus_granted: bool = False
    reset_asserted: bool = True

    def write_word(self, address: int, value: int) -> None:
        if address not in (BUSREQ_ADDR, RESET_ADDR):
            raise ValueError("not a Z80 control register")
        if not 0 <= value <= 0xffff:
            raise ValueError("word outside 16-bit range")
        # The high data byte is relevant for the conventional word writes.
        asserted = bool(value & 0x0100)
        if address == BUSREQ_ADDR:
            self.bus_requested = asserted
            if not asserted:
                self.bus_granted = False
        else:
            # RESET register bit 8 high releases reset, low asserts it.
            self.reset_asserted = not asserted
            if self.reset_asserted:
                self.bus_granted = False

    def sample_bus_grant(self, granted: bool) -> None:
        """External observation only: never manufacture bus ownership."""
        if granted and (not self.bus_requested or self.reset_asserted):
            raise ValueError("grant inconsistent with requested active Z80 bus")
        self.bus_granted = bool(granted)

    def read_busreq_status(self) -> int:
        """Reference bit-8 busy convention: 0 when 68k bus grant observed."""
        return 0x0000 if self.bus_granted else 0x0100

    def can_68k_access_z80_ram(self) -> bool:
        return self.bus_granted or self.reset_asserted
