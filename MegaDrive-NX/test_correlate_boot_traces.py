#!/usr/bin/env python3
"""Tests for CPU/ROM trace correlation without Switch hardware."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from correlate_boot_traces import analyse, parse, CPU_ROW, ROM_ROW


class CorrelationTests(unittest.TestCase):
    def test_shared_addresses_and_io_write(self):
        with tempfile.TemporaryDirectory() as directory:
            cpu = Path(directory) / "cpu.txt"
            rom = Path(directory) / "rom.txt"
            cpu.write_text(
                "00 000002 000004 6BAC 02\n"
                "01 0035D6 006BAC 7000 02\n"
                "02 500002 A00004 1234 01\n"
                "03 600002 C00004 0000 03\n"
            )
            rom.write_text("00 000002 000004 0000\n01 0035D6 006BAC 7000\n")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(analyse(cpu, rom), 0)
            self.assertIn("Matching CPU-read and ROM-read byte addresses: 2", output.getvalue())
            self.assertIn("VDP control port [C00004]: CPU reads=0, writes=1", output.getvalue())

    def test_inconsistent_word_address_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rom.txt"
            path.write_text("00 000002 000006 7000\n")
            with self.assertRaises(ValueError):
                parse(path, ROM_ROW)

    def test_empty_traces_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            cpu = Path(directory) / "cpu.txt"
            rom = Path(directory) / "rom.txt"
            cpu.write_text("Captured entries: 0\n")
            rom.write_text("Captured cartridge reads: 0 / 32\n")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(analyse(cpu, rom), 0)
            self.assertIn("no address transitions", output.getvalue())
            self.assertIn("no reads recorded", output.getvalue())


if __name__ == "__main__":
    unittest.main()
