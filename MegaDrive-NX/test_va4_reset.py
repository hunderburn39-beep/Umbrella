"""Run: python3 -m unittest MegaDrive-NX/test_va4_reset.py"""
import unittest
from va4_reset import ResetRC


class ResetTests(unittest.TestCase):
    def test_nominal_tau(self):
        self.assertAlmostEqual(ResetRC().tau_s, 0.47)

    def test_voltage_starts_at_zero(self):
        self.assertAlmostEqual(ResetRC().capacitor_voltage(0), 0.0)

    def test_threshold_crossing(self):
        m = ResetRC()
        t = m.threshold_time_s
        self.assertFalse(m.sres_released(t * 0.99))
        self.assertTrue(m.sres_released(t * 1.01))
        self.assertAlmostEqual(m.capacitor_voltage(t), 2.0)

    def test_invalid_components(self):
        with self.assertRaises(ValueError):
            ResetRC(resistance_ohm=0)
        with self.assertRaises(ValueError):
            ResetRC(threshold_v=5.0)

    def test_negative_time(self):
        with self.assertRaises(ValueError):
            ResetRC().capacitor_voltage(-1)


if __name__ == "__main__":
    unittest.main()
