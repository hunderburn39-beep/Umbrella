import unittest
from bus_cycle import BusCycle, Phase, Request

class BusCycleTests(unittest.TestCase):
    def test_wait_until_explicit_dtack(self):
        cycle = BusCycle()
        cycle.start(Request(0xc00004, False, 0x8144))
        self.assertFalse(cycle.sample(as_n=0, dtack_n=1, vdp_selected=1))
        self.assertEqual(cycle.phase, Phase.WAIT)
        self.assertTrue(cycle.sample(as_n=0, dtack_n=0, vdp_selected=1))
        self.assertEqual(cycle.phase, Phase.ACKNOWLEDGED)
        self.assertTrue(cycle.release())

    def test_no_double_completion(self):
        cycle = BusCycle()
        cycle.start(Request(0x000100, True))
        self.assertTrue(cycle.sample(as_n=0, dtack_n=0))
        self.assertFalse(cycle.sample(as_n=0, dtack_n=0))
        self.assertEqual(cycle.samples, 2)

    def test_vdp_select_alone_does_not_acknowledge(self):
        cycle = BusCycle()
        cycle.start(Request(0xc00004, False))
        self.assertFalse(cycle.sample(as_n=0, dtack_n=1, vdp_selected=1))
        self.assertFalse(cycle.release())

    def test_reject_overlapping_cycle(self):
        cycle = BusCycle()
        cycle.start(Request(0, True))
        with self.assertRaises(RuntimeError):
            cycle.start(Request(2, True))

    def test_reject_inactive_strobe(self):
        cycle = BusCycle()
        cycle.start(Request(0, True))
        with self.assertRaises(RuntimeError):
            cycle.sample(as_n=1, dtack_n=0)

    def test_reject_invalid_signal(self):
        cycle = BusCycle()
        cycle.start(Request(0, True))
        with self.assertRaises(ValueError):
            cycle.sample(as_n=0, dtack_n=2)

    def test_odd_upper_lane_rejected(self):
        with self.assertRaises(ValueError):
            Request(1, True, upper=True, lower=False)

    def test_lower_byte_lane(self):
        self.assertEqual(Request(1, True, upper=False, lower=True).address, 1)

    def test_release_idle_rejected(self):
        with self.assertRaises(RuntimeError):
            BusCycle().release()

if __name__ == "__main__":
    unittest.main()
