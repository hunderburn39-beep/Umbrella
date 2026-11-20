# Super Pinball Action — ROM research

Tecmo, 1991 (US/Japan), 1989 prototype. Source input: a locally supplied merged spbactn.zip, 28 files. This public folder contains extraction code and documentation, not ROM dumps or original artwork.

## Run
```sh
python -m pip install Pillow
python extract.py spbactn.zip extracted
```

Output: original chip dumps, CRC32/SHA1/SHA256 manifest, reconstructed Motorola 68000 program for each set, Z80 sound programs, raw graphics regions, indexed PNG atlases, and OKI ADPCM samples decoded to WAV. The expected populated regions contain 53,248 tile slots (including blank tiles) in 52 atlas pages and 42 candidate sample entries (one address pair repeated).

Graphics use diagnostic grayscale, not runtime RGB palettes. The original pen indices are retained. A sprite may be composed of many 8×8 cells; complete tables, animation grouping, collisions and game logic are not reconstructed. Prototype background layout is marked uncertain in MAME. Music synthesized by YM3812 requires runtime register capture; it is not supplied as WAV.

## Technical reference
[MAME driver](https://github.com/mamedev/mame/blob/master/src/mame/tecmo/spbactn.cpp) (BSD-3-Clause, David Haywood).
Main map: ROM 00000–3FFFF, RAM 40000–43FFF, sprite RAM 50000–50FFF, foreground 60000–67FFF, background 70000–77FFF, palette 80000–827FF. Release palette xBGR444, prototype xBRG444. CPU 68000, Z80; audio YM3812 and OKIM6295. 
