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

    def test_register_longword_write_to_ram(self):
        c = cpu("203c 1357 9bdf 23c0 00ff 0010")
        c.run(2)
        self.assertEqual(c.bus.memory.read_word(0xff0010), 0x1357)
        self.assertEqual(c.bus.memory.read_word(0xff0012), 0x9bdf)
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_register_longword_write_preserves_x(self):
        c = cpu("23c1 00ff 0010")
        c.d[1] = 0x80000001
        c.ccr = 0x1f
        self.assertEqual(c.step().mnemonic, "MOVE.L Dn,(abs.l)")
        self.assertEqual(c.ccr, 0x18)

    def test_register_longword_write_odd_address_rejected(self):
        c = cpu("23c0 00ff 0011")
        with self.assertRaises(ValueError):
            c.step()
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_address_indirect_longword_roundtrip(self):
        c = cpu("207c 00ff 0020 223c 89ab cdef 2081 2410")
        trace = c.run(4)
        self.assertEqual([s.mnemonic for s in trace],
                         ["MOVEA.L #imm,An", "MOVE.L #imm,Dn",
                          "MOVE.L Dn,(An)", "MOVE.L (An),Dn"])
        self.assertEqual(c.d[2], 0x89abcdef)
        self.assertEqual(c.a[0], 0xff0020)
        self.assertEqual(c.bus.memory.read_word(0xff0020), 0x89ab)
        self.assertEqual(c.bus.memory.read_word(0xff0022), 0xcdef)

    def test_indirect_longword_read_preserves_address_register(self):
        c = cpu("2010")
        c.a[0] = 0xff0100
        c.bus.memory.write_word(0xff0100, 0x8000)
        c.bus.memory.write_word(0xff0102, 0x0001)
        c.step()
        self.assertEqual(c.d[0], 0x80000001)
        self.assertEqual(c.a[0], 0xff0100)
        self.assertEqual(c.ccr & 15, 8)

    def test_indirect_longword_odd_address_rejected(self):
        c = cpu("2010")
        c.a[0] = 0xff0101
        with self.assertRaises(ValueError):
            c.step()
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_indirect_longword_boundary_rejected(self):
        c = cpu("2081")
        c.a[0] = 0xfffffe
        with self.assertRaises(ValueError):
            c.step()
        self.assertIs(c.bus.cycle.phase, Phase.IDLE)

    def test_movea_absolute_long_loads_pointer(self):
        c = cpu("2279 00ff 0020")
        c.bus.memory.write_word(0xff0020, 0x00c0)
        c.bus.memory.write_word(0xff0022, 0x0004)
        c.ccr = 0x1b
        self.assertEqual(c.step().mnemonic, "MOVEA.L (abs.l),An")
        self.assertEqual(c.a[1], 0xc00004)
        self.assertEqual(c.ccr, 0x1b)

    def test_movea_indirect_loads_pointer(self):
        c = cpu("2250")
        c.a[0] = 0xff0020
        c.bus.memory.write_word(0xff0020, 0x00ff)
        c.bus.memory.write_word(0xff0022, 0x1000)
        self.assertEqual(c.step().mnemonic, "MOVEA.L (An),Am")
        self.assertEqual(c.a[1], 0xff1000)
        self.assertEqual(c.a[0], 0xff0020)

    def test_movea_indirect_same_register_uses_old_pointer(self):
        c = cpu("2050")
        c.a[0] = 0xff0020
        c.bus.memory.write_word(0xff0020, 0x00ff)
        c.bus.memory.write_word(0xff0022, 0x0040)
        c.step()
        self.assertEqual(c.a[0], 0xff0040)

    def test_movea_indirect_rejects_odd_address(self):
        c = cpu("2250")
        c.a[0] = 0xff0021
        with self.assertRaises(ValueError):
            c.step()
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
