#!/usr/bin/env python3
"""Regression tests for the generated C trace audit."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AUDIT = Path(__file__).with_name("audit_generated_traces.py")
HEADER = """
static void nx_trace_flush_main(void);
static void nx_rom_trace_flush_main(void);
static void nx_trace_flush_main(void) {
    FILE *out=fopen("sdmc:/switch/Umbrella-MegaDrive-NX/cpu-bus-trace.txt","w");
}
static void nx_rom_trace_flush_main(void) {
    FILE *out=fopen("sdmc:/switch/Umbrella-MegaDrive-NX/rom-boot-trace.txt","w");
}
"""
WORKER = """
int SDLCALL work_thread(void *data) {
    if (mcycles >= 2000000ULL) {
        __atomic_store_n(&nx_cpu_trace_ready,1,__ATOMIC_RELEASE);
        __atomic_store_n(&nx_rom_trace_ready,1,__ATOMIC_RELEASE);
    }
}
void main_loop(void) {
    nx_trace_flush_main();
    nx_rom_trace_flush_main();
}
"""

class GeneratedTraceAuditTests(unittest.TestCase):
    def run_audit(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "md.c"
            path.write_text(source)
            return subprocess.run([sys.executable,str(AUDIT),str(path)],
                                  capture_output=True,text=True)

    def test_valid_worker_and_main_thread(self):
        result=self.run_audit(HEADER+WORKER)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_worker_sd_write_is_rejected(self):
        source=HEADER+WORKER.replace(
            'if (mcycles >= 2000000ULL) {',
            'FILE *f=fopen("sdmc:/switch/Umbrella-MegaDrive-NX/cpu-bus-trace.txt","w");\n'
            '    if (mcycles >= 2000000ULL) {')
        result=self.run_audit(source)
        self.assertNotEqual(result.returncode,0)

    def test_worker_fputs_is_rejected(self):
        source=HEADER+WORKER.replace(
            'if (mcycles >= 2000000ULL) {',
            'fputs("bad", stderr);\n    if (mcycles >= 2000000ULL) {')
        result=self.run_audit(source)
        self.assertNotEqual(result.returncode,0)

    def test_prototypes_without_main_calls_are_rejected(self):
        source=HEADER+WORKER.replace('    nx_trace_flush_main();','').replace(
            '    nx_rom_trace_flush_main();','')
        result=self.run_audit(source)
        self.assertNotEqual(result.returncode,0)

    def test_missing_main_thread_flush_is_rejected(self):
        result=self.run_audit(HEADER+WORKER.replace('    nx_rom_trace_flush_main();',''))
        self.assertNotEqual(result.returncode,0)

    def test_missing_forward_declaration_is_rejected(self):
        result=self.run_audit(HEADER.replace(
            'static void nx_rom_trace_flush_main(void);','')+WORKER)
        self.assertNotEqual(result.returncode,0)

if __name__=="__main__":
    unittest.main()
