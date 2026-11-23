"""Exhaustive Scc register condition checks across all CCR values."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

class SccTests(unittest.TestCase):
    def test_all_conditions_and_flags(self):
        for ccr in range(32):
            n, z, v, c = (bool(ccr & b) for b in (8, 4, 2, 1))
            expected = (True, False, not c and not z, c or z,
                        not c, c, not z, z, not v, v, not n, n,
                        n == v, n != v, not z and n == v, z or n != v)
            for condition, result in enumerate(expected):
                with self.subTest(ccr=ccr, condition=condition):
                    rom = bytearray(0x102)
                    rom[:4] = (0xff0100).to_bytes(4, "big")
                    rom[4:8] = (0x100).to_bytes(4, "big")
                    rom[0x100:] = (0x50c7 | (condition << 8)).to_bytes(2, "big")
                    cpu = CPU68KReference(ReferenceBusController(bytes(rom)))
                    cpu.reset()
                    cpu.ccr = ccr
                    cpu.d[7] = 0x12345678
                    self.assertEqual(cpu.step().mnemonic, "Scc Dn")
                    self.assertEqual(cpu.d[7], 0x123456ff if result else 0x12345600)
                    self.assertEqual(cpu.ccr, ccr)
                    self.assertEqual(cpu.pc, 0x102)
                    self.assertEqual(cpu.d[0], 0)

if __name__ == "__main__":
    unittest.main()
