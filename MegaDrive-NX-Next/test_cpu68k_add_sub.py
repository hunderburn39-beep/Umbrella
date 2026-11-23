"""68000 ADD/SUB/ADDA/SUBA through the instruction decoder."""
import unittest
from cpu68k_alu import X, N, Z, V, C
from cpu68k_test_support import make_cpu, ram_bytes, ram_word, ram_long, state, bus_idle

RAM = 0xff1000


class AddTests(unittest.TestCase):
    def test_add_byte_register_preserves_upper_bits_and_sets_nv(self):
        cpu = make_cpu(0xd001, d={0: 0x1234567f, 1: 1})
        result = cpu.step()
        self.assertEqual(result.mnemonic, "ADD.B <ea>,Dn")
        self.assertEqual(result.pc_after, 0x102)
        self.assertEqual(cpu.d[0], 0x12345680)
        self.assertEqual(cpu.ccr, N | V)

    def test_add_replaces_x_with_carry(self):
        cpu = make_cpu(0xd001, d={0: 1, 1: 1}, ccr=X | N | Z | V | C)
        cpu.step()
        self.assertEqual(cpu.d[0] & 0xff, 2)
        self.assertEqual(cpu.ccr, 0)

    def test_add_word_carry_sets_c_x_z(self):
        cpu = make_cpu(0xd041, d={0: 0xabcdffff, 1: 1})
        cpu.step()
        self.assertEqual(cpu.d[0], 0xabcd0000)
        self.assertEqual(cpu.ccr, Z | C | X)

    def test_add_long_immediate(self):
        cpu = make_cpu(0xd0bc, 0x0000, 0x0001, d={0: 0x7fffffff})
        result = cpu.step()
        self.assertEqual(cpu.d[0], 0x80000000)
        self.assertEqual(cpu.ccr, N | V)
        self.assertEqual(result.pc_after, 0x106)

    def test_add_word_postincrement_source(self):
        cpu = make_cpu(0xd458, d={2: 3}, a={0: RAM}, ram={RAM: bytes([0x01, 0x02])})
        cpu.step()
        self.assertEqual(cpu.d[2], 0x0105)
        self.assertEqual(cpu.a[0], RAM + 2)

    def test_add_to_memory_long(self):
        cpu = make_cpu(0xd191, d={0: 0x20}, a={1: RAM}, ram={RAM: (0x10).to_bytes(4, "big")})
        result = cpu.step()
        self.assertEqual(result.mnemonic, "ADD.L Dn,<ea>")
        self.assertEqual(ram_long(cpu, RAM), 0x30)
        self.assertEqual(cpu.d[0], 0x20)
        self.assertEqual(cpu.ccr, 0)

    def test_postincrement_destination_applies_once(self):
        cpu = make_cpu(0xd158, d={0: 1}, a={0: RAM}, ram={RAM: bytes([0x00, 0xff])})
        cpu.step()
        self.assertEqual(ram_word(cpu, RAM), 0x0100)
        self.assertEqual(cpu.a[0], RAM + 2)

    def test_byte_to_memory_uses_only_its_lane(self):
        cpu = make_cpu(0xd110, d={0: 5}, a={0: RAM + 1}, ram={RAM: bytes([0xaa, 0x10])})
        cpu.step()
        self.assertEqual(ram_bytes(cpu, RAM, 2), bytes([0xaa, 0x15]))
        cpu = make_cpu(0xd110, d={0: 5}, a={0: RAM}, ram={RAM: bytes([0x10, 0xbb])})
        cpu.step()
        self.assertEqual(ram_bytes(cpu, RAM, 2), bytes([0x15, 0xbb]))

    def test_byte_postincrement_through_a7_steps_by_two(self):
        cpu = make_cpu(0xd01f, d={0: 1}, a={7: RAM}, ram={RAM: bytes([0x07, 0x99])})
        cpu.step()
        self.assertEqual(cpu.d[0] & 0xff, 8)
        self.assertEqual(cpu.a[7], RAM + 2)

    def test_address_register_source_allowed_for_word(self):
        cpu = make_cpu(0xd049, d={0: 1}, a={1: 0x0001ffff})
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, Z | C | X)


class SubTests(unittest.TestCase):
    def test_sub_word_register_borrow(self):
        cpu = make_cpu(0x9041, d={0: 5, 1: 7})
        self.assertEqual(cpu.step().mnemonic, "SUB.W <ea>,Dn")
        self.assertEqual(cpu.d[0], 0xfffe)
        self.assertEqual(cpu.ccr, N | C | X)

    def test_sub_to_memory_computes_memory_minus_register(self):
        cpu = make_cpu(0x9110, d={0: 2}, a={0: RAM}, ram={RAM: bytes([0x01, 0x00])})
        cpu.step()
        self.assertEqual(ram_bytes(cpu, RAM, 1), bytes([0xff]))
        self.assertEqual(cpu.ccr, N | C | X)

    def test_sub_long_immediate_overflow(self):
        cpu = make_cpu(0x90bc, 0x0000, 0x0001, d={0: 0x80000000})
        cpu.step()
        self.assertEqual(cpu.d[0], 0x7fffffff)
        self.assertEqual(cpu.ccr, V)


class AddaSubaTests(unittest.TestCase):
    def test_adda_word_sign_extends_and_keeps_flags(self):
        cpu = make_cpu(0xd2c0, d={0: 0x00008000}, a={1: 0x10000}, ccr=X | N | Z | V | C)
        self.assertEqual(cpu.step().mnemonic, "ADDA.W <ea>,An")
        self.assertEqual(cpu.a[1], 0x8000)
        self.assertEqual(cpu.ccr, X | N | Z | V | C)

    def test_adda_long_from_address_register(self):
        cpu = make_cpu(0xd3c8, a={0: 0x1000, 1: 0x2000})
        cpu.step()
        self.assertEqual(cpu.a[1], 0x3000)

    def test_adda_wraps_at_32_bits(self):
        cpu = make_cpu(0xd2c0, d={0: 2}, a={1: 0xffffffff})
        cpu.step()
        self.assertEqual(cpu.a[1], 1)

    def test_suba_long_immediate_on_stack_pointer(self):
        cpu = make_cpu(0x9ffc, 0x0000, 0x0010)
        sp = cpu.a[7]
        cpu.step()
        self.assertEqual(cpu.a[7], sp - 0x10)


class RejectedEncodingTests(unittest.TestCase):
    def assert_rejected(self, *words, **registers):
        cpu = make_cpu(*words, **registers)
        before = state(cpu)
        with self.assertRaises(NotImplementedError):
            cpu.step()
        self.assertEqual(state(cpu), before)
        self.assertTrue(bus_idle(cpu))

    def test_addx_and_subx_not_modeled(self):
        self.assert_rejected(0xd300, d={0: 1, 1: 2}, ccr=X)
        self.assert_rejected(0x9308, a={0: RAM, 1: RAM})

    def test_byte_add_from_address_register_is_illegal(self):
        self.assert_rejected(0xd009, a={1: 5})

    def test_failed_write_restores_registers_and_pc(self):
        # ADD.W D0,(A0)+ aimed at ROM: the write is refused after the read.
        self.assert_rejected(0xd158, d={0: 1}, a={0: 0x200}, ccr=X | C)

    def test_peripheral_byte_read_refused(self):
        self.assert_rejected(0xd010, a={0: 0xc00004})

    def test_unready_vdp_word_read_refused(self):
        self.assert_rejected(0xd050, a={0: 0xc00004})


if __name__ == "__main__":
    unittest.main()
