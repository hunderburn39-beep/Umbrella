"""68000 condition-code truth table regression checks.

This tests all 14 conditional branch predicates against N/Z/V/C
combinations, without asserting cycle-accurate execution.
"""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference

class ConditionMatrixTests(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU68KReference(ReferenceBusController(bytes(8)))

    @staticmethod
    def expected(code, n, z, v, c):
        if code == 0: return True
        if code == 1: return False
        if code == 2: return not (c or z)
        if code == 3: return c or z
        if code == 4: return not c
        if code == 5: return c
        if code == 6: return not z
        if code == 7: return z
        if code == 8: return not v
        if code == 9: return v
        if code == 10: return not n
        if code == 11: return n
        if code == 12: return n == v
        if code == 13: return n != v
        if code == 14: return not z and n == v
        if code == 15: return z or n != v
        raise ValueError(code)

    def test_all_16_conditions_all_16_nzvc_states(self):
        for flags in range(16):
            n, z, v, c = (bool(flags & bit) for bit in (8, 4, 2, 1))
            self.cpu.ccr = flags
            for code in range(16):
                with self.subTest(flags=flags, condition=code):
                    self.assertEqual(
                        self.cpu._condition(code),
                        self.expected(code, n, z, v, c),
                    )

    def test_extend_flag_does_not_change_branch_conditions(self):
        for flags in range(16):
            for code in range(16):
                self.cpu.ccr = flags
                without_x = self.cpu._condition(code)
                self.cpu.ccr = flags | 0x10
                with self.subTest(flags=flags, condition=code):
                    self.assertEqual(self.cpu._condition(code), without_x)

    def test_cmp_word_equal_preserves_extend(self):
        self.cpu.ccr = 0x10
        self.cpu._compare_word(0x1234, 0x1234)
        self.assertEqual(self.cpu.ccr, 0x14)

    def test_cmp_word_unsigned_borrow(self):
        self.cpu.ccr = 0
        self.cpu._compare_word(0, 1)
        self.assertEqual(self.cpu.ccr & 0x0f, 0x09)

    def test_cmp_word_signed_overflow(self):
        self.cpu.ccr = 0
        self.cpu._compare_word(0x7fff, 0xffff)
        self.assertEqual(self.cpu.ccr & 0x0f, 0x0b)

    def test_move_flags_preserve_extend_and_clear_overflow_carry(self):
        self.cpu.ccr = 0x13
        self.cpu._logic_flags(0, 16)
        self.assertEqual(self.cpu.ccr, 0x14)

if __name__ == "__main__":
    unittest.main()
