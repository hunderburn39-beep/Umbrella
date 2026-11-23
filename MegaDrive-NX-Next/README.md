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

## Z80 RAM and integration bridge
`z80_ram.py` provides an 8 KiB byte-addressed RAM reference with a modeled 8 KiB mirror and explicitly gated 68000-side access. `z80_bridge.py` connects the Z80 BUSREQ/RESET control state to RAM access for end-to-end regression tests. Grant must be externally observed; this is **not** a real Z80 core or verified VA2 arbitration. The bridge is not yet connected to `ReferenceBusController`, which remains word-only. Z80 RAM word lanes, audio peripherals and actual timing remain unimplemented. Tests are in `test_z80_ram.py` and `test_z80_bridge.py`.

## Main controller Z80 bridge integration
`ReferenceBusController` now owns a `Z80Bridge` and exposes explicit untimed control-register and Z80 RAM byte methods. They are blocked while a word bus cycle is active. The original 68000 word transaction path deliberately does not complete Z80 accesses: physical byte-lane behavior and DTACK timing have not been established. Regression tests: `test_controller_z80.py`. This is **not** CPU instruction execution or a verified 315-6123 implementation.

## VDP command-port reference
`vdp_ports.py` recognizes conventional VDP register-write control words and stages two-word control commands. The reference controller exposes `stage_vdp_control_word()` for isolated untimed tests only; its real 68000 bus-cycle path continues to wait for external DTACK and never automatically writes VDP registers. Data port, VRAM, FIFO, DMA, status bits, rasterization and VA2-specific chip behavior are not implemented. Regression tests: `test_vdp_ports.py` and `test_controller_vdp.py`.

## VRAM reference storage
`vram.py` provides a 64 KiB byte-array reference with byte/word access, address-boundary wrapping and clearing. `VDPPorts` now owns an isolated VRAM instance with explicit **diagnostic-only** read/write methods. No control-command address decoding into VRAM operations, data-port transfer, FIFO, DMA, VDP memory layout, rendering, or VA2 timing is claimed. `test_vram.py` and `test_vdp_vram.py` cover storage and verify that unacknowledged 68000 writes cannot mutate VRAM. CI execution not yet confirmed.

## VDP VRAM command transfer reference
`vdp_address.py` decodes conventional two-word VDP control commands into VRAM addresses and operation codes. `VDPPorts` now supports **reference** VRAM read/write via an active command and register 15 address auto-increment, with wraparound. These are direct Python method calls, not timed VDP FIFO operations or acknowledged 68000 bus cycles. CRAM/VSRAM, DMA, read buffering, hardware byte-swapping, rendering and VA2-specific behavior are unimplemented. Tests: `test_vdp_address.py` and `test_vdp_transfer.py`.

## 8x8 graphics patterns
`tiles.py` decodes and encodes conventional 8x8, 4bpp packed Mega Drive pattern data (32 bytes each, 2048 addressable patterns in 64 KiB). This produces palette indices 0..15, **not** RGB pixels or a rendered frame. `test_tiles.py` validates packing and bounds; `test_tile_vdp_integration.py` validates that reference VDP VRAM transfers populate patterns. Plane A/B, window, sprites, CRAM palettes, scroll, priorities, raster timing and VA2 ASIC-specific behavior remain unimplemented. Test execution in GitHub Actions is not yet confirmed.

## CRAM palette and tile diagnostics
`cram.py` stores 64 conventional Mega Drive 9-bit RGB palette entries (word mask `0x0EEE`) and maps each 3-bit channel to 8-bit RGB by a simple linear approximation. This is **not** a calibrated Genesis 3 VA2 analog output model. `VDPPorts` owns a CRAM instance with diagnostic-only palette injection. `tile_preview.py` maps 4bpp tile indices through one of four 16-color palettes and exports an 8x8 PPM image. Transparency, shadow/highlight, CRAM VDP port commands, plane composition and timing are not implemented. Tests: `test_cram.py`, `test_tile_preview.py`. GitHub Actions execution remains unverified.

## Diagnostic name-table planes
`planes.py` decodes conventional 16-bit plane name-table attributes: 11-bit pattern index, H/V flip, palette bank and priority. `DiagnosticPlane` samples a specified VRAM name-table base using 32/64/128-tile plane dimensions and resolves a pixel through the tile decoder and CRAM. It is a **direct diagnostic sampler**, not an implemented Plane A/B compositor or an ASIC renderer. Scrolling, window plane, sprite overlays, priority mixing, transparency, VDP register-controlled table addresses and scanline timing remain pending. Tests: `test_planes.py`; CI execution not yet confirmed.
