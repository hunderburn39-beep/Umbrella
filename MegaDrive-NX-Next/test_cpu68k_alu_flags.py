"""Pure 68000 ALU flag and shift semantics (no CPU or bus involved)."""
import unittest
import cpu68k_alu as alu
from cpu68k_alu import X, N, Z, V, C


class SignExtendTests(unittest.TestCase):
    def test_sign_extend(self):
        self.assertEqual(alu.sign_extend(0xff, 8), -1)
        self.assertEqual(alu.sign_extend(0x7f, 8), 127)
        self.assertEqual(alu.sign_extend(0x8000, 16), -32768)
        self.assertEqual(alu.sign_extend(0xffffffff, 32), -1)
        self.assertEqual(alu.sign_extend(0x1ff, 8), -1)  # only low bits count


class AddFlagTests(unittest.TestCase):
    def test_byte_signed_overflow(self):
        self.assertEqual(alu.add(0x7f, 0x01, 8), (0x80, N | V))

    def test_byte_carry_sets_x_zero(self):
        self.assertEqual(alu.add(0xff, 0x01, 8), (0x00, Z | C | X))

    def test_byte_carry_and_overflow(self):
        self.assertEqual(alu.add(0x80, 0x80, 8), (0x00, Z | V | C | X))

    def test_word_plain(self):
        self.assertEqual(alu.add(0x1234, 0x0001, 16), (0x1235, 0))

    def test_long_carry(self):
        self.assertEqual(alu.add(0xffffffff, 2, 32), (1, C | X))

    def test_inputs_are_masked_to_size(self):
        self.assertEqual(alu.add(0x1ff, 1, 8), (0, Z | C | X))


class SubCmpFlagTests(unittest.TestCase):
    def test_borrow_sets_c_x_n(self):
        self.assertEqual(alu.sub(0, 1, 8), (0xff, N | C | X))

    def test_signed_overflow(self):
        self.assertEqual(alu.sub(0x80, 1, 8), (0x7f, V))

    def test_equal_sets_zero(self):
        self.assertEqual(alu.sub(5, 5, 8), (0, Z))

    def test_word_borrow(self):
        self.assertEqual(alu.sub(0x1234, 0x1235, 16), (0xffff, N | C | X))

    def test_long_overflow_and_borrow(self):
        self.assertEqual(alu.sub(0x7fffffff, 0xffffffff, 32),
                         (0x80000000, N | V | C | X))

    def test_cmp_never_reports_x(self):
        self.assertEqual(alu.cmp(0, 1, 8), (0xff, N | C))

    def test_merge_keep_x(self):
        self.assertEqual(alu.merge_keep_x(X | C | V, N), X | N)
        self.assertEqual(alu.merge_keep_x(0, N | X), N)  # X from flags ignored


class LogicFlagTests(unittest.TestCase):
    def test_negative_and_zero(self):
        self.assertEqual(alu.logic_flags(0x80, 8), N)
        self.assertEqual(alu.logic_flags(0, 16), Z)
        self.assertEqual(alu.logic_flags(0x100, 8), Z)  # masked to size


class ShiftTests(unittest.TestCase):
    def test_lsl_byte_carry_to_x(self):
        self.assertEqual(alu.shift("LS", True, 0x81, 1, 8, 0), (0x02, C | X))

    def test_lsl_clears_x_when_bit_out_is_zero(self):
        self.assertEqual(alu.shift("LS", True, 0x01, 1, 8, X), (0x02, 0))

    def test_lsr_to_zero(self):
        self.assertEqual(alu.shift("LS", False, 0x01, 1, 8, 0), (0, Z | C | X))

    def test_lsr_word_last_bit_out(self):
        self.assertEqual(alu.shift("LS", False, 0x00f8, 4, 16, 0), (0x000f, C | X))

    def test_lsl_by_size_and_beyond(self):
        self.assertEqual(alu.shift("LS", True, 0xff, 8, 8, 0), (0, Z | C | X))
        self.assertEqual(alu.shift("LS", True, 0xff, 9, 8, X), (0, Z))

    def test_asl_overflow_when_msb_changes(self):
        self.assertEqual(alu.shift("AS", True, 0x40, 1, 8, 0), (0x80, N | V))
        self.assertEqual(alu.shift("AS", True, 0x80, 1, 8, 0), (0, Z | V | C | X))
        self.assertEqual(alu.shift("AS", True, 0x20, 1, 8, 0), (0x40, 0))
        self.assertEqual(alu.shift("AS", True, 0xc0, 1, 8, 0), (0x80, N | C | X))

    def test_asl_overflow_is_sticky_across_steps(self):
        self.assertEqual(alu.shift("AS", True, 0x01, 7, 8, 0), (0x80, N | V))

    def test_asr_replicates_sign(self):
        self.assertEqual(alu.shift("AS", False, 0x81, 1, 8, 0), (0xc0, N | C | X))
        self.assertEqual(alu.shift("AS", False, 0x80, 7, 8, 0), (0xff, N))
        self.assertEqual(alu.shift("AS", False, 0x80, 8, 8, 0), (0xff, N | C | X))

    def test_asr_positive_runs_out(self):
        self.assertEqual(alu.shift("AS", False, 0x4000, 14, 16, 0), (1, 0))
        self.assertEqual(alu.shift("AS", False, 0x4000, 15, 16, 0), (0, Z | C | X))

    def test_rol_keeps_x_and_sets_c(self):
        self.assertEqual(alu.shift("RO", True, 0x81, 1, 8, 0), (0x03, C))
        self.assertEqual(alu.shift("RO", True, 0x81, 1, 8, X), (0x03, X | C))

    def test_ror_wraps_low_bit_to_msb(self):
        self.assertEqual(alu.shift("RO", False, 0x01, 1, 8, 0), (0x80, N | C))

    def test_rol_word_by_eight_swaps_bytes(self):
        self.assertEqual(alu.shift("RO", True, 0x1234, 8, 16, 0), (0x3412, 0))

    def test_roxl_rotates_through_x(self):
        self.assertEqual(alu.shift("ROX", True, 0x00, 1, 8, X), (0x01, 0))
        self.assertEqual(alu.shift("ROX", True, 0x80, 1, 8, X), (0x01, C | X))
        self.assertEqual(alu.shift("ROX", True, 0x80, 2, 8, 0), (0x01, 0))

    def test_roxr_rotates_through_x(self):
        self.assertEqual(alu.shift("ROX", False, 0x01, 1, 8, 0), (0, Z | C | X))

    def test_count_zero_rules(self):
        # Shifts: C and V cleared, X unchanged.
        self.assertEqual(alu.shift("LS", True, 0x80, 0, 8, X | C | V), (0x80, X | N))
        # Rotate without X: C cleared, X unchanged.
        self.assertEqual(alu.shift("RO", True, 0x00, 0, 8, X | C), (0, X | Z))
        # Rotate through X: C takes X.
        self.assertEqual(alu.shift("ROX", True, 0x00, 0, 8, X), (0, X | Z | C))
        self.assertEqual(alu.shift("ROX", True, 0x00, 0, 8, 0), (0, Z))

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            alu.shift("BAD", True, 1, 1, 8, 0)
        with self.assertRaises(ValueError):
            alu.shift("LS", True, 1, 64, 8, 0)
        with self.assertRaises(ValueError):
            alu.shift("LS", True, 1, -1, 8, 0)


if __name__ == "__main__":
    unittest.main()
