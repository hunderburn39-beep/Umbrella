"""Shared helpers for 68000 reference CPU tests. Not itself a test module.

Programs are placed at ROM 0x100. Work RAM lives at 0xFF0000 and is a 64 KiB
mirror, so RAM address A maps to bytearray offset A & 0xFFFF.
"""
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

ROM_DATA = 0x200  # conventional location for read-only test tables


def make_cpu(*words, d=None, a=None, ccr=0, rom_data=None, ram=None):
    """Reset CPU with `words` at 0x100; d/a map register index to value."""
    rom = bytearray(0x400)
    rom[0:4] = (0xff8000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    for index, word in enumerate(words):
        rom[0x100 + 2 * index:0x102 + 2 * index] = word.to_bytes(2, "big")
    for address, data in (rom_data or {}).items():
        rom[address:address + len(data)] = data
    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
    cpu.reset()
    for index, value in (d or {}).items():
        cpu.d[index] = value
    for index, value in (a or {}).items():
        cpu.a[index] = value
    cpu.ccr = ccr
    for address, data in (ram or {}).items():
        offset = address & 0xffff
        cpu.bus.memory.ram[offset:offset + len(data)] = data
    return cpu


def ram_bytes(cpu, address, length):
    offset = address & 0xffff
    return bytes(cpu.bus.memory.ram[offset:offset + length])


def ram_word(cpu, address):
    return int.from_bytes(ram_bytes(cpu, address, 2), "big")


def ram_long(cpu, address):
    return int.from_bytes(ram_bytes(cpu, address, 4), "big")


def state(cpu):
    """Registers, CCR and PC; used to prove failed instructions change nothing."""
    return (tuple(cpu.d), tuple(cpu.a), cpu.ccr, cpu.pc)


def bus_idle(cpu):
    return cpu.bus.cycle.phase is Phase.IDLE
