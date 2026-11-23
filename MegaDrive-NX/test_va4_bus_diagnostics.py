import unittest
from va4_bus_diagnostics import BusObservation, byte_address, is_vdp_window, classify

class BusDiagnosticsTest(unittest.TestCase):
    def test_word_to_byte_address(self):
        self.assertEqual(byte_address(0x600002), 0xc00004)
        self.assertEqual(byte_address(0x000100), 0x000200)

    def test_vdp_window(self):
        self.assertTrue(is_vdp_window(0x600002))
        self.assertFalse(is_vdp_window(0x400002))

    def test_wait_is_not_completed_write(self):
        sample = BusObservation(0x600002, 0, 0, 1, 1, 1)
        self.assertEqual(classify(sample), "vdp-write-wait-sample")

    def test_ack_is_only_sampled_level(self):
        sample = BusObservation(0x600002, 0, 0, 0, 1, 0)
        self.assertEqual(classify(sample), "vdp-write-ack-levels-observed")

    def test_non_vdp_and_read(self):
        self.assertEqual(classify(BusObservation(0x200000, 0, 0, 1, 0, 1)), "non-vdp")
        self.assertEqual(classify(BusObservation(0x600002, 0, 1, 1, 1, 1)), "vdp-read-sample")

    def test_invalid_signals(self):
        with self.assertRaises(ValueError):
            classify(BusObservation(0x600002, 0, 2, 1, 1, 1))

if __name__ == "__main__":
    unittest.main()
