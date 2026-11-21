# Super Hang-On V0.9

Native HTML5 / Canvas reconstruction, landscape with tilt. V0.8 sprites and PCM engine retained.

V0.9 verifies all road pixels against EPR-10642.47 and uses decoded row boundaries for road, player, roadside and opponent projection. Original route sequences and background layouts remain unverified; procedural approximations are still present.

Run `python3 tools/verify-road.py /path/to/shangon.zip` with your local ROM; no ROM binaries added. Run `node tests/road-geometry.test.cjs` to check projection boundaries. Physical iPhone and full browser testing pending.
