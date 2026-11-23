"""Untimed MC68000 word multiply/divide reference; decoder integration pending."""
from cpu68k_alu import X, V, logic_flags, sign_extend

def multiply(dst, src, signed, ccr):
    a, b = dst & 0xffff, src & 0xffff
    if signed:
        a, b = sign_extend(a, 16), sign_extend(b, 16)
    result = (a * b) & 0xffffffff
    return result, (ccr & X) | logic_flags(result, 32)

def divide(dst, src, signed, ccr):
    a, b = dst & 0xffffffff, src & 0xffff
    if signed:
        a, b = sign_extend(a, 32), sign_extend(b, 16)
    if not b:
        raise ZeroDivisionError("68000 vector 5 pending CPU integration")
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    rem = a - q * b
    lo, hi = (-32768, 32767) if signed else (0, 65535)
    if not lo <= q <= hi:
        # N/Z undefined on overflow: reference policy clears both.
        return dst & 0xffffffff, (ccr & X) | V
    return ((rem & 0xffff) << 16) | (q & 0xffff), (ccr & X) | logic_flags(q, 16)
