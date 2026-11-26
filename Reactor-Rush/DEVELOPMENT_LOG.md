# Reactor Rush V5.0 — shared development log

## Initial handoff
Author: ChatGPT
Status: brief prepared; implementation and validation not confirmed.

Claude and ChatGPT: append dated entries with author, commit SHA, files changed, tests actually executed, results, remaining work and blockers. Read latest main and CLAUDE_TASKS.md before each session. Do not overwrite another agent's changes. Record the final playable URL only after verification.

---

## 2026-11-26 — Claude — session 1 (engine, tests, simulation; renderer NOT touched)
Author: Claude (Sonnet 5.5) · Base: main @ 6cc16062 (unchanged on remote at start and before push)
Commit with the code: **dda3590a** · this log entry is a separate follow-up commit.

### Read first
- CLAUDE_TASKS.md (V5.0 brief) and this log. No instruction was changed or skipped silently; items not done are listed under "Not done".
- Shipped `index.html` is still **V4.0**. Its game logic is a loose approximation, NOT the brief: energy bar 5 x 25 = 125 with four invented features (IMPLOSÃO/ALTERAÇÃO/DEMOLIÇÃO/INCISÃO), no Fluctometer awards, no Quantumeter levels 55/85/110/135, no Energoon, no Pair Explosion, simplified Gargantoon. It should not be described as matching the reference.

### Blocker: reference PDF unreadable
`pokerstars.it/.../Reactoonz 2.pdf` is not on this session's network allowlist, and WebSearch did not return it. Mechanics were taken from two public secondary pages (casinos.com, slotcatalog.com). **Neither gives a paytable**; they also disagree on minimum cluster (3 vs 5) and on Level 1 (four 1x1 vs "4x1"). Every interpretation is tabulated in `engine/ASSUMPTIONS.md`. **ChatGPT / user: please supply the PDF text or its paytable tables; five concrete questions are listed at the end of that file.** Until then no equivalence claim of any kind is made.

### Files added (all under Reactor-Rush/, no other game touched, index.html and CSS untouched)
- `engine/engine.js` — pure engine, no DOM/audio/timers, seeded PRNG (sfc32). 7x7, cascades, Fluctometer, Uncharged/Electric Wilds, Quantumeter 55/85/110/135, Energoon (4 x 1x1; 2x2), Gargantoon 3x3 with splitting 3x3 -> two 2x2 -> nine 1x1, overcharge x2, Pair Explosion, activation order, 5083x cap. UMD: `window.RREngine` in browser, `require()` in Node.
- `tests/engine.test.js` — 16 tests, `node --test Reactor-Rush/tests/engine.test.js`.
- `sim/run-sim.js` — reproducible multi-process runner (fixed 50k chunks, result independent of worker count).
- `sim/*.json` — every run kept, including the failed first validation.

### Tests actually executed
- 16/16 pass on Node v22.23.5. They cover: PRNG and `simulate()` reproducibility, cluster threshold 5, wild bridging, Uncharged blocking, single-claim of wilds, payout monotonicity, Quantumeter level boundaries, Uncharged -> Electric, zap + meter charge, Gargantoon splitting (3x3 and 2x2), overcharge x2, levels 1–4 effects and Quantumeter disable after Gargantoon, Pair Explosion adjacent/apart/single, anchored-block gravity, win cap, and an **audited run of 20 000 full rounds** checking end-state invariants (valid cells, no unresolved cluster, no leftover pair, no unplayed Quantumeter level, block bookkeeping).
- Mutation sanity check (temporary, reverted): minCluster 4, level-4 threshold 140, and removing the x2 were each caught by the expected tests.
- Not tested: any browser. No Chrome or Safari run, no render test, no 16:9/9:16 check this session.

### Simulation (virtual bet = 1, Free Play only)
Parameter note: with equal symbol weights and sourced rules, hit rate was 16 % and the Quantumeter never reached level 1 in 100k rounds (raw RTP 6.5 %), so symbol weights and wild-source rates are original tuning, chosen by feature frequency only. `payScale` is one global factor.
1. First calibration: 400k rounds, seed 111 -> payScale 1.24 (SE 0.57 %, too noisy).
2. **First validation FAILED to agree:** 2,000,000 rounds, seed 20261126, payScale 1.24 -> RTP 97.29 %, SE 0.32 %, 95 % CI [96.66 %, 97.92 %]; 96.20 % outside the CI. Kept as `results-first-validation-payScale1.24.json`. Cause: calibration noise.
3. Recalibration on a 10x bigger sample: 4,000,000 rounds, seed 111 -> raw RTP 78.48 %, payScale **1.2258**.
4. **Validation on fresh seeds (payScale 1.2258):**
   - seed 424242, 2,000,000 rounds: RTP 95.84 %, SE 0.32 %, 95 % CI [95.22 %, 96.46 %]
   - seed 90210, 2,000,000 rounds: RTP 95.64 %, SE 0.32 %, 95 % CI [95.02 %, 96.26 %]
   - 96.20 % lies inside both intervals; both point estimates are 0.4–0.6 points below it.
   - hit rate 48.8 %, 1.45 cascades/round, Gargantoon in ~1.0 % of rounds, Quantumeter L1 ~2.9 % / L2 ~1.0 % / L3 ~0.45 % / L4 ~0.5 %, Pair Explosion ~0.15/round. Runtime ~22 s per 2M rounds.
- Caveats: the CI is a normal approximation from per-round variance; wins are heavy-tailed, so it can be optimistic. This is the RTP of **this project's own tuned paytable**, not evidence about the original. **Volatility is far lower than the reference:** highest win seen in 6M validated rounds ~278x vs a stated max of 5083x; the cap was never hit.

### Not done (honest list)
1. **Renderer integration.** `index.html` still runs its own inline logic; the engine is not wired in, so the playable game does not yet reflect the engine or the brief. Separation of simulation from rendering exists only as the new module.
2. Animated unboxed reactor-level and big-win messages (V4.0 already has unboxed bitmap/lettering banners, but there are no reactor levels in the playable game to announce).
3. Original-paytable verification, original probabilities: impossible without the PDF.
4. Safari and Chrome tests, 16:9 / 9:16 layout re-check, Quantum Arcade music and no-voice check after integration.
5. GitHub Pages publish and verification: nothing to publish yet that changes the game; no playable URL is claimed.
6. Wider volatility (tail) tuning, if the PDF's paytable is obtained.

### Suggested next steps (for whichever agent continues)
- Get the PDF tables -> replace `baseWin`/`SIZE_GROWTH`, set `minCluster`, thresholds; re-run `node Reactor-Rush/sim/run-sim.js --calibrate --rounds 4000000 --seed 111`, set `payScale`, validate on new seeds.
- Integrate: give the engine an event-recording mode (steps: win clusters, removals, falls, zaps, spawns) so `index.html` only animates events; keep approved art, layout and audio untouched; then browser-test.
- Before editing `index.html`: `git fetch` and re-read this log.

## Session 2 (Claude, 2026-11-26) — renderer integration, on branch `reactor-rush-v5-renderer` (NOT merged to main)

I worked in parallel before seeing the session-1 engine on main. Result: a second, independent engine (`rr-engine.js`) wired into `index.html`, plus `rr-sim.js`, `tests/engine-tests.js` (22 pass), `tests/ui-tests.py` (25 pass, Chrome headless only), `REPORT-V5.0.md`, and a V4.0 backup in `backup-V4.0/`. `engine/engine.js` and `sim/run-sim.js` from session 1 are untouched.

**Decision for the owner (not mine to make):** two engines now exist. `rr-engine.js` is wired into the renderer (traced frames, 4 reactor levels, Gargantoon splitting, Wild Pair Explosion, unboxed 3D messages, pay table menu, portrait/landscape panels), but its own observed RTP is 97.47 % (95 % CI 96.37–98.57 %, 20M rounds, seeds 101/202/303/404) and its pay table, weights and Fluctometer/explosion rules are secondary-source/own tuning, not official. Session-1 engine has the closer RTP (95.6–95.8 %) but is not yet rendered. Options: (a) merge this branch and later swap the engine behind the same frame format, (b) port event tracing to `engine/engine.js` and re-use the renderer from this branch.

Not done / not verified: Safari and real iPhone, audio by ear, official PDF (still HTTP 403 here), live GitHub Pages check. Main and the published stable version were not changed.
