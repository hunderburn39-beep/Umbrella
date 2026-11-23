"""68000 effective-address decoding for the reference CPU.

Resolves the standard 68000 addressing modes, fetching extension words and
applying (An)+ / -(An) side effects exactly once. The bus has 24 address
lines, so memory accesses use `address & 0xffffff`; the full 32-bit effective
address is still kept for LEA. Byte accesses use the bus byte lanes and so
work only on cartridge ROM and work RAM; peripheral byte lanes stay
unmodeled and raise NotImplementedError. Not cycle timing, not VA2 decoding.
"""
from dataclasses import dataclass

from cpu68k_alu import mask, sign_extend

# Addressing-mode keys, named as in the Motorola programmer's reference.
DN, AN = "Dn", "An"
IND, POST, PRE = "(An)", "(An)+", "-(An)"
D16, D8X = "d16(An)", "d8(An,Xn)"
ABSW, ABSL = "abs.w", "abs.l"
D16PC, D8PCX = "d16(PC)", "d8(PC,Xn)"
IMM = "#imm"

ALTERABLE_MEMORY = frozenset({IND, POST, PRE, D16, D8X, ABSW, ABSL})
DATA_ALTERABLE = ALTERABLE_MEMORY | {DN}
CONTROL = frozenset({IND, D16, D8X, ABSW, ABSL, D16PC, D8PCX})
DATA = DATA_ALTERABLE | {D16PC, D8PCX, IMM}
ALL = DATA | {AN}


def mode_key(mode: int, reg: int):
    """Map the 3-bit mode/register fields to a key, or None if reserved."""
    simple = {0: DN, 1: AN, 2: IND, 3: POST, 4: PRE, 5: D16, 6: D8X}
    if mode in simple:
        return simple[mode]
    if mode == 7:
        return {0: ABSW, 1: ABSL, 2: D16PC, 3: D8PCX, 4: IMM}.get(reg)
    return None


@dataclass
class Operand:
    kind: str          # "dreg", "areg", "mem" or "imm"
    bits: int
    reg: int = 0
    address: int = 0   # full 32-bit effective address for "mem"
    value: int = 0     # immediate value for "imm"


def _index_value(cpu, extension: int) -> int:
    """Brief-format index register contribution; 68020 formats unsupported."""
    if extension & 0x0100 or extension & 0x0600:
        raise NotImplementedError("68020 full-format or scaled index not modeled")
    register = (extension >> 12) & 7
    source = cpu.a[register] if extension & 0x8000 else cpu.d[register]
    return sign_extend(source, 32 if extension & 0x0800 else 16)


def resolve(cpu, mode: int, reg: int, bits: int, allowed) -> Operand:
    """Decode an operand, fetch its extension words and apply side effects.

    The addressing mode is validated against `allowed` before anything is
    fetched or modified, so a rejected encoding has no side effects.
    """
    key = mode_key(mode, reg)
    if key is None or key not in allowed:
        raise NotImplementedError(f"addressing mode {mode}/{reg} not valid here")
    if key == AN and bits == 8:
        raise NotImplementedError("byte access to an address register is illegal")
    if key == DN:
        return Operand("dreg", bits, reg=reg)
    if key == AN:
        return Operand("areg", bits, reg=reg)
    if key == IMM:
        if bits == 32:
            value = (cpu.fetch_word() << 16) | cpu.fetch_word()
        else:
            value = cpu.fetch_word() & mask(bits)
        return Operand("imm", bits, value=value)
    step = 2 if (bits == 8 and reg == 7) else bits // 8  # A7 stays word aligned
    if key == IND:
        address = cpu.a[reg]
    elif key == POST:
        address = cpu.a[reg]
        cpu.a[reg] = (address + step) & 0xffffffff
    elif key == PRE:
        address = (cpu.a[reg] - step) & 0xffffffff
        cpu.a[reg] = address
    elif key == D16:
        address = cpu.a[reg] + sign_extend(cpu.fetch_word(), 16)
    elif key == D8X:
        extension = cpu.fetch_word()
        address = cpu.a[reg] + sign_extend(extension, 8) + _index_value(cpu, extension)
    elif key == ABSW:
        address = sign_extend(cpu.fetch_word(), 16)
    elif key == ABSL:
        address = (cpu.fetch_word() << 16) | cpu.fetch_word()
    elif key == D16PC:
        base = cpu.pc  # address of the extension word
        address = base + sign_extend(cpu.fetch_word(), 16)
    else:  # D8PCX
        base = cpu.pc
        extension = cpu.fetch_word()
        address = base + sign_extend(extension, 8) + _index_value(cpu, extension)
    return Operand("mem", bits, reg=reg, address=address & 0xffffffff)


def read(cpu, operand: Operand) -> int:
    """Read the operand value masked to its size."""
    bits = operand.bits
    if operand.kind == "dreg":
        return cpu.d[operand.reg] & mask(bits)
    if operand.kind == "areg":
        return cpu.a[operand.reg] & mask(bits)
    if operand.kind == "imm":
        return operand.value
    address = operand.address & 0xffffff
    if bits == 8:
        return cpu.read_byte(address)
    if bits == 16:
        return cpu.read_word(address)
    return cpu.read_long(address)


def write(cpu, operand: Operand, value: int):
    """Write a data-register or memory operand; upper Dn bits are preserved."""
    bits = operand.bits
    value &= mask(bits)
    if operand.kind == "dreg":
        keep = ~mask(bits) & 0xffffffff
        cpu.d[operand.reg] = (cpu.d[operand.reg] & keep) | value
    elif operand.kind == "mem":
        address = operand.address & 0xffffff
        if bits == 8:
            cpu.write_byte(address, value)
        elif bits == 16:
            cpu.write_word(address, value)
        else:
            cpu.write_long(address, value)
    else:
        raise ValueError("operand is not writable here")
