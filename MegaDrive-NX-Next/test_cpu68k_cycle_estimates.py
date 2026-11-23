"""Nominal CPU cycle-estimate regression tests."""
import unittest
from types import SimpleNamespace
from cpu68k_cycle_estimates import estimate_instruction_cycles


class CycleEstimateTests(unittest.TestCase):
    def test_fixed_opcode_nominal_cycles(self):
        for opcode, expected in ((0x4e71, 4), (0x4e75, 16),
                                 (0x4e73, 20), (0x4e72, 4)):
            with self.subTest(opcode=opcode):
                self.assertEqual(
                    estimate_instruction_cycles(SimpleNamespace(opcode=opcode)),
                    expected)

    def test_moveq_registers_have_same_cost(self):
        for opcode in (0x7000, 0x72ff, 0x7e80):
            self.assertEqual(
                estimate_instruction_cycles(SimpleNamespace(opcode=opcode)), 4)

    def test_branch_dependent_dbcc_is_not_guessed(self):
        with self.assertRaises(NotImplementedError):
            estimate_instruction_cycles(SimpleNamespace(opcode=0x51c8))

    def test_unknown_opcode_is_not_guessed(self):
        with self.assertRaises(NotImplementedError):
            estimate_instruction_cycles(SimpleNamespace(opcode=0x3080))


if __name__ == "__main__":
    unittest.main()
