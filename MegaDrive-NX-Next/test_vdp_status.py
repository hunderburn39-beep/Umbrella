import unittest
from vdp_status import DiagnosticVDPStatus, SPRITE_COLLISION, SPRITE_OVERFLOW
from sprite_scanline import ScanlineResult
from vdp_ports import VDPPorts

class VDPStatusTests(unittest.TestCase):
    def test_empty_status(self):
        self.assertEqual(DiagnosticVDPStatus().word(), 0)

    def test_collision_bit(self):
        s = DiagnosticVDPStatus()
        s.observe(ScanlineResult((), False, False, True))
        self.assertEqual(s.word(), SPRITE_COLLISION)

    def test_overflow_bit_from_sprite_count(self):
        s = DiagnosticVDPStatus()
        s.observe(ScanlineResult((), True, False, False))
        self.assertEqual(s.word(), SPRITE_OVERFLOW)

    def test_overflow_bit_from_cell_budget(self):
        s = DiagnosticVDPStatus()
        s.observe(ScanlineResult((), False, True, False))
        self.assertEqual(s.word(), SPRITE_OVERFLOW)

    def test_latched_across_scanlines(self):
        s = DiagnosticVDPStatus()
        s.observe(ScanlineResult((), False, False, True))
        s.observe(ScanlineResult((), True, False, False))
        s.observe(ScanlineResult((), False, False, False))
        self.assertEqual(s.word(), SPRITE_COLLISION | SPRITE_OVERFLOW)

    def test_frame_reset(self):
        s = DiagnosticVDPStatus(True, True)
        s.begin_frame()
        self.assertEqual(s.word(), 0)

    def test_port_diagnostic_only(self):
        v = VDPPorts()
        v.diagnostic_observe_scanline(ScanlineResult((), False, False, True))
        self.assertEqual(v.diagnostic_status_word(), SPRITE_COLLISION)
        with self.assertRaises(NotImplementedError):
            v.read_status()

    def test_port_reset_clears_diagnostic_latches(self):
        v = VDPPorts()
        v.diagnostic_observe_scanline(ScanlineResult((), True, False, False))
        v.reset()
        self.assertEqual(v.diagnostic_status_word(), 0)

if __name__ == "__main__":
    unittest.main()
