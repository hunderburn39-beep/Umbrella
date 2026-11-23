"""Genesis 3 VA2 hardware identity and safe address probes.

Reference-only metadata. This is NOT an ASIC 315-6123 implementation.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Board:
    model: str = "Sega Genesis 3"
    revision: str = "VA2"
    main_asic: str = "315-6123"
    asic_family: str = "Yamaha FQ8007"
    implementation_verified: bool = False

def cpu_word_to_byte(word_address: int) -> int:
    """23-bit 68000 word bus to 24-bit byte address."""
    if not 0 <= word_address <= 0x7fffff:
        raise ValueError("word address outside 68000 address bus")
    return word_address << 1

def cpu_vdp_address(word_address: int) -> bool:
    """Candidate standard Mega Drive VDP aperture; not VA2 timing proof."""
    return (cpu_word_to_byte(word_address) & 0xe00000) == 0xc00000

def require_verified_core(board: Board) -> None:
    if not board.implementation_verified:
        raise RuntimeError("315-6123 core not implemented or verified")
