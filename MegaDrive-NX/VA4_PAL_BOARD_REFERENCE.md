# Mega Drive Model 1 PAL-G VA4: reference board

Status: **reference target, not an implemented board simulation**.

## Choice and source
Use Sega's **Model 1 PAL-G VA4 (837-7460)** as the reference for a Portuguese/PAL build. Primary source: Sega Mega Drive Model 1 PAL-G/PAL-I service manual, schematic sheets and VA4 parts list:
https://consolemods.org/wiki/images/6/6b/PAL_Mega_Drive_Model_1_Service_Manual.pdf

Secondary component inventory:
https://retrotechwiki.com/Sega_Mega_Drive_%28Model_1%29

Do **not** label the existing Nuked-MD build as a literal VA4 board: its current chip selection includes FC1004, which is not the discrete VA4 chipset.

## Confirmed principal VA4 parts (manual)
| Reference | Part / role |
|---|---|
| IC1 | SCN68000C8N64, Motorola-compatible 68000 |
| IC2/IC3 | 32K x 8 SRAM each, 68000 work RAM |
| IC4 | 315-5364 (YM6045C), custom control logic |
| IC5 | 315-5309 (YM6046), custom logic |
| IC6 | Z80A |
| IC7 | 8K x 8 SRAM |
| IC8 | 315-5313 / 315-5313A VDP |
| IC9/IC10 | 64K x 4 DRAM video memory each |
| IC11 | YM2612 FM synthesizer |
| IC12 | CXA1034 audio amplifier (or service-manual alternatives) |
| IC13 | CXA1145P video encoder |
| IC14 | LM358 op amp |
| IC15/IC17 | 7805 voltage regulators |
| OSC1 | 53.203424 MHz PAL reference oscillator |

## Non-IC parts to inventory from actual schematic
- Resistors and resistor networks: pull-ups, pull-downs, current limits, analog gain, video termination.
- Capacitors: decoupling, reset RC timing, analog audio/video filters.
- Transistors/diodes: switches, buffering and protection where present.
- Ferrite beads, oscillator, connectors, supply regulation and ground return.
- Track each component with **reference designator, value, tolerance, nets, purpose and simulation treatment**. Never guess values from a different board revision.

## Fidelity tiers
1. **Digital timing mandatory**: oscillator/dividers, reset, bus arbitration, address decode, wait states, VDP select, UDS/LDS, DTACK and RAM timing.
2. **Analog transfer-function model**: audio mixing/filtering and video output. Use measured or schematic-supported transfer functions, not a full SPICE simulation on Switch.
3. **Electrical inventory only**: supply bypass, protection and other components with no measurable effect on game-level behavior under nominal conditions.

## Next engineering gates
1. Transcribe schematic net connections for IC1, IC4, IC5 and IC8 and verify each pin direction/active level.
2. Compare existing Nuked-MD FC1004 pin behavior against VA4's separate IC4+IC5 topology. Explicitly record unsupported equivalences.
3. Build a pin-level address/handshake test with raw 68000 and VDP inputs. Do not force DTACK.
4. Reconcile the VDP diagnostic ROM's display path and performance only after the bus test passes.
5. Add resistor/capacitor/transistor inventory from the exact VA4 schematic sheets, with traceable designators.

This document does not claim electrical component-level emulation is implemented or that the NRO now matches VA4.
