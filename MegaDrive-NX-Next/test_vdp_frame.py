import unittest
from tiles import encode_tile
from vdp_ports import VDPPorts
from vdp_frame import evaluate_diagnostic_frame
from vdp_status import SPRITE_COLLISION, SPRITE_OVERFLOW

class DiagnosticFrameTests(unittest.TestCase):
    def setUp(self):
        self.vdp = VDPPorts()
        self.sat = 0xd000
        encode_tile(self.vdp.vram, 1, [[1] * 8 for _ in range(8)])

    def entry(self, index, x=0, y=0, link=0, pattern=1):
        addr = self.sat + index * 8
        for n, value in enumerate((y + 128, link, pattern, x + 128)):
            self.vdp.vram.write_word(addr + n * 2, value)

    def test_empty_frame(self):
        self.entry(0, y=300)
        result = evaluate_diagnostic_frame(self.vdp, self.sat)
        self.assertEqual(result.status_word, 0)
        self.assertEqual(result.collision_lines, ())

    def test_collision_latched_across_visible_lines(self):
        self.entry(0, y=10, link=1)
        self.entry(1, y=10)
        result = evaluate_diagnostic_frame(self.vdp, self.sat, 256)
        self.assertEqual(result.collision_lines, tuple(range(10, 18)))
        self.assertEqual(result.status_word, SPRITE_COLLISION)
        self.assertEqual(self.vdp.diagnostic_status_word(), SPRITE_COLLISION)

    def test_frame_start_resets_previous_latches(self):
        self.entry(0, link=1)
        self.entry(1)
        self.assertEqual(evaluate_diagnostic_frame(self.vdp, self.sat).status_word, SPRITE_COLLISION)
        self.entry(0, y=300, link=0)
        self.assertEqual(evaluate_diagnostic_frame(self.vdp, self.sat).status_word, 0)

    def test_sprite_overflow(self):
        for i in range(17):
            self.entry(i, x=i * 8, link=i + 1 if i < 16 else 0)
        result = evaluate_diagnostic_frame(self.vdp, self.sat, 256)
        self.assertEqual(result.sprite_overflow_lines, tuple(range(8)))
        self.assertTrue(result.status_word & SPRITE_OVERFLOW)

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            evaluate_diagnostic_frame(self.vdp, self.sat, 300)
        with self.assertRaises(ValueError):
            evaluate_diagnostic_frame(self.vdp, self.sat, 320, 200)

    def test_cpu_status_remains_unimplemented(self):
        self.entry(0, link=1)
        self.entry(1)
        evaluate_diagnostic_frame(self.vdp, self.sat)
        with self.assertRaises(NotImplementedError):
            self.vdp.read_status()

if __name__ == "__main__":
    unittest.main()
