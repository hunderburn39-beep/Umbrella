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
        self.assertIn("nx_cpu_trace_n == 64 || mcycles >= 2000000ULL",self.code)
        self.assertNotIn("nx_cpu_trace_n > 0 &&",self.code)
        self.assertIn("NO ACTIVE CPU ADDRESS OBSERVED",self.code)
        self.assertIn("nx_k<nx_cpu_trace_n",self.code)

    def test_worker_handoff_uses_atomic_release_acquire(self):
        self.assertIn("__atomic_store_n(&nx_cpu_trace_ready,1,__ATOMIC_RELEASE)",self.code)
        self.assertIn("__atomic_load_n(&nx_cpu_trace_ready,__ATOMIC_ACQUIRE)",self.code)
        self.assertIn("nx_trace_flush_main();",self.code)

    def test_rom_trace_main_thread_handoff(self):
        self.assertIn("nx_rom_trace_flush_main();",self.code)
        self.assertIn("__atomic_store_n(&nx_rom_trace_ready,1,__ATOMIC_RELEASE)",self.code)
        self.assertIn("__atomic_load_n(&nx_rom_trace_ready,__ATOMIC_ACQUIRE)",self.code)
        self.assertLess(self.code.index("# V4.9:"),self.code.index("# V5.0:"))
        self.assertIn("nx_rom_n == 32 || mcycles >= 2000000ULL",self.code)
        self.assertIn("md.vaddress != nx_rom_last && !nx_rom_trace_saved",self.code)

    def test_trace_functions_declared_before_use(self):
        self.assertIn("static void nx_trace_flush_main(void);",self.code)
        self.assertIn("static void nx_rom_trace_flush_main(void);",self.code)

    def test_no_instruction_pc_claim(self):
        self.assertIn("NOT a decoded instruction PC",self.code)

if __name__=="__main__":
    unittest.main()
