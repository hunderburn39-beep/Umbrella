import unittest
from board import Board, cpu_word_to_byte, cpu_vdp_address, require_verified_core

class Genesis3VA2Tests(unittest.TestCase):
    def test_hardware_identity(self):
        self.assertEqual(Board().main_asic, "315-6123")
        self.assertEqual(Board().revision, "VA2")

    def test_word_bus_mapping(self):
        self.assertEqual(cpu_word_to_byte(0x600002), 0xc00004)
        self.assertEqual(cpu_word_to_byte(0x7fffff), 0xfffffe)

    def test_vdp_candidate_window(self):
        self.assertTrue(cpu_vdp_address(0x600002))
        self.assertFalse(cpu_vdp_address(0x400002))

    def test_refuse_unverified_core(self):
        with self.assertRaisesRegex(RuntimeError, "not implemented"):
            require_verified_core(Board())

    def test_invalid_address(self):
        with self.assertRaises(ValueError):
            cpu_word_to_byte(0x800000)

if __name__ == "__main__":
    unittest.main()
