# Phase 2 — palette and chained sprite investigation
Verified against the supplied merged ROM:
- US palette pointer tables at 0x2478 and 0x7602; four consecutive banks at 0x34cf6, 0x35cf6, 0x36cf6, 0x37cf6.
- Japan pointer tables at 0x2478 and 0x7648; banks at 0x34c70, 0x35c70, 0x36c70, 0x37c70.
- Each bank contains 2048 big-endian words (128 groups of 16 colors), decoded as xBGR444. High nibble is ignored. These are static values; actual group selection, fading and mixing require tracing.
- Chained square sprite addressing follows the Tecmo shared sprite device: interleave the three low x/y bits; aligned groups of 4, 16 or 64 cells form 16/32/64-pixel squares. The normal release has 4096/1024/256 possible groups; prototype has 2048/512/128. These are possible aligned groups, not counts of distinct game objects.
- The US code around 0xc8d4–0xc970 writes background attributes and tile IDs into 0x70000 and 0x74000. A stream branch handles ordinary two-byte entries and a separate dispatch handles control bytes. Full command interpretation, map composition and runtime verification remain open.
- Open index.html in a modern browser and choose your original spbactn.zip; the ROM is read locally and never included in this repository. The browser viewer was committed but has not yet been verified end-to-end on iOS.
Reference: MAME src/mame/tecmo/spbactn.cpp and src/mame/shared/tecmo_spr.cpp, BSD-3-Clause.
