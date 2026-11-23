"""Read-only 68000/VDP trace checks for VA4 research.

Addresses in the existing captured trace are 68000 word addresses:
physical byte address = (word_address << 1) & 0xffffff.
This tool does not implement or validate a VA4 ASIC.
"""
from dataclasses import dataclass

VDP_WORD_BASE = 0x600000
VDP_WORD_MASK = 0x700000

@dataclass(frozen=True)
class BusObservation:
    word_address: int
    cpu_as: int
    cpu_rw: int
    board_dtack: int
    vdp_sel: int
    vdp_ack: int

def byte_address(word_address):
    if not 0 <= word_address <= 0x7fffff:
        raise ValueError("68000 word address out of range")
    return (word_address << 1) & 0xffffff

def is_vdp_window(word_address):
    return (word_address & VDP_WORD_MASK) == VDP_WORD_BASE

def classify(obs):
    """Classify *sampled levels*, not completed write transactions."""
    if not all(x in (0, 1) for x in (
        obs.cpu_as, obs.cpu_rw, obs.board_dtack, obs.vdp_sel, obs.vdp_ack
    )):
        raise ValueError("Signals must be binary")
    if not 0 <= obs.word_address <= 0x7fffff:
        raise ValueError("68000 word address out of range")
    if obs.cpu_as:
        return "idle-or-unsampled"
    if not is_vdp_window(obs.word_address):
        return "non-vdp"
    if obs.cpu_rw:
        return "vdp-read-sample"
    if not obs.vdp_sel:
        return "vdp-write-not-selected"
    if obs.board_dtack == 0 and obs.vdp_ack == 0:
        return "vdp-write-ack-levels-observed"
    return "vdp-write-wait-sample"
