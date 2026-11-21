# PCB Native V2.0 — Hardware reference

Target: Super Hang-On upright/mini architecture with Out Run-derived CPU board and Super Hang-On-specific video board, not the separate ride-on hardware variant.

## PCB identification
- CPU: PCB 171-5376-01, assembly label 837-6278-02; game label 834-6277-02.
- Video: PCB 171-5480, assembly label 837-6279-03.
- Interconnect: three 50-pin connectors (A/B/C).
- References: https://arcarc.xmission.com/archive/PDF_Arcade_Manuals_and_Schematics/Super_Hang-On_Schematics.pdf (original CPU schematic, 1987).
- Hardware notes: https://github.com/mamedev/mame/blob/master/src/mame/sega/segaorun.cpp
- Custom IC inventory: https://github.com/mamedev/mame/blob/master/src/mame/sega/segaic16.cpp

## Digital devices
CPU: 2 x 68000 at 10 MHz; Z80A and YM2151 at 4 MHz; YM3012 DAC; 315-5195 memory mapper; 315-5218 PCM; 2 x 315-5155 road bit extraction; 315-5222 road mixing; 315-5223A/5224/5225/5226 programmable logic.
Video: 315-5196 sprites; 315-5197 tilemaps; 315-5213 sprite logic; 315-5242 color encoder; 315-5251 programmable logic; ADC0804, D4051 analog mux, TLP521-4 optocouplers, ULN2003 outputs.
RAM families: TMM2063, TMM2115, TMM2018, D42832 (32K x8); schematic and PCB revision may differ.
Oscillators: CPU 40 MHz, sound 16 MHz, video 25.1748 MHz. Target 320 x 224 visible, approx. 60.0546 Hz.
Analog sound: TL084, LM324, MP7633JN, MF6CN-50 filters, 4066 switching.

## Owner ROM audit
25 entries read and CRC32 calculated from actual ZIP shangon(1).zip; all 25 match the requirements in pinned upstream sho_core.c (revision 4f5f25f1c680c53946323e0bf9a1cf8bfb4f72c2).
Name / bytes / CRC32 / role:
```
epr-10886.133 65536 8be3cd36 main
epr-10884.118 65536 cb06150d main
epr-10887.132 65536 8d248bb0 main
epr-10885.117 65536 70795f26 main
epr-10792.76 65536 16299d25 sub
epr-10790.58 65536 2246cbc1 sub
epr-10793.75 65536 d9525427 sub
epr-10791.57 65536 5faf4cbe sub
epr-10652.54 32768 260286f9 tiles
epr-10651.55 32768 c609ee7b tiles
epr-10650.56 32768 b236a403 tiles
mpr-10794.8 131072 7c958e63 sprites
mpr-10798.16 131072 7d58f807 sprites
mpr-10795.6 131072 d9d31f8c sprites
mpr-10799.14 131072 96d90d3d sprites
mpr-10796.4 131072 fb48957c sprites
mpr-10800.12 131072 feaff98e sprites
mpr-10797.2 131072 27f2870d sprites
mpr-10801.10 131072 12781795 sprites
epr-10642.47 32768 7836bcc3 road
epr-10649c.88 32768 f6c1ce71 Z80
epr-10643.66 32768 06f55364 PCM
epr-10644.67 32768 b41d541d PCM
epr-10645.68 32768 a60dabff PCM
epr-10646.69 32768 473cc411 PCM
```

No ROM bytes committed. CRC match verifies the input set, not runtime fidelity. Existing local-build script uses upstream translation of both 68000 programs; obtains device behavior from software models, including Z80 and audio. This is functional reconstruction, not a transistor-level PCB clone. Native and WASM compilation, 1200-frame comparison, sound, DIP/free play, and physical Safari testing remain pending.
