# Super Hang-On V1.0

Native HTML5 / Canvas reconstruction, landscape with tilt. V0.8 sprites and PCM engine retained.

V0.9 verifies all road pixels against EPR-10642.47 and uses decoded row boundaries for road, player, roadside and opponent projection. Original route sequences and background layouts remain unverified; procedural approximations are still present.

Run `python3 tools/verify-road.py /path/to/shangon.zip` with your local ROM; no ROM binaries added. Run `node tests/road-geometry.test.cjs` to check projection boundaries. Physical iPhone and full browser testing pending.

## V1.0

Recover four course sequences and 631 records from the main 68000 ROM at 0x8AEC and 0x8B4C. Original raw triples verified by expanded CRC32 2525c975. Game now uses 6/10/14/18 stages and ROM-based bend breakpoints instead of sinusoidal curvature. Direction mapping, strength, timing and units are provisional; hills and landscapes still approximated. Run `python3 tools/verify-courses.py /path/to/shangon.zip` and `node tests/course-model.test.cjs`. No full ROM binaries committed.
