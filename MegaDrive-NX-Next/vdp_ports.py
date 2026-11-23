"""Software-visible VDP port command staging reference.

Models 16-bit control-port command assembly and register-write command
recognition only. Does not implement VA2 VDP execution, FIFO, DMA, DTACK,
video output, or command-to-VRAM transfers.
"""
from dataclasses import dataclass, field
from vram import VRAM

CONTROL_PORT = 0xC00004
DATA_PORT = 0xC00000

@dataclass
class VDPPorts:
    registers: list[int] = field(default_factory=lambda: [0] * 24)
    vram: VRAM = field(default_factory=VRAM)
    pending_command: int | None = None
    last_command: int | None = None

    def write_control(self, value: int) -> str:
        if not 0 <= value <= 0xffff:
            raise ValueError("VDP control word must be 16-bit")
        if self.pending_command is not None:
            self.last_command = (self.pending_command << 16) | value
            self.pending_command = None
            return "command-staged"
        if (value & 0xC000) == 0x8000:
            index = (value >> 8) & 0x1f
            if index >= len(self.registers):
                raise NotImplementedError("VDP register index outside modeled range")
            self.registers[index] = value & 0xff
            return "register-write"
        self.pending_command = value
        return "command-pending"

    def write_data(self, value: int) -> None:
        if not 0 <= value <= 0xffff:
            raise ValueError("VDP data word must be 16-bit")
        raise NotImplementedError("VDP data port, VRAM and FIFO not implemented")

    def read_status(self) -> int:
        raise NotImplementedError("VDP status requires timing and FIFO model")

    def reset(self) -> None:
        self.registers[:] = [0] * len(self.registers)
        self.pending_command = None
        self.last_command = None

    def diagnostic_vram_read(self, address: int) -> int:
        """Direct VRAM inspection, intentionally bypassing the VDP data port."""
        return self.vram.read_word(address)

    def diagnostic_vram_write(self, address: int, value: int) -> None:
        """Direct VRAM test injection, not a VDP FIFO or CPU bus write."""
        self.vram.write_word(address, value)
