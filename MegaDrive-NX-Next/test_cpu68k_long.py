"""68000 longword data movement reference tests."""
import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Phase
from cpu68k_reference import CPU68KReference

def cpu(program):
    code = bytes.fromhex(program)
    rom = bytearray(0x100 + len(code))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = code
    c = CPU68KReference(ReferenceBusController(bytes(rom)))
    c.reset()
    return c

class LongwordTests(unittest.TestCase):
    def test_immediate_long_to_d0(self):
        c = cpu("203c 1234 5678")
        self.assertEqual(c.step().mnemonic, "MOVE.L #imm,Dn")
        self.assertEqual(c.d[0], 0x12345678)
        self.assertEqual(c.pc, 0x106)

    def test_immediate_long_to_d1(self):
        c = cpu("223c ffff 0001")
        c.step()
        self.assertEqual(c.d[1], 0xffff0001)
        self.assertTrue(c.ccr & 8)

    def test_immediate_zero_sets_z_preserves_x(self):
        c = cpu("203c 0000 0000")
        c.ccr = 0x1b
        c.step()
        self.assertEqual(c.ccr, 0x14)

    def test_longword_to_ram_and_back(self):
        c = cpu("23fc 89ab cdef 00ff 0010 2239 00ff 0010")
        c.run(2)
        self.assertEqual(c.bus.memory.read_word(0xff0010), 0x89ab)
        self.assertEqual(c.bus.memory.read_word(0xff0012), 0xcdef)
        self.assertEqual(c.d[1], 0x89abcdef)
        self.assertTrue(c.ccr & 8)
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_longword_rom_read(self):
        c = cpu("2039 0000 0100")
        c.step()
        self.assertEqual(c.d[0], 0x20390000)

    def test_odd_longword_address(self):
        c = cpu("2039 00ff 0001")
        with self.assertRaises(ValueError):
            c.step()
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_cross_bus_boundary_rejected(self):
        c = cpu("2039 00ff fffe")
        with self.assertRaises(ValueError):
            c.step()
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_longword_write_unsupported_peripheral(self):
        c = cpu("23fc 0000 0001 00c0 0008")
        with self.assertRaises(NotImplementedError):
            c.step()
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

if __name__ == "__main__":
    unittest.main()
