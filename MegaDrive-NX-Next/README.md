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
Reference 68000 reset-vector decoder, ROM/RAM word bus, explicit active-low DTACK bus-cycle state machine and an integrated ROM/RAM reference bus controller implemented in Python, with unit tests. The bus deliberately refuses unimplemented VDP, IO and Z80 accesses. This is not a CPU executor, verified ASIC, Switch NRO or playable console. CI execution remains unverified.

## Bus handshake research
`bus_cycle.py` records requests and waits for an externally sampled DTACK low. VDP select alone never completes a transfer. The module does not generate ASIC timing or connect to a real CPU executor; it is a protocol regression harness.

## Reference bus integration
`bus_controller.py` links word-aligned ROM/RAM accesses to the DTACK state machine. ROM/RAM replies are immediate only by reference-test convention, not measured VA2 timing. VDP, Z80 and IO transactions deliberately remain unimplemented; even a supplied external ACK cannot be treated as a completed chip transaction until a responder exists. Byte-lane operations are not yet supported.

## Peripheral address selection
`peripheral_decode.py` classifies standard cartridge, Z80, IO, VDP and work RAM address regions and labels commonly used 68000 IO register addresses, including controller data/control and Z80 BUSREQ/RESET. This is a software-visible reference map, **not** verified Genesis 3 VA2 ASIC decoding. No peripheral data, register side effects, DTACK or ASIC timing are implemented. Tests: `test_peripheral_decode.py`.

## Z80 control research
`z80_control.py` models the conventional 68000-facing Z80 BUSREQ (0xA11100) and RESET (0xA11200) bit-8 control convention. Grant is an explicit external observation, never inferred from a request. This module does not execute Z80 instructions, provide bus-grant timing or integrate Z80 RAM with the main reference bus. `test_z80_control.py` covers request/grant/reset transitions. The reset-held access assumption requires confirmation against VA2 hardware behavior.
