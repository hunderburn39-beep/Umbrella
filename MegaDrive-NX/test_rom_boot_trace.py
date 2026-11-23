#!/usr/bin/env python3
"""Regression tests for captured Mega Drive cartridge boot reads."""
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from analyse_rom_boot_trace import analyse

HEADER = "Cartridge reads: word address, byte address, ROM data\n"
ROWS = [
    (0,0x000000,0x00FF),(1,0x000001,0x0200),
    (2,0x000002,0x0000),(3,0x000003,0x6BAC),
    (4,0x0035D6,0x7000),(5,0x0035D7,0x1039),
    (6,0x0035D8,0x00A1),(7,0x0035D9,0x0001),
    (8,0x0035DA,0x3200),(9,0x0035DB,0x0240),
    (10,0x0035DC,0x000F),(11,0x0035DD,0x670A),
    (12,0x0035DE,0x23FC),(13,0x0035DF,0x5345),
    (14,0x0035E0,0x4741),(15,0x0035E1,0x00A1),
    (16,0x0035E2,0x4000)
]

def make_trace(rows):
    return HEADER+"".join(f"{seq:02d} {addr:06X} {addr*2:06X} {word:04X}\n" for seq,addr,word in rows)

class BootTraceTests(unittest.TestCase):
    def run_trace(self, trace):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"trace.txt"
            p.write_text(trace)
            out=StringIO()
            with redirect_stdout(out):
                rc=analyse(p)
            return rc,out.getvalue()

    def test_vectors_and_tmss_instruction(self):
        rc,out=self.run_trace(make_trace(ROWS))
        self.assertEqual(rc,0)
        self.assertIn("0x00FF0200",out)
        self.assertIn("0x00006BAC",out)
        self.assertIn("0x6bbc",out.lower())
        self.assertIn("target 0x006BC6",out)
        self.assertIn("A10001 & 0x0F",out)
        self.assertIn("neither the A10001 read result",out)
        self.assertIn("not an instruction-execution",out)

    def test_invalid_byte_address(self):
        trace=make_trace(ROWS).replace("00 000000 000000 00FF","00 000000 000002 00FF")
        rc,out=self.run_trace(trace)
        self.assertEqual(rc,1)
        self.assertIn("mismatch",out)

    def test_missing_vectors(self):
        rc,out=self.run_trace(make_trace(ROWS[4:]))
        self.assertEqual(rc,0)
        self.assertIn("Incomplete initial vector reads",out)

if __name__=="__main__":
    unittest.main()
