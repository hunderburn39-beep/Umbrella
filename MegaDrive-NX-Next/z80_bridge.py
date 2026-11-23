"""Reference integration of Z80 control and RAM into 68000-side transactions.

Byte accesses only; VA2 chip timing and physical lane behavior are unknown.
"""
from dataclasses import dataclass, field
from z80_control import Z80Control, BUSREQ_ADDR, RESET_ADDR
from z80_ram import Z80RAM

@dataclass
class Z80Bridge:
    control: Z80Control = field(default_factory=Z80Control)
    ram: Z80RAM = field(init=False)

    def __post_init__(self):
        self.ram = Z80RAM(self.control)

    def write_control_word(self, address: int, value: int):
        if address not in (BUSREQ_ADDR, RESET_ADDR):
            raise ValueError("unknown Z80 control address")
        self.control.write_word(address, value)

    def observe_grant(self, granted: bool):
        self.control.sample_bus_grant(granted)

    def read_byte(self, address: int) -> int:
        return self.ram.read_byte(address)

    def write_byte(self, address: int, value: int):
        self.ram.write_byte(address, value)

    def status_word(self) -> int:
        return self.control.read_busreq_status()
