# PAL-G VA4 clock and bus evidence ledger

Status: documented wiring evidence, NOT an implemented VA4 chipset.

## Confirmed oscillator / clock pins
| Source | From | To | Evidence |
|---|---|---|---|
| oscillator | OSC1 pin 3 (53.203424 MHz) | VDP 315-5313A pin 52 MCLK | dual-frequency oscillator installation guide |
| oscillator | OSC1 pin 3 | 315-5364 pin 51 MCLK | same |
| VDP | 315-5313A pin 51 CLOCK0 | Z80 pin 6 | same |
| VDP | 315-5313A pin 49 CLOCK1 | YM2612 pin 24 | same |
| VDP | 315-5313A pin 50 SCBR | CXA1145P pin 6 | same |
| PAL selection | JP3/JP4 | VDP pin 46 and CXA1145P pin 7 | same |
| region selection | JP1/JP2 | 315-5309 pin 25 | same; verify JP1 capacitor exception |

Source: https://www.consolesunleashed.com/guides/sega-mega-drive-dual-frequency-oscillator-install-guide/

## Timing baseline
- PAL master clock 53,203,424 Hz.
- 68000 nominal MCLK/7 = 7,600,489.142857 Hz. This is a frequency ratio, not a statement about edge phase or duty cycle.
- PAL subcarrier MCLK/12 = 4,433,618.666667 Hz (approximate: verify actual crystal frequency and video encoder tolerance).
- All transitions must be phase-verified before a pin-level simulation is claimed.

## Interface inventory (not yet netlist verified)
| Producer | Consumer | Signals to trace | Confidence |
|---|---|---|---|
| 68000 | 315-5364 control logic | address, AS, UDS, LDS, RW, DTACK | architecture-level only; pins unverified |
| 315-5364 | 315-5313 VDP | select, control, acknowledge | architecture-level only; pins unverified |
| VDP | VRAM IC9/IC10 | address/data/DRAM controls | architecture-level only; pins unverified |
| 315-5309 | controller ports | input selection and I/O | architecture-level only; pins unverified |

## Diagnostic plan
1. Record raw CPU bus state per phase and decode 0xC00004 byte address as 0x600002 word address.
2. Trace board-level select and DTACK independently of VDP input select, AS, UDS, LDS and internal ready.
3. Detect whether any complete CPU write handshake occurs; count transactions separately from pin samples.
4. Check VDP clock output and pixel clock progression against expected PAL timing.
5. Only after stable boot, model RC reset and audio/video analog transfer functions using documented values.

## Integrity caveats
- The current Nuked-MD FC1004 implementation must not be renamed 315-5364. These are different physical architectures.
- Passive components must be identified by schematic sheet and board revision; do not guess values.
- The PAL service manual contains a block-diagram oscillator transcription inconsistency; use the parts list and schematic frequency (53.203424 MHz).
- No Switch NRO change is implied by this document.
