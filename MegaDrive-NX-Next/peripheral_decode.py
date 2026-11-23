"""Reference 68000 peripheral address decoder for Genesis 3 VA2 research.

The address windows are conventional Mega Drive software-visible regions.
This is NOT verified VA2 ASIC pin decoding or timing. Decode alone never
generates DTACK or a peripheral response.
"""
from dataclasses import dataclass
from enum import Enum

class Device(Enum):
    CARTRIDGE = "cartridge"
    Z80 = "z80"
    IO = "io"
    VDP = "vdp"
    RAM = "ram"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class Selection:
    device: Device
    address: int
    offset: int
    upper: bool
    lower: bool

def select(address: int, *, upper: bool = True, lower: bool = True) -> Selection:
    if not isinstance(address, int) or not 0 <= address <= 0xffffff:
        raise ValueError("24-bit address required")
    if not upper and not lower:
        raise ValueError("no byte lane selected")
    if address & 1 and upper:
        raise ValueError("upper byte lane cannot start at odd address")
    if address <= 0x3fffff:
        device, offset = Device.CARTRIDGE, address
    elif 0xa00000 <= address <= 0xa0ffff:
        device, offset = Device.Z80, address - 0xa00000
    elif 0xa10000 <= address <= 0xa1ffff:
        device, offset = Device.IO, address - 0xa10000
    elif 0xc00000 <= address <= 0xdfffff:
        device, offset = Device.VDP, address & 0x1fffff
    elif 0xe00000 <= address <= 0xffffff:
        device, offset = Device.RAM, address & 0xffff
    else:
        device, offset = Device.UNKNOWN, address
    return Selection(device, address, offset, upper, lower)

def io_register_name(address: int) -> str | None:
    """Identify common 68000 IO addresses, without inventing register behavior."""
    names = {
        0xa10000: "VERSION",
        0xa10002: "PORT_A_DATA",
        0xa10004: "PORT_B_DATA",
        0xa10006: "PORT_C_DATA",
        0xa10008: "PORT_A_CTRL",
        0xa1000a: "PORT_B_CTRL",
        0xa1000c: "PORT_C_CTRL",
        0xa11100: "Z80_BUSREQ",
        0xa11200: "Z80_RESET",
    }
    if not isinstance(address, int) or address & 1:
        return None
    return names.get(address)
