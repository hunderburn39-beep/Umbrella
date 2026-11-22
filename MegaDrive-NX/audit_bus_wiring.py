#!/usr/bin/env python3
"""Compare critical Mega Drive bus wiring in pinned upstream and Switch port.

This is a static regression audit, not proof of electrical timing correctness.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
upstream = root / "third_party" / "Nuked-MD" / "md.c"
patched = root / "build" / "md.c"
if not upstream.is_file() or not patched.is_file():
    raise SystemExit("Expected upstream and patched md.c. Run build.sh first.")
a = upstream.read_text()
b = patched.read_text()
checks = {
    "CPU address directly drives motherboard word-address bus":
        "md.vaddress = m68k.o_address;",
    "Board address is forwarded to FC1004":
        "ym.i_vaddress = md.vaddress;",
    "Board address strobe is forwarded to FC1004":
        "ym.i_as = md.as;",
    "Board write/read is forwarded to FC1004":
        "ym.i_rw = md.rw;",
    "Board byte strobes are forwarded to FC1004":
        "ym.i_uds = md.uds;",
    "Board low byte strobe is forwarded to FC1004":
        "ym.i_lds = md.lds;",
    "FC1004 clock is executed":
        "FC1004_Clock(&ym, mcycles & 1, mcycles);",
    "Board acknowledge reaches CPU":
        "m68k.input.i_dtack = md.dtack;",
}
failures = []
for label, snippet in checks.items():
    original = snippet in a
    ported = snippet in b
    print(f"{'PASS' if original and ported else 'FAIL'}: {label} (upstream={original}, port={ported})")
    if not (original and ported):
        failures.append(label)
# These probes must not be confused with confirmed write transactions.
for label, snippet in {
    "CPU/BOARD/CHIP diagnostic": "nx_decode_publish(nx_cpu_write_seen,nx_board_write_seen,nx_chip_select_seen);",
    "SEL/STB/RDY diagnostic": "nx_handshake_publish(nx_sel_samples,nx_strobe_samples,nx_ready_samples);",
}.items():
    ok = snippet in b
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    if not ok:
        failures.append(label)
print("RESULT:", "FAIL" if failures else "PASS", "| Static wiring only; Switch hardware test required")
if failures:
    raise SystemExit(1)
