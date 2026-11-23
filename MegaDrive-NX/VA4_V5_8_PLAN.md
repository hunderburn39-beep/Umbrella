# Mega Drive NX V5.8: Model 2 VA4 investigation

Status: isolated research branch, **not a working VA4 simulation**.

## Goal
Evaluate a late Mega Drive Model 2 VA4 board profile without changing the existing V5.7 implementation or claiming that a new board revision fixes the VDP issue.

## Important architectural distinction
The current Switch build is a software simulation based on pinned Nuked-MD source, not an FPGA or a physical recreation of the board. The existing code clocks discrete modeled modules (68k, Z80, VDP, FC1004, VRAM, FM, etc.). Selecting VA4 does not automatically replace these modules with a verified ASIC 315-5960 model.

## Acceptance criteria
1. Document VA4 ASIC identification and pin-level behavior using verifiable board schematics and photographs.
2. Audit the current Nuked-MD module boundaries, clock domains, bus arbitration, TMSS, cartridge mapping, and VDP handshake.
3. Implement a selectable board profile only where hardware behavior is independently substantiated.
4. Add regression tests comparing old and new profiles against the same diagnostic ROM and Super Hang-On boot traces.
5. Build an AArch64 NRO, inspect logs and NRO header, then validate startup and graphics on real Switch hardware.
6. Record cycle rate, first video frame, failure stage, and any mismatch. Do not claim playable performance without measurement.

## Current limitations
- No confirmed VA4-specific model or performance improvement.
- Super Hang-On game ROM must be provided separately from a lawful source.
- V5.7 build failures must be diagnosed independently; board profile changes do not fix CI errors by themselves.
- This branch is deliberately isolated from main and does not publish a new release.

## Next implementation step
Inspect `MegaDrive-NX/port.py`, generated `md.c`, the VDP handshake trace and the CI failure logs before editing clock or wiring logic.
