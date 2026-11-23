import unittest
from bus_controller import ReferenceBusController
from bus_cycle import Request
from sprite_scanline import ScanlineResult
from vdp_status import SPRITE_COLLISION, SPRITE_OVERFLOW

class ControllerVDPStatusTests(unittest.TestCase):
    def setUp(self):
        self.controller = ReferenceBusController(bytes.fromhex("4e 71"))

    def test_idle_diagnostic_read(self):
        self.assertEqual(self.controller.diagnostic_read_vdp_status(0xc00004), 0)

    def test_diagnostic_latches_visible_through_controller(self):
        self.controller.vdp.diagnostic_observe_scanline(
            ScanlineResult((), True, False, True)
        )
        self.assertEqual(
            self.controller.diagnostic_read_vdp_status(0xc00004),
            SPRITE_COLLISION | SPRITE_OVERFLOW
        )

    def test_no_diagnostic_bypass_during_cycle(self):
        self.controller.begin(Request(0xc00004, True))
        with self.assertRaises(RuntimeError):
            self.controller.diagnostic_read_vdp_status(0xc00004)
        self.assertFalse(self.controller.clock())
        self.assertEqual(self.controller.finish(), (False, None))

    def test_wrong_port_rejected(self):
        with self.assertRaises(ValueError):
            self.controller.diagnostic_read_vdp_status(0xc00000)

    def test_diagnostic_read_does_not_acknowledge_vdp_bus(self):
        self.controller.diagnostic_read_vdp_status(0xc00004)
        self.controller.begin(Request(0xc00004, True))
        self.assertFalse(self.controller.clock())
        self.assertEqual(self.controller.finish(), (False, None))

    def test_frame_reset_clears_readout(self):
        self.controller.vdp.diagnostic_observe_scanline(
            ScanlineResult((), False, False, True)
        )
        self.controller.vdp.diagnostic_begin_frame()
        self.assertEqual(self.controller.diagnostic_read_vdp_status(0xc00004), 0)

if __name__ == "__main__":
    unittest.main()
