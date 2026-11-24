import unittest
from cpu68k_muldiv import multiply, divide
from cpu68k_alu import X, N, Z, V

class MulDivTests(unittest.TestCase):
    def test_unsigned_multiply(self):
        self.assertEqual(multiply(0xffff, 2, False, X), (131070, X))
    def test_signed_multiply(self):
        self.assertEqual(multiply(0xffff, 2, True, 0), (0xfffffffe, N))
    def test_zero_multiply(self):
        self.assertEqual(multiply(0, 2, True, X), (0, X | Z))
    def test_unsigned_divide(self):
        self.assertEqual(divide(17, 5, False, X), (0x00020003, X))
    def test_signed_divide(self):
        self.assertEqual(divide(0xffffffef, 5, True, 0), (0xfffefffd, N))
    def test_overflow(self):
        self.assertEqual(divide(0x10000, 1, False, X), (0x10000, X | V))
    def test_zero_divisor(self):
        with self.assertRaises(ZeroDivisionError):
            divide(1, 0, False, 0)
