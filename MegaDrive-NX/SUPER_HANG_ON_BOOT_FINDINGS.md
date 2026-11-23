# Super Hang-On: boot evidence and next hardware checks

## Observed in supplied rom-boot-trace.txt

This is a cartridge-read trace, **not** a decoded 68000 instruction-execution trace.

| Observation | Value |
| --- | --- |
| Initial SSP vector (ROM bytes 0..3) | `0x00FF0200` |
| Initial PC vector (ROM bytes 4..7) | `0x00006BAC` |
| Cartridge read entries | 32 |
| First observed code word at reset PC | `0x7000` |
| Branch opcode at `0x006BBA` | `0x670A` |
| Conditional branch destination | `0x006BC6` |
| Potential TMSS unlock write | longword `0x53454741` to `0xA14000` |

At `0x006BAE`, the ROM contains `MOVE.B $A10001,D0` (words
`1039 00A1 0001`). The next words include `ANDI.W #$000F,D0`
and `BEQ` to `0x006BC6`. If the branch is not taken, the code contains
`MOVE.L #'SEGA',$A14000` beginning at `0x006BBC`.

**Do not infer the value read from A10001, the branch outcome, actual
instruction retirement, or a TMSS write from ROM reads alone.**

## Required next Switch trace

1. Observe the 68000 reset release and actual CPU address-strobe transitions.
2. Correlate the CPU bus address with cartridge reads at `0x006BAC`.
3. Capture the *returned data* for the CPU read at `0xA10001`, if issued.
4. Capture an actual bus write to `0xA14000`, if the TMSS branch is taken.
5. Only after CPU progress is demonstrated, capture writes to VDP
   control/data ports `0xC00004` and `0xC00000`.
6. If CPU addresses stop, inspect DTACK, reset and bus arbitration
   before modifying the VDP rendering equations.

## Validation boundary

Static audits and successful GitHub Actions compilation cannot establish
that the Switch is correctly executing the game. Compare these expected
milestones with hardware-generated `cpu-bus-trace.txt` and
`rom-boot-trace.txt`. The CPU trace records **bus transitions**, not a
decoded instruction PC.
