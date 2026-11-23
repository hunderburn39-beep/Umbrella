#!/usr/bin/env python3
"""Check invariants of the 68000 bus trace source patch without a Switch SDK."""
import unittest
from pathlib import Path

PORT = Path(__file__).with_name("port.py")

class CpuTracePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = PORT.read_text()

    def test_cpu_trace_records_flag_changes(self):
        self.assertIn("nx_addr != nx_cpu_trace_last || nx_flags != nx_cpu_trace_last_flags",self.code)
        self.assertIn("nx_cpu_trace_last_flags = nx_flags;",self.code)

    def test_partial_trace_flushed_on_timeout(self):
        self.assertIn("mcycles >= 2000000ULL",self.code)
        self.assertIn("nx_cpu_trace_n > 0",self.code)
        self.assertIn("nx_k<nx_cpu_trace_n",self.code)

    def test_no_instruction_pc_claim(self):
        self.assertIn("NOT a decoded instruction PC",self.code)

if __name__=="__main__":
    unittest.main()
