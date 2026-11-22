# VA4 PAL-G: reset, clocks, and passive-component evidence

Reference board: Sega Model 1 PAL-G VA4, not the FC1004-based integrated board.

## Schematic sources
- Sega maintenance manual (August 1992), VA4 schematics starting on printed page 64: https://gamesx.com/files/Mega_Drive_Maintenance_Manual_-_PAL-G%2C_August%2C_1992%2C_Rev._A.pdf
- Sega VA4 service bulletins summarized at https://retrotechwiki.com/Sega_Mega_Drive_/_Genesis_%28Model_1%29_Troubleshooting_Guide

## Confirmed constraints
- Master oscillator: 53.203424 MHz PAL. All clock-domain relationships must be checked against the schematic before assigning dividers.
- IC4: 315-5364 (YM6045C); IC5: 315-5309 (YM6046); IC8: 315-5313 or 315-5313A.
- **VA4 has no TMSS security ROM.** Existing Nuked-MD TMSS HUD/logic must be treated as a mismatch to the VA4 target, not evidence of a defective VA4 chip.
- Board's audio YM2612 is discrete (IC11).

## Real passive components that affect observable behavior
| Reference | Evidence | Significance | Implementation decision |
|---|---|---|---|
| C92 | Sega bulletin 008: original 51 pF; recommends 33 pF for 32X compatibility | Clock signal integrity near IC4 | Track as clock-conditioning variant; do not blindly simulate analog RC in CPU loop |
| FB7 | Bulletin 008: jumper/short in 32X repair | Signal integrity | Document original and repair variants separately |
| C112 | Bulletin 008: remove 33 pF rear-side addition | Clock integrity | Do not confuse with same-designator parts in other revisions |
| C10 | Bulletin 008: connection from IC4 pin 31 to EM16 | Clock path | Map nets before modeling |
| C78 / C100 | Bulletin 012: remove for VCLK lock-up repair | Video clock integrity | Preserve stock baseline and optional service-bulletin profile |
| JP1 | VA4 service parts list: 47 uF 10 V capacitor | Supply/board revision nuance | Do not assume JP1 is solely a region jumper on this PCB |

The bulletins concern **repair variants**; they do not establish that all stock VA4 boards should use modified values.

## Diagnostic engineering acceptance gates
1. Validate raw 68000 word address against physical byte address and trace CPU AS/RW/UDS/LDS.
2. Probe IC4-side decode, chip-select, and DTACK separately from IC8 input pins.
3. Ensure a diagnostic write reaches the VDP control port, then verify VDP internal acknowledgement and actual pixels.
4. Audit TMSS: make a VA4-specific mode without TMSS only when the chipset and boot path are modeled consistently.
5. Measure performance and compare output to a known-good VA4; never declare a chip-equivalent reproduction based on a boot screen alone.

## Important limitation
No pin-complete VA4 netlist has been transcribed yet. No resistor/transistor values should be invented. The existing Switch NRO remains a Nuked-MD-based diagnostic build, **not** a VA4 electrical simulation.
