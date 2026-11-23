"""End-to-end synthetic CPU/VDP scanline IRQ smoke diagnostic.

No cartridge ROM is required. The reference CPU executes STOP, a synthetic
VDP scanline scheduler asserts VBlank, the CPU enters vector 30, executes
RTE, and resumes. This does not simulate physical VDP clocks or bus timing.
"""
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference
from vdp_ports import VDPPorts
from vdp_scanline_reference import VDPScanlineReference


def main():
    rom = bytearray(0x140)
    rom[0:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[30 * 4:30 * 4 + 4] = (0x120).to_bytes(4, "big")
    rom[0x100:0x106] = bytes.fromhex("4e72 2000 4e71")
    rom[0x120:0x122] = bytes.fromhex("4e73")
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    vdp = VDPPorts()
    vdp.registers[1] = 0x20
    scheduler = VDPScanlineReference(visible_lines=224, total_lines=262)
    assert cpu.step().mnemonic == "STOP"
    assert cpu.stopped and cpu.pc == 0x104
    for _ in range(224):
        tick = scheduler.tick(cpu, vdp)
        assert not tick.events
        assert cpu.stopped
    tick = scheduler.tick(cpu, vdp)
    assert tick.line == 224 and len(tick.events) == 1
    assert tick.events[0].level == 6 and tick.events[0].accepted
    assert cpu.pc == 0x120 and not cpu.stopped and cpu.sr == 0x2600
    assert cpu.step().mnemonic == "RTE"
    assert cpu.pc == 0x104 and cpu.sr == 0x2000
    assert cpu.step().mnemonic == "NOP"
    assert cpu.pc == 0x106 and cpu.a[7] == 0xff0000
    print("PASS: STOP -> VBlank line 224 -> IRQ6 vector 30 -> RTE -> NOP")


if __name__ == "__main__":
    main()
