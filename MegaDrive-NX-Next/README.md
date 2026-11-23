# Mega Drive NX Next | Genesis 3 VA2

New, isolated software hardware-reconstruction project for Nintendo Switch homebrew.

## Target hardware
- Sega Genesis 3, motherboard VA2
- Main GOAC: Sega 315-6123 / Yamaha FQ8007
- Architecture differs from Mega Drive II VA4 (315-5960).
- Video/audio encoding, memory and board-level compatibility require independent evidence.

## Design rule
Reconstruct chip-level behavior and board connections, not a generic emulator frontend.
No claim of a verified transistor-level or gate-level 315-6123 model. The original Nuked-MD FC1004 model cannot be relabeled as a 315-6123.

## Baseline reuse
The previous MegaDrive-NX project supplies *diagnostic methods* only:
- 68000 word-to-byte address checks
- CPU bus and VDP acknowledgement traces
- ROM boot trace correlation
- reproducible devkitA64 CI checks
- startup checkpoints and no filesystem access from worker threads

The previous implementation, including its unresolved VDP behavior, is NOT copied as a working core.

## Milestones
1. Confirm VA2 schematics, board photos and 315-6123 bus/memory mapping.
2. Write executable reference tests for CPU address, reset, ROM and VDP transactions.
3. Create independently testable CPU, RAM, video, sound and cartridge interfaces.
4. Connect verified board timing and bus arbitration.
5. Build Switch NRO and check ELF/NRO architecture.
6. Test diagnostic ROM on Switch, then user-supplied Super Hang-On ROM.

## Status
Research scaffold created. No executable console core, no NRO, no validated gameplay.
