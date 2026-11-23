"""Instruction-level 68000 cycle estimates for diagnostic scheduling only.

Values below are nominal 68000 baseline timings for the explicitly listed
register/immediate instructions, NOT measured VA2 timings. Memory waits,
prefetch, DMA, interrupts, VDP DTACK, and dynamic bus cycles are excluded.
Unknown instructions fail closed rather than silently receiving a cost.
"""
NOMINAL_CYCLES = {
    0x4e71: 4,  # NOP
    0x4e75: 16,  # RTS (nominal)
    0x4e73: 20,  # RTE (nominal)
    0x4e72: 4,  # STOP plus immediate fetch, simplified
}


def estimate_instruction_cycles(step):
    opcode = step.opcode
    if opcode in NOMINAL_CYCLES:
        return NOMINAL_CYCLES[opcode]
    if opcode & 0xf100 == 0x7000:
        return 4  # MOVEQ
    if opcode & 0xf0f8 == 0x50c8:
        raise NotImplementedError("DBcc timing depends on branch outcome")
    raise NotImplementedError(
        f"no validated diagnostic cycle estimate for 0x{opcode:04x}"
    )
