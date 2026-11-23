"""68000 arithmetic, logic, compare, shift, LEA and TST instruction groups.

`execute(cpu, opcode)` returns the instruction mnemonic, or None when the
opcode is outside these groups. Encodings that are recognized but not modeled
(ADDX/SUBX, ABCD/SBCD, EXG, CMPM, MULU/MULS/DIVU/DIVS, bit-field forms) raise
NotImplementedError rather than executing incorrectly. Illegal encodings are
not distinguished from unmodeled ones: no illegal-instruction exception is
modeled. Instruction-level reference only, not cycle timing.
"""
import cpu68k_alu as alu
import cpu68k_ea as ea

SIZE_NAMES = ("B", "W", "L")
SHIFT_KINDS = ("AS", "LS", "ROX", "RO")


def _fields(opcode):
    return (opcode >> 9) & 7, (opcode >> 6) & 7, (opcode >> 3) & 7, opcode & 7


def _dreg(bits, reg):
    return ea.Operand("dreg", bits, reg=reg)


def _group4(cpu, opcode):
    _, _, mode, reg = _fields(opcode)
    if opcode & 0xf1c0 == 0x41c0:
        address_register = (opcode >> 9) & 7
        operand = ea.resolve(cpu, mode, reg, 32, ea.CONTROL)
        cpu.a[address_register] = operand.address  # EA only; no memory access
        return "LEA <ea>,An"
    if opcode & 0xff00 == 0x4a00 and (opcode >> 6) & 3 != 3:
        size = (opcode >> 6) & 3
        bits = alu.SIZE_BITS[size]
        value = ea.read(cpu, ea.resolve(cpu, mode, reg, bits, ea.DATA_ALTERABLE))
        cpu.ccr = alu.merge_keep_x(cpu.ccr, alu.logic_flags(value, bits))
        return f"TST.{SIZE_NAMES[size]} <ea>"
    return None


def _logic_group(cpu, opcode, name, function, unmodeled):
    dn, opmode, mode, reg = _fields(opcode)
    if opmode in (3, 7):
        raise NotImplementedError(f"{unmodeled} not modeled")
    if opmode >= 4 and mode in (0, 1):
        raise NotImplementedError("BCD/EXG register forms not modeled")
    size = opmode & 3
    bits = alu.SIZE_BITS[size]
    m = alu.mask(bits)
    if opmode < 4:
        source = ea.resolve(cpu, mode, reg, bits, ea.DATA)
        result = function(cpu.d[dn] & m, ea.read(cpu, source)) & m
        ea.write(cpu, _dreg(bits, dn), result)
        text = f"{name}.{SIZE_NAMES[size]} <ea>,Dn"
    else:
        destination = ea.resolve(cpu, mode, reg, bits, ea.ALTERABLE_MEMORY)
        result = function(ea.read(cpu, destination), cpu.d[dn] & m) & m
        ea.write(cpu, destination, result)
        text = f"{name}.{SIZE_NAMES[size]} Dn,<ea>"
    cpu.ccr = alu.merge_keep_x(cpu.ccr, alu.logic_flags(result, bits))
    return text


def _or_group(cpu, opcode):
    return _logic_group(cpu, opcode, "OR", lambda a, b: a | b, "DIVU/DIVS")


def _and_group(cpu, opcode):
    return _logic_group(cpu, opcode, "AND", lambda a, b: a & b, "MULU/MULS")


def _arith_group(cpu, opcode, name, subtract):
    dn, opmode, mode, reg = _fields(opcode)
    if opmode in (3, 7):  # ADDA / SUBA: no flags, word source sign-extended
        source_bits = 16 if opmode == 3 else 32
        value = ea.read(cpu, ea.resolve(cpu, mode, reg, source_bits, ea.ALL))
        if source_bits == 16:
            value = alu.sign_extend(value, 16)
        current = cpu.a[dn]
        cpu.a[dn] = ((current - value) if subtract else (current + value)) & 0xffffffff
        return f"{name}A.{'W' if opmode == 3 else 'L'} <ea>,An"
    if opmode >= 4 and mode in (0, 1):
        raise NotImplementedError("ADDX/SUBX not modeled")
    size = opmode & 3
    bits = alu.SIZE_BITS[size]
    m = alu.mask(bits)
    function = alu.sub if subtract else alu.add
    if opmode < 4:
        source = ea.resolve(cpu, mode, reg, bits, ea.ALL)
        result, flags = function(cpu.d[dn] & m, ea.read(cpu, source), bits)
        ea.write(cpu, _dreg(bits, dn), result)
        text = f"{name}.{SIZE_NAMES[size]} <ea>,Dn"
    else:
        destination = ea.resolve(cpu, mode, reg, bits, ea.ALTERABLE_MEMORY)
        result, flags = function(ea.read(cpu, destination), cpu.d[dn] & m, bits)
        ea.write(cpu, destination, result)
        text = f"{name}.{SIZE_NAMES[size]} Dn,<ea>"
    cpu.ccr = flags
    return text


def _sub_group(cpu, opcode):
    return _arith_group(cpu, opcode, "SUB", True)


def _add_group(cpu, opcode):
    return _arith_group(cpu, opcode, "ADD", False)


def _cmp_eor_group(cpu, opcode):
    dn, opmode, mode, reg = _fields(opcode)
    if opmode in (3, 7):  # CMPA: compares the full 32-bit address register
        source_bits = 16 if opmode == 3 else 32
        value = ea.read(cpu, ea.resolve(cpu, mode, reg, source_bits, ea.ALL))
        if source_bits == 16:
            value = alu.sign_extend(value, 16)
        _, flags = alu.cmp(cpu.a[dn], value & 0xffffffff, 32)
        cpu.ccr = alu.merge_keep_x(cpu.ccr, flags)
        return f"CMPA.{'W' if opmode == 3 else 'L'} <ea>,An"
    size = opmode & 3
    bits = alu.SIZE_BITS[size]
    m = alu.mask(bits)
    if opmode < 3:
        source = ea.resolve(cpu, mode, reg, bits, ea.ALL)
        _, flags = alu.cmp(cpu.d[dn] & m, ea.read(cpu, source), bits)
        cpu.ccr = alu.merge_keep_x(cpu.ccr, flags)
        return f"CMP.{SIZE_NAMES[size]} <ea>,Dn"
    if mode == 1:
        raise NotImplementedError("CMPM not modeled")
    destination = ea.resolve(cpu, mode, reg, bits, ea.DATA_ALTERABLE)
    result = (ea.read(cpu, destination) ^ (cpu.d[dn] & m)) & m
    ea.write(cpu, destination, result)
    cpu.ccr = alu.merge_keep_x(cpu.ccr, alu.logic_flags(result, bits))
    return f"EOR.{SIZE_NAMES[size]} Dn,<ea>"


def _shift_group(cpu, opcode):
    left = bool(opcode & 0x0100)
    size_field = (opcode >> 6) & 3
    direction = "L" if left else "R"
    if size_field == 3:  # memory form: word operand shifted by exactly one
        if opcode & 0x0800:
            raise NotImplementedError("bit-field instructions not modeled")
        kind = SHIFT_KINDS[(opcode >> 9) & 3]
        operand = ea.resolve(cpu, (opcode >> 3) & 7, opcode & 7, 16, ea.ALTERABLE_MEMORY)
        result, ccr = alu.shift(kind, left, ea.read(cpu, operand), 1, 16, cpu.ccr)
        ea.write(cpu, operand, result)
        cpu.ccr = ccr
        return f"{kind}{direction}.W <ea>"
    bits = alu.SIZE_BITS[size_field]
    kind = SHIFT_KINDS[(opcode >> 3) & 3]
    count_field = (opcode >> 9) & 7
    from_register = bool(opcode & 0x20)
    count = (cpu.d[count_field] & 63) if from_register else (count_field or 8)
    register = opcode & 7
    result, ccr = alu.shift(kind, left, cpu.d[register] & alu.mask(bits), count, bits, cpu.ccr)
    ea.write(cpu, _dreg(bits, register), result)
    cpu.ccr = ccr
    source = "Dn" if from_register else "#n"
    return f"{kind}{direction}.{SIZE_NAMES[size_field]} {source},Dn"


_GROUPS = {0x4: _group4, 0x8: _or_group, 0x9: _sub_group, 0xb: _cmp_eor_group,
           0xc: _and_group, 0xd: _add_group, 0xe: _shift_group}


def execute(cpu, opcode):
    handler = _GROUPS.get(opcode >> 12)
    return handler(cpu, opcode) if handler else None
