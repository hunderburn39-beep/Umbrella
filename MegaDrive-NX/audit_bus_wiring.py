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
    "FC1004 video clock reaches motherboard":
        "md.vclk = ym.o_vclk;",
    "Motherboard video clock reaches FC1004":
        "ym.i_vclk = md.vclk;",
    "Motherboard reset reaches 68000":
        "m68k.input.i_reset = md.reset;",
    "Motherboard reset reaches 68000 after chip arbitration":
        "md.reset = ym.o_reset;",
    "68000 clock depends on board video clock":
        "if (!md.vclk)",
    "VDP pixel clock advances renderer":
        "Video_PlotVDP();",
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
# Cartridge must be a real participant on the 68000 motherboard bus.
cart_upstream = (root / "third_party" / "Nuked-MD" / "cartridge.c").read_text()
cart_ported = (root / "build" / "cartridge.c").read_text()
cart_checks = {
    "Cartridge ROM loader": "romfile = fopen(filename, \"rb\");",
    "Cartridge ROM word conversion": "rom[i] = short_swap(rom[i]);",
    "Cartridge chip enable": "if (!ym.o_ce0)",
    "Cartridge read strobe": "if (!ym.o_cas0)",
    "Cartridge ROM data reaches motherboard": "md.vdata = rom[md.vaddress & 0x1fffff];",
}
for label, snippet in cart_checks.items():
    ok = snippet in cart_upstream and snippet in cart_ported
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    if not ok:
        failures.append(label)
# Verify the full cartridge-to-CPU read path, including CPU input data.
cart_cpu_checks = {
    "Cartridge handler invoked on MD board": "cart_handle_md();",
    "Motherboard ROM word enters 68000 input": "m68k.input.i_data = md.vdata & 0xffff;",
    "68000 executes a clock edge": "M68K_Clock2(&m68k, 1, 0);",
    "68000 executes opposite clock edge": "M68K_Clock2(&m68k, 0, 1);",
}
for label, snippet in cart_cpu_checks.items():
    ok = snippet in a and snippet in b
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    if not ok:
        failures.append(label)
# The two HUD counters previously disagreed although they should count
# the exact same VDP selection event. Verify the generated C, not port.py.
import re
sel_blocks = re.findall(
    r"if\s*\(ym\.vdp\.input\.i_sel0\s*&&\s*!ym\.vdp\.input\.i_as\)\s*\{([^}]*)\}",
    b, re.S,
)
shared = len(sel_blocks) == 1 and all(
    sel_blocks[0].count(token) == 1
    for token in ("nx_sel_samples++;", "nx_chip_select_seen++;")
)
print(f"{'PASS' if shared else 'FAIL'}: CHIP and SEL increment inside one identical VDP event")
if not shared:
    failures.append("CHIP and SEL sample mismatch")
print("RESULT:", "FAIL" if failures else "PASS", "| Static wiring only; Switch hardware test required")
if failures:
    raise SystemExit(1)
