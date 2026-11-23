"""Pure 68000 integer ALU reference."""
X, N, Z, V, C = 0x10, 0x08, 0x04, 0x02, 0x01
SIZE_BITS = (8, 16, 32)

def mask(bits):
    return (1 << bits) - 1

def sign_extend(value, bits):
    value &= mask(bits)
    return value - (1 << bits) if value & (1 << (bits - 1)) else value

def nz_flags(result, bits):
    return (N if result & (1 << (bits - 1)) else 0) | (Z if result == 0 else 0)

def add(dst, src, bits):
    m = mask(bits)
    d, s = dst & m, src & m
    full = d + s
    result = full & m
    flags = nz_flags(result, bits)
    if (~(d ^ s)) & (d ^ result) & (1 << (bits - 1)):
        flags |= V
    if full > m:
        flags |= C | X
    return result, flags

def sub(dst, src, bits):
    m = mask(bits)
    d, s = dst & m, src & m
    result = (d - s) & m
    flags = nz_flags(result, bits)
    if (d ^ s) & (d ^ result) & (1 << (bits - 1)):
        flags |= V
    if d < s:
        flags |= C | X
    return result, flags

def cmp(dst, src, bits):
    result, flags = sub(dst, src, bits)
    return result, flags & ~X

def merge_keep_x(old_ccr, flags):
    return (old_ccr & X) | (flags & (N | Z | V | C))

def logic_flags(result, bits):
    return nz_flags(result & mask(bits), bits)

def shift(kind, left, value, count, bits, old_ccr):
    if kind not in ("AS", "LS", "ROX", "RO"):
        raise ValueError("unknown shift kind")
    if not 0 <= count <= 63:
        raise ValueError("shift count must be 0..63")
    m = mask(bits)
    top = 1 << (bits - 1)
    v = value & m
    x = 1 if old_ccr & X else 0
    if count == 0:
        carry = x if kind == "ROX" else 0
        return v, (old_ccr & X) | nz_flags(v, bits) | (C if carry else 0)
    carry = 0
    overflow = False
    for _ in range(count):
        if left:
            out = 1 if v & top else 0
            if kind == "ROX":
                v = ((v << 1) & m) | x
                x = out
            elif kind == "RO":
                v = ((v << 1) & m) | out
            else:
                v = (v << 1) & m
                if kind == "AS" and bool(v & top) != bool(out):
                    overflow = True
        else:
            out = v & 1
            if kind == "ROX":
                v = (v >> 1) | (top if x else 0)
                x = out
            elif kind == "RO":
                v = (v >> 1) | (top if out else 0)
            elif kind == "AS":
                v = (v >> 1) | (v & top)
            else:
                v >>= 1
        carry = out
    flags = nz_flags(v, bits)
    if carry:
        flags |= C
    if overflow:
        flags |= V
    if kind == "RO":
        flags |= old_ccr & X
    elif carry:
        flags |= X
    return v, flags
