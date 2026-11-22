"""Offline validation of VDP write acknowledgements and pixel-clock progress.

Samples are observations, not a substitute for the real Nuked-MD chip equations.
A write is counted only on a transition from an unacknowledged bus request to
an acknowledged request; a held DTACK must not be counted repeatedly.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    cycle: int
    cpu_as_n: int
    cpu_rw: int
    cpu_addr_word: int
    cpu_uds_n: int
    cpu_lds_n: int
    board_dtack_n: int
    vdp_sel: int
    vdp_as_n: int
    vdp_uds_n: int
    vdp_lds_n: int
    vdp_ready_n: int
    pixel_clock: int
    pixel_valid: int


def analyze(samples):
    counts = dict(requests=0, selected=0, acknowledged=0,
                  complete=0, missing_select=0, missing_ack=0,
                  pixel_edges=0, valid_pixels=0)
    prev_request = False
    prev_ack = False
    prev_pixel_clock = None
    last_cycle = -1
    for s in samples:
        if s.cycle <= last_cycle:
            raise ValueError("Samples must be in strictly increasing cycle order")
        last_cycle = s.cycle
        for name in ("cpu_as_n", "cpu_rw", "cpu_uds_n", "cpu_lds_n",
                     "board_dtack_n", "vdp_sel", "vdp_as_n",
                     "vdp_uds_n", "vdp_lds_n", "vdp_ready_n",
                     "pixel_clock", "pixel_valid"):
            if getattr(s, name) not in (0, 1):
                raise ValueError(name + " must be binary")
        request = (s.cpu_as_n == 0 and s.cpu_rw == 0
                   and (s.cpu_uds_n == 0 or s.cpu_lds_n == 0)
                   and (s.cpu_addr_word & 0x700000) == 0x600000)
        selected = s.vdp_sel == 1 and s.vdp_as_n == 0
        strobed = selected and (s.vdp_uds_n == 0 or s.vdp_lds_n == 0)
        ack = request and s.board_dtack_n == 0
        if request and not prev_request:
            counts["requests"] += 1
            if not selected:
                counts["missing_select"] += 1
        if request and selected:
            counts["selected"] += 1
        if ack and not prev_ack:
            counts["acknowledged"] += 1
            if strobed and s.vdp_ready_n == 0:
                counts["complete"] += 1
        if request and not ack:
            counts["missing_ack"] += 1  # clock samples, not transactions
        if prev_pixel_clock is not None and s.pixel_clock != prev_pixel_clock:
            counts["pixel_edges"] += 1
        counts["valid_pixels"] += s.pixel_valid
        prev_request, prev_ack, prev_pixel_clock = request, ack, s.pixel_clock
    return counts
