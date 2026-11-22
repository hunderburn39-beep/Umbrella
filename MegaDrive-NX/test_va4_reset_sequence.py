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

    def test_pulse_is_microseconds_not_milliseconds(self):
        seq = VA4ResetSequence()
        # 128 cycles at PAL MCLK/7 are approximately 16.84 microseconds.
        self.assertGreater(seq.button_pulse_s, 16e-6)
        self.assertLess(seq.button_pulse_s, 18e-6)
        # Cold-boot release delay is distinct from the reset pulse width.
        self.assertGreater(seq.vres_release_delay_s, 0.01)
        self.assertLess(seq.button_pulse_s, seq.vres_release_delay_s)

    def test_negative_time(self):
        with self.assertRaises(ValueError):
            VA4ResetSequence().power_on(-0.01)
        with self.assertRaises(ValueError):
            VA4ResetSequence().reset_button_vres(-0.01)


if __name__ == "__main__":
    unittest.main()
