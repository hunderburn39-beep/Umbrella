# Reactor Rush V5.1 — Godot (WebGL)

Graphics front-end in **Godot 4.3** (Compatibility renderer → WebGL 2). The rules, the maths and the house reserve
are **not** reimplemented: the Web export loads the validated `Reactor-Rush/engine/engine.js` through `web/rr_bridge.js`
(governed rounds, reserve cap 0.94, credited win `round2(win × bet)`), and Godot only draws the frames it returns.

- `scripts/main.gd` — layout over the approved artwork (landscape 1920×1080, portrait 1080×1920), HUD, round playback, info screen with the house-rule disclosure.
- `scripts/board.gd` — 7×7 board in the frame opening, drop-in, win highlight, explosions with particles, cascades.
- `scripts/quantum_panel.gd`, `scripts/fluct_panel.gd` — animated reactor panels (original design).
- `scripts/sfx.gd` — music (`assets/audio/quantum_arcade.mp3`) and synthesised effects.
- `assets/` — images extracted from the approved skin, Fira Sans (SIL OFL, `assets/fonts/OFL-FiraSans.txt`).

Outside the Web export there is no engine: the editor shows a preview board and pays nothing.

**Build:** workflow `.github/workflows/reactor-rush-godot-web.yml` (branch `reactor-rush-paytable-validation`) exports with
Godot 4.3 headless, copies `engine.js` and `rr_bridge.js` next to `index.html`, and tests the build in Chromium
(SwiftShader WebGL 2). Download the artifact `reactor-rush-godot-web` and serve the folder over HTTP
(`python3 -m http.server`), it does not run from `file://`. Nothing is published to `main` or GitHub Pages.
