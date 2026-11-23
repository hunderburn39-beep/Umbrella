"""Immediate arithmetic regression matrix."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

class ImmediateArithmeticTests(unittest.TestCase):
    def test_matrix(self):
        for base, name in ((0x600, "ADDI"), (0x400, "SUBI"), (0xc00, "CMPI")):
            for size, bits in enumerate((8, 16, 32)):
                mask = (1 << bits) - 1
                sign = 1 << (bits - 1)
                for a,b in ((0,0),(mask,1),(sign-1,1),(sign,1),(0,1),(1,1),(sign,sign)):
                    for x in (0,16):
                        with self.subTest(name=name,bits=bits,a=a,b=b,x=x):
                            opcode = base | (size << 6) | 3
                            program = opcode.to_bytes(2,"big") + b.to_bytes(4 if bits==32 else 2,"big")
                            rom = bytearray(0x100 + len(program))
                            rom[:4] = (0xff0100).to_bytes(4,"big")
                            rom[4:8] = (0x100).to_bytes(4,"big")
                            rom[0x100:] = program
                            cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
                            cpu.reset()
                            original = (0x12345678 & ~mask) | a
                            cpu.d[3] = original
                            cpu.ccr = x | 15
                            add = name == "ADDI"
                            raw = a+b if add else a-b
                            result = raw & mask
                            signed = lambda n: n if n < sign else n-(mask+1)
                            sr = signed(a)+signed(b) if add else signed(a)-signed(b)
                            carry = not 0 <= raw <= mask
                            overflow = not -sign <= sr < sign
                            flags = (x if name=="CMPI" else 16 if carry else 0) | (8 if result&sign else 0) | (4 if result==0 else 0) | (2 if overflow else 0) | int(carry)
                            cpu.step()
                            self.assertEqual(cpu.d[3], original if name=="CMPI" else (original & ~mask)|result)
                            self.assertEqual(cpu.ccr,flags)
                            self.assertEqual(cpu.pc,0x100+len(program))

if __name__ == "__main__":
    unittest.main()
