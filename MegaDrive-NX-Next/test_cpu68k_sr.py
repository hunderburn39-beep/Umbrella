"""Limited 68000 supervisor SR and STOP regression tests."""
import unittest
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference


def cpu(program):
    code = bytes.fromhex(program)
    rom = bytearray(0x100 + len(code))
    rom[:4] = (0xff0000).to_bytes(4, "big")
    rom[4:8] = (0x100).to_bytes(4, "big")
    rom[0x100:] = code
    result = CPU68KReference(ReferenceBusController(bytes(rom)))
    result.reset()
    return result


class SupervisorStatusTests(unittest.TestCase):
    def test_reset_enters_supervisor_with_mask_seven(self):
        c = cpu("4e71")
        self.assertEqual(c.sr, 0x2700)

    def test_moveq_changes_ccr_not_supervisor_or_mask(self):
        c = cpu("7000")
        c.step()
        self.assertEqual(c.sr, 0x2704)

    def test_stop_supervisor_sets_sr_and_halts(self):
        c = cpu("4e72 2304 4e71")
        result = c.step()
        self.assertEqual(result.mnemonic, "STOP")
        self.assertEqual(c.sr, 0x2304)
        self.assertEqual(c.pc, 0x104)
        self.assertTrue(c.stopped)
        with self.assertRaises(RuntimeError):
            c.step()

    def test_stop_rejects_unmodeled_user_mode(self):
        c = cpu("4e72 0000")
        with self.assertRaises(NotImplementedError):
            c.step()
        self.assertFalse(c.stopped)
        self.assertEqual(c.sr, 0x2700)

    def test_reset_clears_stop_and_restores_supervisor(self):
        c = cpu("4e72 2700")
        c.step()
        c.reset()
        self.assertFalse(c.stopped)
        self.assertEqual(c.sr, 0x2700)
        self.assertEqual(c.pc, 0x100)

    def test_unmodeled_sr_bits_are_rejected(self):
        c = cpu("4e72 2780")
        with self.assertRaises(NotImplementedError):
            c.step()
        self.assertFalse(c.stopped)


if __name__ == "__main__":
    unittest.main()
