# Super Hang-On V1.3

Native HTML5 / Canvas reconstruction, landscape with tilt. V0.8 sprites and PCM engine retained.

V0.9 verifies all road pixels against EPR-10642.47 and uses decoded row boundaries for road, player, roadside and opponent projection. Original route sequences and background layouts remain unverified; procedural approximations are still present.

Run `python3 tools/verify-road.py /path/to/shangon.zip` with your local ROM; no ROM binaries added. Run `node tests/road-geometry.test.cjs` to check projection boundaries. Physical iPhone and full browser testing pending.

## V1.0

Recover four course sequences and 631 records from the main 68000 ROM at 0x8AEC and 0x8B4C. Original raw triples verified by expanded CRC32 2525c975. Game now uses 6/10/14/18 stages and ROM-based bend breakpoints instead of sinusoidal curvature. Direction mapping, strength, timing and units are provisional; hills and landscapes still approximated. Run `python3 tools/verify-courses.py /path/to/shangon.zip` and `node tests/course-model.test.cjs`. No full ROM binaries committed.

## V1.1

103 height-profile records and 1,283 scenery-pattern event records recovered. Original order and fields retained; runtime sorts a copy for visibility (one original position decreases). Scenery trigger coordinates replace uniform spacing. Each event currently draws a provisional atlas item; object count, graphics and side assignment have not been decoded. Hill shape remains provisional. Verify with `python3 tools/verify-course-events.py /path/to/shangon.zip` and `node tests/course-events.test.cjs`.

## V1.2

Sub-CPU pointer table at 0x19E8 provides 24 blocks of 2048 signed x/y road vectors. All 423 curve directions and all 208 straight records agree with the main CPU. 422 of 423 curves match inverse radius within 5%. Browser bend now scales as 64/radius (clamped), rather than radius/100. Visual gain and six-unit smoothing remain approximations. Validate and optionally export the vectors from your local ROM: `python3 tools/verify-road-vectors.py /path/to/shangon.zip [vectors.json]`. Run `node tests/road-vectors.test.cjs`. Elevations and object graphic mapping pending.

## V1.3

Recovered 21 sub-CPU vertical profiles (7,700 signed x/y vectors), pointer table 0x1A48. Browser replaces sinusoidal hills with interpolated original x-component samples (stride 16). Event positions come from main-CPU tables. Timing, sign-to-screen mapping, visual gain and perspective remain approximate. Full raw vectors can be exported locally using `python3 tools/verify-height-profiles.py /path/to/shangon.zip [profiles.json]`. `node tests/height-model.test.cjs` checks finite projection values and profile IDs. No raw ROM binaries added.
