#!/usr/bin/env python3
"""Validate the *generated* Nuked-MD md.c, not merely port.py text."""
import sys
from pathlib import Path

def main(path):
    source = Path(path).read_text()
    errors=[]
    marker="int SDLCALL work_thread(void *data)"
    if source.count(marker)!=1:
        errors.append("Expected exactly one worker entry point")
    else:
        worker=source.split(marker,1)[1]
        # The worker ends at the next top-level function; use a known
        # main-thread flush definition to verify placement separately.
        for needle in ('fopen("sdmc:/switch/Umbrella-MegaDrive-NX/cpu-bus-trace.txt"',
                       'fopen("sdmc:/switch/Umbrella-MegaDrive-NX/rom-boot-trace.txt"'):
            if needle in worker:
                errors.append("SD trace write remains after worker entry: "+needle)
    for name in ("nx_trace_flush_main","nx_rom_trace_flush_main"):
        if source.count(name+"();")<1:
            errors.append("Missing main-thread call: "+name)
    for token in ("__atomic_store_n(&nx_cpu_trace_ready,1,__ATOMIC_RELEASE)",
                  "__atomic_store_n(&nx_rom_trace_ready,1,__ATOMIC_RELEASE)",
                  "mcycles >= 2000000ULL"):
        if token not in source:
            errors.append("Missing generated trace guard: "+token)
    for error in errors:
        print("ERROR:",error)
    if errors:
        return 1
    print("Generated trace audit OK: main-thread flush and worker handoff present.")
    return 0

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("Usage: python3 audit_generated_traces.py build/md.c")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
