#!/usr/bin/env python3
"""Regression checks for Switch CPU bus capture decoder."""
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from analyse_cpu_bus_trace import analyse

class CpuBusTraceTests(unittest.TestCase):
    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"cpu-bus-trace.txt"
            p.write_text("CPU bus address transitions\n"+rows)
            out=StringIO()
            with redirect_stdout(out):
                rc=analyse(p)
            return rc,out.getvalue()

    def test_vdp_write_and_io_read(self):
        rc,out=self.run_rows(
            "00 508000 A10000 0000 00\n"
            "01 600002 C00004 8F02 03\n")
        self.assertEqual(rc,0)
        self.assertIn("IO",out)
        self.assertIn("VDP",out)
        self.assertIn("WRITE",out)
        self.assertIn("data is the CPU output bus",out)

    def test_bad_address(self):
        rc,out=self.run_rows("00 600002 C00006 8F02 03\n")
        self.assertEqual(rc,1)
        self.assertIn("mismatch",out)

    def test_no_vdp_write_is_not_proof(self):
        rc,out=self.run_rows("00 000000 000000 0000 00\n")
        self.assertEqual(rc,0)
        self.assertIn("NOT proof",out)

if __name__=="__main__":
    unittest.main()
