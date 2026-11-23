"""Explicit VDP event to CPU IRQ bridge tests (not hardware timing)."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference
from vdp_irq_bridge import deliver_vdp_event_reference


def cpu():
    rom = bytearray(0x140)
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x106] = bytes.fromhex("4e72 2000 4e71")
    rom[0x120:0x122] = bytes.fromhex("4e73")
    for level in (4, 6):
        offset = (24 + level) * 4
        rom[offset:offset + 4] = (0x120).to_bytes(4, "big")
    c = CPU68KReference(ReferenceBusController(bytes(rom)))
    c.reset()
    return c


class VDPIRQBridgeTests(unittest.TestCase):
    def test_vblank_blocked_by_reset_mask(self):
        c = cpu()
        result = deliver_vdp_event_reference(c, "vblank", enabled=True)
        self.assertEqual(result.level, 6)
        self.assertFalse(result.accepted)
        self.assertEqual(c.pc, 0x100)

    def test_vblank_wakes_stopped_cpu_and_returns(self):
        c = cpu()
        c.step()
        result = deliver_vdp_event_reference(c, "vblank", enabled=True)
        self.assertTrue(result.accepted)
        self.assertFalse(c.stopped)
        self.assertEqual(c.sr, 0x2600)
        self.assertEqual(c.pc, 0x120)
        c.step()
        self.assertEqual(c.sr, 0x2000)
        self.assertEqual(c.pc, 0x104)

    def test_hblank_level_four_and_masked_inside_vblank(self):
        c = cpu()
        c.step()
        first = deliver_vdp_event_reference(c, "vblank", enabled=True)
        second = deliver_vdp_event_reference(c, "hblank", enabled=True)
        self.assertTrue(first.accepted)
        self.assertEqual(second.level, 4)
        self.assertFalse(second.accepted)
        self.assertEqual(c.a[7], 0xfefffa)

    def test_disabled_event_never_delivered(self):
        c = cpu()
        c.step()
        result = deliver_vdp_event_reference(c, "hblank", enabled=False)
        self.assertFalse(result.enabled)
        self.assertFalse(result.accepted)
        self.assertTrue(c.stopped)

    def test_rejects_invalid_event_and_non_boolean_enable(self):
        c = cpu()
        with self.assertRaises(ValueError):
            deliver_vdp_event_reference(c, "collision", enabled=True)
        with self.assertRaises(ValueError):
            deliver_vdp_event_reference(c, "vblank", enabled=1)


if __name__ == "__main__":
    unittest.main()
