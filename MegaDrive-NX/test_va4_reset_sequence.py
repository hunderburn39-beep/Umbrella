import unittest
from va4_reset_sequence import VA4ResetSequence


class VA4ResetSequenceTests(unittest.TestCase):
    def test_ordering(self):
        seq = VA4ResetSequence()
        self.assertFalse(seq.power_on(0).sres_high)
        t = seq.rc.threshold_time_s
        self.assertTrue(seq.power_on(t + 0.001).sres_high)
        self.assertFalse(seq.power_on(t + 0.001).vres_high)
        self.assertTrue(seq.power_on(t + 0.014).vres_high)

    def test_button_pulse_128_vclks(self):
        seq = VA4ResetSequence()
        self.assertAlmostEqual(seq.button_pulse_s * seq.vclk_hz, 128)
        self.assertFalse(seq.reset_button_vres(seq.button_pulse_s / 2))
        self.assertTrue(seq.reset_button_vres(seq.button_pulse_s * 2))

    def test_negative_time(self):
        with self.assertRaises(ValueError):
            VA4ResetSequence().power_on(-0.01)
        with self.assertRaises(ValueError):
            VA4ResetSequence().reset_button_vres(-0.01)


if __name__ == "__main__":
    unittest.main()
