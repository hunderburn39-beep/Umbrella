"""Synthetic VDP scanline scheduling and 68000 IRQ integration tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference
from vdp_ports import VDPPorts
from vdp_scanline_reference import VDPScanlineReference


def cpu():
    rom = bytearray(0x140)
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x106] = bytes.fromhex("4e72 2000 4e71")
    rom[0x120:0x122] = bytes.fromhex("4e73")
    for level in (4, 6):
        offset = (24 + level) * 4
        rom[offset:offset + 4] = (0x120).to_bytes(4, "big")
    result = CPU68KReference(ReferenceBusController(bytes(rom)))
    result.reset()
    return result


class VDPScanlineReferenceTests(unittest.TestCase):
    def test_vblank_at_first_nonvisible_line(self):
        c, v = cpu(), VDPPorts()
        v.registers[1] = 0x20
        c.step()
        scheduler = VDPScanlineReference(visible_lines=224, total_lines=262)
        for _ in range(224):
            self.assertFalse(scheduler.tick(c, v).events)
        event = scheduler.tick(c, v)
        self.assertEqual(event.line, 224)
        self.assertEqual(event.events[0].level, 6)
        self.assertTrue(event.events[0].accepted)
        self.assertEqual(c.pc, 0x120)

    def test_hblank_counter_reload_and_mask(self):
        c, v = cpu(), VDPPorts()
        v.registers[0] = 0x10
        v.registers[10] = 2
        c.step()
        scheduler = VDPScanlineReference()
        first = scheduler.tick(c, v)
        self.assertEqual(first.events[0].level, 4)
        self.assertTrue(first.events[0].accepted)
        self.assertFalse(scheduler.tick(c, v).events)
        self.assertFalse(scheduler.tick(c, v).events)
        third = scheduler.tick(c, v)
        self.assertEqual(third.line, 3)
        self.assertFalse(third.events[0].accepted)

    def test_disabled_registers_do_not_inject(self):
        c, v = cpu(), VDPPorts()
        scheduler = VDPScanlineReference()
        for _ in range(263):
            self.assertFalse(scheduler.tick(c, v).events)
        self.assertEqual(scheduler.frame, 1)
        self.assertEqual(scheduler.line, 1)

    def test_frame_rollover_and_h_counter_reset(self):
        c, v = cpu(), VDPPorts()
        v.registers[10] = 7
        scheduler = VDPScanlineReference(total_lines=225)
        for _ in range(225):
            scheduler.tick(c, v)
        self.assertEqual((scheduler.frame, scheduler.line, scheduler.h_counter), (1, 0, 0))

    def test_invalid_geometry_rejected(self):
        with self.assertRaises(ValueError):
            VDPScanlineReference(visible_lines=200)
        with self.assertRaises(ValueError):
            VDPScanlineReference(visible_lines=240, total_lines=240)


if __name__ == "__main__":
    unittest.main()
