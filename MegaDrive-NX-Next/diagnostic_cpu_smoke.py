"""Standalone smoke diagnostic for CPU -> bus -> VDP VRAM reference path.

Run: python MegaDrive-NX-Next/diagnostic_cpu_smoke.py
This is a synthetic test program, not a commercial ROM or timed ASIC.
"""
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

# MOVEA.L #$C00004,A0
# MOVE.W #$8F02,D0  ; auto-increment 2
# MOVE.W D0,(A0)
# MOVE.W #$4000,D0  ; VRAM write command first word
# MOVE.W D0,(A0)
# MOVE.W #$0000,D0  ; command second word
# MOVE.W D0,(A0)
# MOVEA.L #$C00000,A0
# MOVE.W #$1234,D0
# MOVE.W D0,(A0)
PROGRAM = bytes.fromhex(
    "207c 00c0 0004 "
    "303c 8f02 3080 "
    "303c 4000 3080 "
    "303c 0000 3080 "
    "207c 00c0 0000 "
    "303c 1234 3080"
)

def main():
    rom = bytearray(0x100 + len(PROGRAM))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = PROGRAM
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    cpu.vdp_ready = True  # Explicit synthetic readiness, NOT hardware timing.
    trace = cpu.run(10)
    word = cpu.bus.vdp.vram.read_word(0)
    assert word == 0x1234, f"VRAM expected 0x1234, got 0x{word:04x}"
    assert cpu.bus.vdp.registers[15] == 2
    reads, writes, vdp_reads, vdp_writes = cpu.bus.diagnostic_bus_counts()
    assert reads > 0 and writes == 4 and vdp_reads == 0 and vdp_writes == 4, (
        f"unexpected bus counts: {reads}, {writes}, {vdp_reads}, {vdp_writes}"
    )
    for item in trace:
        print(f"{item.pc_before:06X}: {item.opcode:04X} {item.mnemonic}")
    print(f"PASS: VRAM[0000]={word:04X}, VDP auto-increment={cpu.bus.vdp.registers[15]}")
    print(f"BUS: {reads} acknowledged reads, {writes} writes, {vdp_writes} VDP writes")

if __name__ == "__main__":
    main()
