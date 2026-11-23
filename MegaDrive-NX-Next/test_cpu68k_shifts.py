"""68000 shift and rotate instructions through the instruction decoder."""
import unittest
from cpu68k_alu import X, N, Z, V, C
from cpu68k_test_support import make_cpu, ram_word, state, bus_idle

RAM = 0xff1000
KINDS = {"AS": 0, "LS": 1, "ROX": 2, "RO": 3}
B, W, L = 0, 1, 2


def reg_shift(kind, left, size, count, reg=0, from_register=False):
    """Encode ASx/LSx/ROXx/ROx on a data register (count 8 encodes as 0)."""
    return (0xe000 | ((count & 7) << 9) | (0x100 if left else 0) | (size << 6)
            | (0x20 if from_register else 0) | (KINDS[kind] << 3) | reg)


def mem_shift(kind, left, mode=2, reg=0):
    """Encode the word-sized memory form, which shifts by exactly one."""
    return 0xe0c0 | (KINDS[kind] << 9) | (0x100 if left else 0) | (mode << 3) | reg


class EncodingSanityTests(unittest.TestCase):
    def test_known_opcodes(self):
        self.assertEqual(reg_shift("RO", True, W, 8), 0xe158)   # ROL.W #8,D0
        self.assertEqual(reg_shift("AS", True, W, 1), 0xe340)   # ASL.W #1,D0
        self.assertEqual(reg_shift("LS", True, W, 2), 0xe548)   # LSL.W #2,D0
        self.assertEqual(reg_shift("RO", False, W, 1), 0xe258)  # ROR.W #1,D0
        self.assertEqual(mem_shift("LS", True), 0xe3d0)         # LSL.W (A0)


class RegisterShiftTests(unittest.TestCase):
    def test_lsl_byte_preserves_upper_bits(self):
        cpu = make_cpu(reg_shift("LS", True, B, 1), d={0: 0x12345681})
        self.assertEqual(cpu.step().mnemonic, "LSL.B #n,Dn")
        self.assertEqual(cpu.d[0], 0x12345602)
        self.assertEqual(cpu.ccr, C | X)

    def test_lsr_word(self):
        cpu = make_cpu(reg_shift("LS", False, W, 4), d={0: 0xaaaa00f8})
        cpu.step()
        self.assertEqual(cpu.d[0], 0xaaaa000f)
        self.assertEqual(cpu.ccr, C | X)

    def test_asl_word_overflow(self):
        cpu = make_cpu(reg_shift("AS", True, W, 1), d={0: 0x4000})
        cpu.step()
        self.assertEqual(cpu.d[0], 0x8000)
        self.assertEqual(cpu.ccr, N | V)

    def test_asr_long_keeps_sign(self):
        cpu = make_cpu(reg_shift("AS", False, L, 1), d={0: 0x80000001})
        cpu.step()
        self.assertEqual(cpu.d[0], 0xc0000000)
        self.assertEqual(cpu.ccr, N | C | X)

    def test_rol_word_by_eight_swaps_bytes(self):
        cpu = make_cpu(reg_shift("RO", True, W, 8), d={0: 0x00001234})
        cpu.step()
        self.assertEqual(cpu.d[0], 0x00003412)

    def test_ror_keeps_x(self):
        cpu = make_cpu(reg_shift("RO", False, B, 1), d={0: 0x01}, ccr=X)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x80)
        self.assertEqual(cpu.ccr, X | N | C)

    def test_roxl_uses_x(self):
        cpu = make_cpu(reg_shift("ROX", True, B, 1), d={0: 0x80}, ccr=X)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x01)
        self.assertEqual(cpu.ccr, C | X)

    def test_immediate_count_eight_encodes_as_zero(self):
        cpu = make_cpu(reg_shift("LS", False, L, 8), d={0: 0x12345678})
        cpu.step()
        self.assertEqual(cpu.d[0], 0x00123456)

    def test_count_from_register_is_modulo_64(self):
        cpu = make_cpu(reg_shift("LS", True, L, 1, from_register=True),
                       d={0: 1, 1: 0x44})
        self.assertEqual(cpu.step().mnemonic, "LSL.L Dn,Dn")
        self.assertEqual(cpu.d[0], 0x10)

    def test_register_count_zero_clears_c_keeps_x(self):
        cpu = make_cpu(reg_shift("LS", True, L, 1, from_register=True),
                       d={0: 0x80000000, 1: 64}, ccr=X | C)
        cpu.step()
        self.assertEqual(cpu.d[0], 0x80000000)
        self.assertEqual(cpu.ccr, X | N)

    def test_register_count_beyond_operand_size(self):
        cpu = make_cpu(reg_shift("LS", True, L, 1, from_register=True),
                       d={0: 1, 1: 33}, ccr=X | C)
        cpu.step()
        self.assertEqual(cpu.d[0], 0)
        self.assertEqual(cpu.ccr, Z)

    def test_shifting_the_count_register_itself(self):
        cpu = make_cpu(reg_shift("LS", True, L, 0, reg=0, from_register=True),
                       d={0: 3})
        cpu.step()
        self.assertEqual(cpu.d[0], 3 << 3)


class MemoryShiftTests(unittest.TestCase):
    def test_lsl_word_in_memory(self):
        cpu = make_cpu(mem_shift("LS", True), a={0: RAM}, ram={RAM: bytes([0x80, 0x01])})
        self.assertEqual(cpu.step().mnemonic, "LSL.W <ea>")
        self.assertEqual(ram_word(cpu, RAM), 0x0002)
        self.assertEqual(cpu.ccr, C | X)

    def test_asr_word_in_memory(self):
        cpu = make_cpu(mem_shift("AS", False), a={0: RAM}, ram={RAM: bytes([0x80, 0x01])})
        cpu.step()
        self.assertEqual(ram_word(cpu, RAM), 0xc000)
        self.assertEqual(cpu.ccr, N | C | X)

    def test_roxr_word_in_memory(self):
        cpu = make_cpu(mem_shift("ROX", False), a={0: RAM}, ram={RAM: bytes([0x00, 0x01])})
        cpu.step()
        self.assertEqual(ram_word(cpu, RAM), 0)
        self.assertEqual(cpu.ccr, Z | C | X)

    def test_rol_word_postincrement(self):
        cpu = make_cpu(mem_shift("RO", True, mode=3), a={0: RAM}, ram={RAM: bytes([0x80, 0x00])})
        cpu.step()
        self.assertEqual(ram_word(cpu, RAM), 0x0001)
        self.assertEqual(cpu.a[0], RAM + 2)

    def test_register_and_bit_field_forms_are_refused(self):
        for opcode in (mem_shift("LS", True, mode=0), 0xe8d0):
            cpu = make_cpu(opcode, d={0: 1}, a={0: RAM})
            before = state(cpu)
            with self.assertRaises(NotImplementedError):
                cpu.step()
            self.assertEqual(state(cpu), before)
            self.assertTrue(bus_idle(cpu))


if __name__ == "__main__":
    unittest.main()
