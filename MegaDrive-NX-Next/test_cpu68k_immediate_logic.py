"""Immediate logical operations: ORI, ANDI and EORI, all register sizes."""
import unittest
import operator
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

class ImmediateLogicTests(unittest.TestCase):
    def test_matrix(self):
        for base, name, operation in ((0, "ORI", operator.or_),
                                      (0x200, "ANDI", operator.and_),
                                      (0xa00, "EORI", operator.xor)):
            for size, bits in enumerate((8, 16, 32)):
                mask = (1 << bits) - 1
                for original, immediate in ((0x12345678, 0x89abcdef),
                                            (0xffffffff, 0xffffffff),
                                            (0, 0), (0, 1)):
                    with self.subTest(name=name, bits=bits, original=original, immediate=immediate):
                        opcode = base | (size << 6) | 3
                        extension = (immediate & mask).to_bytes(4 if bits == 32 else 2, "big")
                        program = opcode.to_bytes(2, "big") + extension
                        rom = bytearray(0x100 + len(program))
                        rom[:4] = (0xff0100).to_bytes(4, "big")
                        rom[4:8] = (0x100).to_bytes(4, "big")
                        rom[0x100:] = program
                        cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
                        cpu.reset()
                        cpu.d[3] = original
                        cpu.ccr = 0x1f
                        result = operation(original & mask, immediate & mask)
                        self.assertEqual(cpu.step().mnemonic, name + "." + ("B", "W", "L")[size] + " #imm,Dn")
                        self.assertEqual(cpu.d[3], (original & ~mask) | result)
                        flags = 0x10 | (8 if result & (1 << (bits - 1)) else 0) | (4 if result == 0 else 0)
                        self.assertEqual(cpu.ccr, flags)
                        self.assertEqual(cpu.pc, 0x100 + len(program))
                        self.assertEqual(cpu.d[0], 0)

if __name__ == "__main__":
    unittest.main()
