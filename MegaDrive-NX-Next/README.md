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

## Plane A/B diagnostic composition
`compositor.py` combines two `DiagnosticPlane` samplers using a simplified conventional priority order (A high, B high, A low, B low, backdrop) and treats color index 0 as transparent. It produces RGB rows and PPM bytes, **not** a hardware-timed frame. `demo_frame.py` creates a synthetic 64x64 PPM diagnostic frame from patterns and name tables; it is not ROM-driven. `test_compositor.py` covers transparency, ordering, backdrop and PPM size. Scroll, sprites, window plane, backdrop register wiring, shadow/highlight and 315-6123 timing remain unimplemented. Test execution not yet verified.

## Diagnostic full-plane scrolling
`scroll.py` implements independent signed horizontal/vertical pixel offsets for each diagnostic plane, wrapping at the plane dimensions. `DiagnosticCompositor` now accepts `scroll_a` and `scroll_b` offsets. This is **not** register-driven Mega Drive line scrolling or column scrolling, and sign conventions still require trace-based validation. `test_scroll.py` covers X/Y shifts, wrapping and independent planes. Sprite attribute tables, sprite mixing, real VDP timing and Switch NRO remain pending. GitHub Actions execution not confirmed.

## Diagnostic sprite attribute table
`sprites.py` decodes conventional 8-byte SAT entries (9-bit X/Y with 128-pixel bias), tile dimensions, palette, H/V flip, priority, pattern index and linked-list traversal. It samples individual sprite pixels with column-major pattern ordering and transparent color index 0. `test_sprites.py` contains reference tests for attributes, links, positions and pattern layout. **Not yet integrated into the A/B compositor.** Hardware sprite-per-line limits, collision/masking, priority interactions, sprite cache and VA2 timing remain unimplemented. GitHub Actions execution remains unverified.

## Diagnostic sprite and plane composition
`DiagnosticCompositor` now optionally accepts `sprite_table_base` and samples the SAT-linked sprites alongside scrolled planes A/B. The reference ordering is high sprite > high A > high B > low sprite > low A > low B > backdrop. Sprite pixel index zero is transparent, and earlier SAT entries win equal-priority overlaps. `test_sprite_compositor.py` covers these cases. **This remains a simplified diagnostic**, not a verified hardware pixel pipeline: sprite per-line limits, collision flags, masking, window plane, shadow/highlight, VDP timing and Switch NRO are not implemented. GitHub Actions results are not verified.

## Sprite scanline diagnostics
`sprite_scanline.py` evaluates linked SAT sprites on a specified scanline, using conventional reference budgets of 16 sprites / 32 sprite cells in H32 and 20 sprites / 40 cells in H40. It reports count/cell overflow and visible overlapping nonzero sprite pixels. The compositor can optionally enable scanline filtering with `sprite_scanline_width=256` or `320` alongside `sprite_table_base`. `test_sprite_scanline.py` tests nine cases. **Limitations:** collision and overflow flags are not connected to a VDP status register, sprite masking and hardware fetch timing are not modeled, and the 315-6123 VA2 implementation is not independently validated. CI results have not been checked.

## Diagnostic VDP sprite status latches
`vdp_status.py` tracks conventional sprite collision (bit 5, `0x0020`) and overflow (bit 6, `0x0040`) based on `ScanlineResult`. `VDPPorts.diagnostic_observe_scanline`, `diagnostic_status_word`, and `diagnostic_begin_frame` expose explicit diagnostic operations; `reset` clears these latches. **Important:** `read_status()` still raises `NotImplementedError`, since actual CPU-visible status needs a verified timing/FIFO/status model. Scanline evaluation is not automatically driven by CPU execution. Eight tests in `test_vdp_status.py` cover latching, clearing, and separation from hardware status. GitHub Actions results not verified.

## Explicit diagnostic frame evaluation
`vdp_frame.py` adds `evaluate_diagnostic_frame(vdp, sat_base, width, height)`. It clears the diagnostic latches at frame start, evaluates each visible scanline with the existing sprite scanline model, records line numbers for collision/count overflow/cell overflow, and exposes the resulting diagnostic status word. Widths 256/320 and heights 224/240 are accepted. `test_vdp_frame.py` provides six reference tests. This is **not a clocked video frame**, is not driven by the Motorola 68000, does not decode SAT base from VDP registers, and does not make `VDPPorts.read_status()` CPU-readable. GitHub Actions execution has not been verified.

## Guarded VDP diagnostic read through bus controller
`ReferenceBusController.diagnostic_read_vdp_status(0xC00004)` exposes the accumulated diagnostic sprite collision/overflow bits only when the reference bus is idle. It rejects other ports and cannot be used during an active cycle. `test_controller_vdp_status.py` covers six cases, including that the real 68000 VDP read path still stalls without an implemented responder and DTACK. **This is a diagnostic inspection API, not a CPU-visible VDP status read.** Timing, FIFO, status semantics and physical 315-6123 behavior remain unverified; test execution has not been confirmed.

## Externally gated VDP reference bus transfers
`ReferenceBusController.clock_vdp_reference(ready=...)` is an **opt-in** reference transaction path for canonical 16-bit VDP control/data ports. `ready=False` leaves the cycle waiting; `ready=True` allows staged control writes and VRAM data reads/writes if an appropriate command is active. A completed transaction cannot be applied twice. The normal `clock()` still never fabricates VDP DTACK. CPU-visible status reads remain explicitly unimplemented. `test_vdp_bus_reference.py` adds nine cases. This is not verified VDP response timing, FIFO, DMA or an operational 68000 CPU core. GitHub Actions execution not yet verified.

## Minimal Motorola 68000 instruction reference
`cpu68k_reference.py` adds a deliberately narrow instruction-level harness: reset-vector initialization, 16-bit instruction fetches via the reference bus controller, NOP, MOVEQ and BRA with 8/16-bit displacements. Unsupported opcodes raise `NotImplementedError`; STOP is explicitly not modeled without supervisor/status-register semantics. `test_cpu68k_reference.py` adds ten tests. **This is not a full 68000 CPU, cannot boot a commercial Mega Drive ROM, and does not execute VDP transactions from CPU instructions.** CI test execution has not been confirmed.

## Selected 68000 MOVE.W bus writes
`cpu68k_reference.py` now implements `MOVE.W #imm,(abs.l)` (`0x33FC`) and `MOVE.W Dn,(abs.l)` (`0x33C0..0x33C7`) in addition to the previous minimal instructions. The CPU harness sends word writes to work RAM through the reference bus, and to canonical VDP data/control ports through the opt-in `clock_vdp_reference` path only when `cpu.vdp_ready=True` is explicitly configured. Without readiness, VDP writes remain unacknowledged. `test_cpu68k_move.py` adds seven test scenarios, including a short program that stages a VDP VRAM-write command and writes a word. This is an instruction subset, not commercial ROM execution or verified 315-6123 timing. Tests were added but their execution has not been confirmed.

## CPU word reads and register destinations
`CPU68KReference.read_word(address)` performs an explicit 16-bit bus transaction with cleanup on unsupported or unacknowledged reads. `MOVE.W (abs.l),Dn` and `MOVE.W #imm,Dn` preserve the upper 16 bits of destination Dn, and permit a CPU-driven RAM write/read round trip. Canonical VDP data reads remain opt-in through `cpu.vdp_ready=True`; VDP status and other unimplemented peripheral reads still fail explicitly. `test_cpu68k_read.py` adds eight tests. This is a partial 68000 instruction harness, not full ROM boot, clocked VDP, or validated Genesis 3 VA2 silicon. Automated test execution is not yet confirmed.

## Address-register indirect 68000 reference instructions
`CPU68KReference` now initializes address registers `A0..A7` on reset (`A7` starts at the initial SSP) and supports `MOVEA.L #imm,An`, `MOVE.W Dn,(An)` and `MOVE.W (An),Dn` through the existing explicit reference bus. `test_cpu68k_indirect.py` adds eight scenarios for RAM, VDP and alignment. The earlier unaligned-word test now expects `ValueError` rather than `NotImplementedError`. These instructions are a small subset of the Motorola 68000, and the status register, condition codes, exceptions and chip timing are not modeled. No passing GitHub Actions status was confirmed for this commit.

## 68000 condition codes and conditional branches
`CPU68KReference` now holds a partial CCR (`X N Z V C`). Implemented MOVE/MOVEQ operations update N/Z and clear V/C while preserving X; `CMP.W Dn,Dm` and `CMPI.W #imm,Dn` compute N/Z/V/C for word subtraction. The reference `Bcc` decoder supports 8-bit and 16-bit displacement conditions except BSR (explicitly unsupported), and BRA remains supported. `test_cpu68k_flags.py` adds eleven regression cases. This is not a complete status register, interrupt, exception, timing or 68000 core model. CI test execution is not confirmed.

## 68000 subroutine stack reference
`CPU68KReference` supports `JSR (abs.l)` (`0x4EB9`), `JSR (An)` (`0x4E90..0x4E97`) and `RTS` (`0x4E75`). Return addresses are pushed to A7 in big-endian 16-bit bus words and popped on return. `test_cpu68k_subroutines.py` adds seven regression cases for stack values, nested calls, alignment and unmodeled stack access. This remains an untimed reference subset without exceptions, supervisor transitions, stack guard semantics or full 68000 execution. Test execution has not been confirmed.

## JMP control flow
`CPU68KReference.step()` supports `JMP (abs.l)` (`4EF9`) and `JMP (An)` (`4ED0..4ED7`), rejects odd jump destinations and leaves A7 unchanged. `test_cpu68k_jump.py` provides five regression cases. This is a partial 68000 instruction reference, not an operational commercial-ROM boot or cycle-accurate Genesis 3 VA2 hardware reconstruction. Test execution is not yet confirmed.

## Synthetic CPU-to-VDP smoke diagnostic
Run `python MegaDrive-NX-Next/diagnostic_cpu_smoke.py` from the repository root. This executes ten supported 68000 reference instructions to configure VDP register 15, stage a VRAM-write command, and write `0x1234` to VRAM address zero through the explicit-ready bus. It prints the instruction trace and asserts the expected VRAM value. This does not prove ASIC timing, real CPU completeness, or commercial game boot. The environment could not download the repository to execute the full suite, so passing tests are not claimed. Also fixed 16-bit word alignment checks and a misleading RTS stack test.

## DBcc loops and CI smoke coverage
The 68000 reference harness now supports DBcc (`0x50C8` pattern, including DBF and DBEQ) with a 16-bit decrement of the low data-register word when its condition is false. The branch base is the extension-word address and CCR is unchanged. Five regression cases are in `test_cpu68k_dbcc.py`. The GitHub Actions workflow now runs Python compileall, the complete unittest discovery suite, and `diagnostic_cpu_smoke.py`. This is synthetic diagnostic coverage only. CI success has not been verified; external ROM boot and chip-level timing remain unimplemented.

## 68000 32-bit MOVE reference operations
The CPU reference supports `MOVE.L #imm,Dn`, `MOVE.L (abs.l),Dn` and `MOVE.L #imm,(abs.l)` with big-endian two-word transfers and 32-bit N/Z flags (X preserved, V/C cleared). Eight cases in `test_cpu68k_long.py` cover ROM/RAM, flags and rejected addresses. BSR.s/BSR.w relative calls are also supported with six dedicated tests in `test_cpu68k_bsr.py`. CI remains unverified; this is not a cycle-accurate CPU or full game-boot implementation.

## MOVE.L register-to-absolute memory
`MOVE.L Dn,(abs.l)` now writes a 32-bit data register as two ordered 16-bit bus cycles (high word first). Three regression cases cover RAM content, CCR updates, and odd-address rejection. This is instruction-level reference behavior, not cycle-accurate timing. The full CI test result has not been independently verified.

## Address-indirect 32-bit transfers
`MOVE.L (An),Dn` and `MOVE.L Dn,(An)` now use two big-endian 16-bit reference bus cycles while preserving the address register. `test_cpu68k_long.py` covers RAM roundtrip, flags, alignment, and boundary rejection. These operations are not cycle accurate and do not imply verified Switch boot or VDP hardware timing.

## MOVEA.L pointer loads
The reference CPU supports `MOVEA.L (abs.l),An` and `MOVEA.L (An),Am` with ordered 16-bit memory reads, preserved CCR, and source-address capture before a same-register destination update. Four tests were added to `test_cpu68k_long.py`. CI execution remains unverified because this runtime cannot resolve github.com; the GitHub connector did confirm the commits.
