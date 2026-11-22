# MegaDrive-NX: hardware mapping audit (2026-11-22)

## Scope and source of truth
**Target hardware:** Sega Mega Drive / Genesis **Model 2 VA0/VA1**, because pinned Nuked-MD revision `594ca2a494104df559a907db7c8f5602a93b2078` simulates the Sega FC1004 (315-5660) combined ASIC. Do not claim this matches the separate-chip Model 1 VA4 or VA6.5 PCB exactly.

Primary hardware references:
- Sega PAL Model 1 maintenance manual (use only for *Model 1* comparisons): https://consolemods.org/wiki/images/6/6b/PAL_Mega_Drive_Model_1_Service_Manual.pdf
- Model 2 IC map: https://retrotechwiki.com/Sega_Mega_Drive_/_Genesis_%28Model_2%29_Troubleshooting_Guide
- Model 1 revision IC map: https://gametechwiki.com/w/index.php/Sega_Mega_Drive/Genesis_Hardware
- Pinned upstream: https://github.com/nukeykt/Nuked-MD/tree/594ca2a494104df559a907db7c8f5602a93b2078

## Model 2 VA0/VA1 hardware vs software mapping

| Hardware element | Model 2 reference | Nuked-MD source in build | Status |
|---|---|---|---|
| Main CPU | 68000 (IC1) | `68k.c`, `M68K_Clock2` in `md.c` | Present in code; timing and correctness **unverified** |
| Work RAM | 64 KiB | `md.c` bus/memory accesses | Memory mapping and bus timings **need trace** |
| Sound CPU | Z80 (IC4) | `z80.c`, `Z80_Clock2` in `md.c` | Present in code; timing **unverified** |
| Z80 RAM | 8 KiB (IC5) | `md.c` Z80 RAM access | Present in code; arbitration **unverified** |
| Main ASIC | Sega FC1004 / 315-5660 (IC6) | `fc1004.c`, `FC1004_Clock` | Present in code; register, clock and handshake accuracy **unverified** |
| Graphics processor | Integrated in FC1004 | `vdp.c`, `Video_PlotVDP` | Present in code; **PIXELS=0** on user's Super Hang-On run |
| FM audio | Integrated in FC1004 | `fm.c`, `audio.c` | Present in code; audio output **unverified** |
| PSG | Integrated audio subsystem | `fc1004.c` / `audio.c` | Signal path needs line-level inspection |
| Video RAM | VRAM IC7/IC8 | `vram.c`, `update_vram` | Present in code; timings **unverified** |
| Bus arbitration | Integrated in FC1004 | `arbiter.c`, `md.c` | Present in code; **highest priority to validate** |
| I/O / controller | Integrated in FC1004 | `iochip.c`, `controller.c`, `nx_frontend.c` | Present in code; mapping and handshake **unverified** |
| Cartridge interface | Cartridge ROM / address bus | `cartridge.c`, `md.c` | Present in code; ROM read traces **needed** |
| TMSS boot | Revision-dependent | `tmss.c` and `port.py` forced built-in TMSS | Adapted; boot mapping **needs validation** |
| RGB encoder, analog amps, regulators | External analog circuitry | Not simulated as discrete analog chips | Intentionally omitted; digital display/audio frontend substitutes outputs |

## Critical observations from Switch tests
- V3.6 measured RATE ~50,921 simulated master cycles/s, V3.7 ~38,191 cycles/s in separate user screenshots. Neither is close to 53.69 MHz NTSC master clock.
- Both show **FRAMES=1, PIXELS=0, VDP=0**, with last observed CPU bus address **13832** (word address, physical byte address 0x6C10). This alone does not establish a CPU infinite loop.
- V3.7 LTO flags should not be assumed beneficial. Restore V3.6 compiler settings for a controlled A/B test.
- The reported 1,224 MHz is the **Switch CPU frequency**, not the Mega Drive's 68000 clock.

## Priority investigation, in order
1. Capture a *bounded, low-overhead* bus trace of 68000 address, R/W, AS, DTACK, data and reset, plus FC1004 register select/ack; retain last 64 transitions in RAM. **No automatic DTACK injection**. Check whether address 0x6C10 is normal ROM polling, a missing VDP response or a bus mapping fault.
2. Validate ROM vector table, reset PC and first 100 meaningful bus transactions against a reference execution of the same ROM. RetroArch is evidence the ROM can run, **not** a chip-level timing oracle.
3. Verify 68000 <-> FC1004 arbitration and control port addresses, then Z80 reset and bus request behavior.
4. Validate VDP register initialization, VRAM writes and scanline timing. Only after VDP commands and PIXELS progress, optimize rendering.
5. Benchmark each individual chip stage and full-cycle overhead with the same ROM, region and diagnostic settings; compare compiler variants on-device.

## Important limitations
This is a **source-to-hardware inventory**, not proof of transistor-level equivalence or completeness. Model 1 and Model 2 board revisions differ. Analog circuitry is not needed as discrete simulated components to present a digital video signal on Switch, but a fully faithful physical motherboard reconstruction would require much more. A Switch NRO running Nuked-MD is **software gate-level simulation**, not an FPGA or a literal hardware motherboard.

## Correction (2026-11-22)
Nuked-MD's own README explicitly states that its NMOS 68000 + NMOS Z80 + FC1004 combination never shipped together in a production Mega Drive. **Model 1 VA7** is the closest actual revision, not Model 2 VA0/VA1 as the original audit implied. The inventory above is an approximate functional mapping, not a literal Model 2 BOM. Reference: https://github.com/nukeykt/Nuked-MD/blob/main/README.md
