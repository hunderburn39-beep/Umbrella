"""68000 AND/OR/EOR/CMP/CMPA/TST/LEA through the instruction decoder."""
import unittest
from cpu68k_alu import X, N, Z, V, C
from cpu68k_test_support import make_cpu, ram_bytes, ram_long, state, bus_idle

RAM = 0xff1000


def assert_rejected(test, *words, **registers):
    cpu = make_cpu(*words, **registers)
    before = state(cpu)
    with test.assertRaises(NotImplementedError):
        cpu.step()
    test.assertEqual(state(cpu), before)
    test.assertTrue(bus_idle(cpu))


class LogicTests(unittest.TestCase):
    def test_and_word_keeps_x_clears_v_c(self):
        cpu = make_cpu(0xc041, d={0: 0xabcd0ff0, 1: 0x0f0f}, ccr=X | V | C)
        self.assertEqual(cpu.step().mnemonic, "AND.W <ea>,Dn")
        self.assertEqual(cpu.d[0], 0xabcd0f00)
        self.assertEqual(cpu.ccr, X)

    def test_and_zero_and_negative(self):
        cpu = make_cpu(0xc001, d={0: 0xf0, 1: 0x0f})
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, Z)
        cpu = make_cpu(0xc081, d={0: 0x80000001, 1: 0xffffffff})
        cpu.step()
        self.assertEqual(cpu.ccr, N)

    def test_and_long_immediate(self):
        cpu = make_cpu(0xc0bc, 0x00ff, 0x00ff, d={0: 0xffffffff})
        result = cpu.step()
        self.assertEqual(cpu.d[0], 0x00ff00ff)
        self.assertEqual(result.pc_after, 0x106)

    def test_or_byte_from_memory(self):
        cpu = make_cpu(0x8010, d={0: 0xf0}, a={0: RAM}, ram={RAM: bytes([0x0f])})
        self.assertEqual(cpu.step().mnemonic, "OR.B <ea>,Dn")
        self.assertEqual(cpu.d[0], 0xff)
        self.assertEqual(cpu.ccr, N)

    def test_or_register_into_memory_long(self):
        cpu = make_cpu(0x8191, d={0: 0xff}, a={1: RAM}, ram={RAM: (0xff00).to_bytes(4, "big")})
        self.assertEqual(cpu.step().mnemonic, "OR.L Dn,<ea>")
        self.assertEqual(ram_long(cpu, RAM), 0xffff)
        self.assertEqual(cpu.d[0], 0xff)

    def test_eor_word_register(self):
        cpu = make_cpu(0xb141, d={0: 0xffff, 1: 0x12345678})
        self.assertEqual(cpu.step().mnemonic, "EOR.W Dn,<ea>")
        self.assertEqual(cpu.d[1], 0x1234a987)
        self.assertEqual(cpu.ccr, N)

    def test_eor_byte_memory_to_zero(self):
        cpu = make_cpu(0xb110, d={0: 0xff}, a={0: RAM}, ram={RAM: bytes([0xff, 0x77])})
        cpu.step()
        self.assertEqual(ram_bytes(cpu, RAM, 2), bytes([0x00, 0x77]))
        self.assertEqual(cpu.ccr, Z)

    def test_logic_rejects_address_register_source(self):
        assert_rejected(self, 0xc048, a={0: 1})
        assert_rejected(self, 0x8048, a={0: 1})

    def test_unmodeled_neighbours_are_refused(self):
        for opcode in (0xc0c1, 0xc1c1, 0x80c1, 0x81c1):  # MULU MULS DIVU DIVS
            assert_rejected(self, opcode, d={0: 6, 1: 3})
        for opcode in (0xc101, 0x8101, 0xc141):          # ABCD SBCD EXG
            assert_rejected(self, opcode, d={0: 1, 1: 2})


class CompareTests(unittest.TestCase):
    def test_cmp_word_memory_keeps_x_and_destination(self):
        cpu = make_cpu(0xb050, d={0: 3}, a={0: RAM}, ram={RAM: bytes([0x00, 0x05])}, ccr=X)
        self.assertEqual(cpu.step().mnemonic, "CMP.W <ea>,Dn")
        self.assertEqual(cpu.d[0], 3)
        self.assertEqual(cpu.ccr, X | N | C)

    def test_cmp_long_immediate_equal(self):
        cpu = make_cpu(0xb0bc, 0x0000, 0x0005, d={0: 5})
        cpu.step()
        self.assertEqual(cpu.ccr, Z)

    def test_cmp_byte_postincrement(self):
        cpu = make_cpu(0xb018, d={0: 1}, a={0: RAM}, ram={RAM: bytes([0x01])})
        cpu.step()
        self.assertEqual(cpu.a[0], RAM + 1)
        self.assertEqual(cpu.ccr, Z)

    def test_register_to_register_compare_still_uses_original_decoder(self):
        cpu = make_cpu(0xb041, d={0: 1, 1: 1})
        self.assertEqual(cpu.step().mnemonic, "CMP.W Dn,Dm")

    def test_cmpa_word_sign_extends_source(self):
        cpu = make_cpu(0xb2c0, d={0: 0xffff}, a={1: 0xffffffff})
        self.assertEqual(cpu.step().mnemonic, "CMPA.W <ea>,An")
        self.assertEqual(cpu.ccr, Z)

    def test_cmpa_long_immediate_leaves_address_register(self):
        cpu = make_cpu(0xb1fc, 0x0000, 0x2000, a={0: 0x1000})
        cpu.step()
        self.assertEqual(cpu.a[0], 0x1000)
        self.assertEqual(cpu.ccr, N | C)

    def test_cmpm_is_refused(self):
        assert_rejected(self, 0xb348, a={0: RAM, 1: RAM})


class TstTests(unittest.TestCase):
    def test_tst_byte_indirect_keeps_x(self):
        cpu = make_cpu(0x4a10, a={0: RAM}, ram={RAM: bytes([0x80])}, ccr=X | V | C)
        self.assertEqual(cpu.step().mnemonic, "TST.B <ea>")
        self.assertEqual(cpu.ccr, X | N)

    def test_tst_byte_postincrement(self):
        cpu = make_cpu(0x4a18, a={0: RAM}, ram={RAM: bytes([0x00])})
        cpu.step()
        self.assertEqual(cpu.a[0], RAM + 1)
        self.assertEqual(cpu.ccr, Z)

    def test_tst_word_displacement(self):
        cpu = make_cpu(0x4a68, 0x0004, a={0: RAM}, ram={RAM + 4: bytes([0x00, 0x00])})
        cpu.step()
        self.assertEqual(cpu.ccr, Z)

    def test_tst_long_predecrement(self):
        cpu = make_cpu(0x4aa0, a={0: RAM + 4}, ram={RAM: (0x80000000).to_bytes(4, "big")})
        cpu.step()
        self.assertEqual(cpu.a[0], RAM)
        self.assertEqual(cpu.ccr, N)

    def test_tst_absolute_word(self):
        cpu = make_cpu(0x4a78, 0x8000, ram={0xff8000: bytes([0x80, 0x00])})
        cpu.step()
        self.assertEqual(cpu.ccr, N)

    def test_tst_rejects_address_register_and_tas(self):
        assert_rejected(self, 0x4a48, a={0: 1})
        cpu = make_cpu(0x4ac0)
        with self.assertRaisesRegex(NotImplementedError, "not implemented"):
            cpu.step()
        self.assertEqual(cpu.pc, 0x100)


class LeaTests(unittest.TestCase):
    def test_lea_displacement_keeps_flags(self):
        cpu = make_cpu(0x43e8, 0x0010, a={0: RAM}, ccr=X | N | Z | V | C)
        self.assertEqual(cpu.step().mnemonic, "LEA <ea>,An")
        self.assertEqual(cpu.a[1], RAM + 0x10)
        self.assertEqual(cpu.ccr, X | N | Z | V | C)

    def test_lea_pc_relative(self):
        cpu = make_cpu(0x41fa, 0x000e)
        cpu.step()
        self.assertEqual(cpu.a[0], 0x102 + 0x0e)

    def test_lea_absolute_word_is_not_masked(self):
        cpu = make_cpu(0x41f8, 0x8000)
        cpu.step()
        self.assertEqual(cpu.a[0], 0xffff8000)

    def test_lea_indexed(self):
        cpu = make_cpu(0x45f0, 0x1004, a={0: RAM}, d={1: 2})
        cpu.step()
        self.assertEqual(cpu.a[2], RAM + 6)

    def test_lea_never_touches_the_bus(self):
        cpu = make_cpu(0x43e8, 0x0010, a={0: 0xc00004})
        cpu.step()
        self.assertEqual(cpu.a[1], 0xc00014)

    def test_lea_rejects_non_control_modes(self):
        assert_rejected(self, 0x41d8, a={0: RAM})  # (An)+
        assert_rejected(self, 0x41c0)              # Dn


if __name__ == "__main__":
    unittest.main()
