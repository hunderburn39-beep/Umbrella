"""Explicit, untimed 68000 autovector interrupt reference tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference


def cpu():
    rom = bytearray(0x140)
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:0x108] = bytes.fromhex("4e72 2000 4e71 4e71")
    rom[0x120:0x122] = bytes.fromhex("4e73")
    for level in (2, 4, 6):
        offset = (24 + level) * 4
        rom[offset:offset + 4] = (0x120).to_bytes(4, "big")
    c = CPU68KReference(ReferenceBusController(bytes(rom)))
    c.reset()
    return c


class AutovectorIRQTests(unittest.TestCase):
    def test_reset_mask_blocks_level_six(self):
        c = cpu()
        self.assertFalse(c.service_autovector_irq_reference(6))
        self.assertEqual(c.pc, 0x100)
        self.assertEqual(c.a[7], 0xff0000)

    def test_stop_unmasked_irq_wakes_and_rte_restores(self):
        c = cpu()
        c.step()  # STOP #$2000 enables interrupts and halts.
        self.assertTrue(c.stopped)
        self.assertTrue(c.service_autovector_irq_reference(4))
        self.assertFalse(c.stopped)
        self.assertEqual(c.pc, 0x120)
        self.assertEqual(c.sr, 0x2400)
        self.assertEqual(c.bus.memory.read_word(0xfefffa), 0x2000)
        self.assertEqual(c.bus.memory.read_word(0xfefffe), 0x104)
        self.assertEqual(c.step().mnemonic, "RTE")
        self.assertEqual(c.pc, 0x104)
        self.assertEqual(c.sr, 0x2000)
        self.assertEqual(c.a[7], 0xff0000)
        self.assertEqual(c.step().mnemonic, "NOP")

    def test_equal_or_lower_irq_masked_inside_handler(self):
        c = cpu()
        c.step()
        self.assertTrue(c.service_autovector_irq_reference(4))
        self.assertFalse(c.service_autovector_irq_reference(4))
        self.assertFalse(c.service_autovector_irq_reference(2))
        self.assertEqual(c.a[7], 0xfefffa)

    def test_higher_level_can_nest(self):
        c = cpu()
        c.step()
        self.assertTrue(c.service_autovector_irq_reference(2))
        self.assertTrue(c.service_autovector_irq_reference(6))
        self.assertEqual(c.sr, 0x2600)
        self.assertEqual(c.a[7], 0xfefff4)
        c.step()
        self.assertEqual(c.sr, 0x2200)
        c.step()
        self.assertEqual(c.sr, 0x2000)
        self.assertEqual(c.pc, 0x104)

    def test_invalid_irq_levels_rejected(self):
        c = cpu()
        for level in (0, 7, -1, 8, True):
            with self.subTest(level=level):
                with self.assertRaises(ValueError):
                    c.service_autovector_irq_reference(level)


if __name__ == "__main__":
    unittest.main()
