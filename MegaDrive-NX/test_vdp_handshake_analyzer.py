"""Regression tests for the read-only VDP handshake trace analyzer."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from analyze_vdp_handshake import analyze

HEADER = "Samples: 8; last master clock: 80\nclock addr data cpu_as cpu_rw board_dtack vdp_sel vdp_ack reg_disp reg_m5\n"
ROWS = [
"10 600002 8004 0 0 1 1 1 0 0",
"16 600002 8004 0 0 1 1 0 0 0",
"17 600002 8004 0 0 0 1 0 0 0",
"30 600002 8104 0 0 1 1 1 0 0",
"36 600002 8104 0 0 1 1 0 0 0",
"37 600002 8104 0 0 0 1 0 0",
"70 600002 8144 0 0 1 1 1 0 1",
"80 600002 8144 0 0 0 1 0 1",
]

class HandshakeTest(unittest.TestCase):
    def test_register_decode_and_ack_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.txt"
            path.write_text(HEADER + "\n".join(ROWS) + "\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                analyze(path)
            result = out.getvalue()
            self.assertIn("Samples: 8", result)
            self.assertIn("Register 1 commands: [(30, '0x4'), (70, '0x44')]", result)
            self.assertIn("Display-enable command observed: True", result)
            self.assertIn("VDP ACK falling edges: 3", result)
            self.assertIn("Board DTACK falling edges: 3", result)
            self.assertIn("Display signal ever enabled: False", result)

    def test_real_capture_shape_and_register_sequence(self):
        # Representative state changes from the Switch capture, not completed writes.
        rows = [
            "1389582 600002 4741 0 0 1 1 1 0 0",
            "1389590 600002 8004 0 0 1 1 1 0 0",
            "1389596 600002 8004 0 0 1 1 0 0 0",
            "1389870 600002 8104 0 0 1 1 1 0 0",
            "1389876 600002 8104 0 0 1 1 0 0 1",
            "1396093 600002 9700 0 0 0 1 0 0 1",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.txt"
            path.write_text(
                "Samples: 6; last master clock: 1396093\n"
                + "clock addr data cpu_as cpu_rw board_dtack vdp_sel vdp_ack reg_disp reg_m5\n"
                + "\n".join(rows) + "\n",
                encoding="utf-8",
            )
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                analyze(path)
            result = out.getvalue()
            self.assertIn("Display-enable command observed: False", result)
            self.assertIn("Display signal ever enabled: False", result)
            self.assertIn("Last candidate: 0x9700", result)

if __name__ == "__main__":
    unittest.main()
