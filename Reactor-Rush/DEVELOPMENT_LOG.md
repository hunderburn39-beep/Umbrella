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

## Session 3 (Claude, 2026-11-26) — OWNER_DECISION_OPTION_B acknowledged and implemented
**Acknowledged:** option B approved (commit d4c3004e). `engine/engine.js` is now the single authoritative engine; `rr-engine.js` from session 2 is archived in `archive/rr-engine-alt/` (unused).
**Done:** `playRoundTrace` added to `engine/engine.js` (no RNG change: 200 000-round baseline identical, sum/hits/cascades/levels bit-for-bit; 20 000-round trace-vs-plain equality test). Renderer in `index.html` now animates only engine frames. Round replay verified in the browser for 12 seeds.
**Tests:** `node --test tests/engine.test.js tests/trace.test.js` 22/22; `python3 tests/ui-tests.py` 37/37 (Chrome headless only). Note: `node --test tests` (whole folder) also tries to run non-test files; pass the two files explicitly.
**RTP, independent re-run:** 4 000 000 rounds, seed 20261127: 95.997 % (95 % CI 95.56–96.44 %), hit rate 48.9 %, max win 268x. File: `sim/results-verify-seed20261127-4M.json`.
**Discrepancies / not verified:** Safari and iPhone untested; audio not listened to; official PDF still 403 (paytable is this project's own, labelled provisional in the info menu); GitHub Pages not checked from my environment; volatility far below reference (max 268x vs 5083x) so top celebration tiers (QUANTUM 250x, MAX 1000x) are almost never reached. Level 4 "x2" in this engine applies only to wins containing a Gargantoon piece.
**Process note:** before this decision I had merged my alternate-engine renderer into main (9ee99bf2). Main therefore briefly played `rr-engine.js`; the branch `reactor-rush-option-b` replaces it with the engine in this log.
- **Merged to main:** feature commit 4c57f9fb, merge commit f371b63b.

## Session 4 (Claude, 2026-11-27) — V5.1 paytable validation, branch `reactor-rush-paytable-validation` (NOT merged to main)
Author: Claude (Sonnet 5.5) · Base: branch head bd4baaad · Commit with these changes: see git history of this branch (this entry is part of it).
**New target (owner):** RTP 94.00 %, Free Play only. **The target is NOT met** (see results); nothing was tuned in this session.

### Why the previous run failed
Actions run 45928565440 (commit bd4baaad, workflow "Reactor Rush paytable validation") ended in failure. The page shows only "Process completed with exit code 1" and an artifact `paytable-validation` (628 bytes); logs need a GitHub sign-in and were not readable here. Reproduced locally: the failing step is the regression test `payout is monotonic in cluster size and in symbol rank` (21/22), which required a **strictly** higher payout for every extra cluster size, while the documented table pays the same value inside the tiers 10–11, 12–14 and 15+. This is a test error, not an engine error.

### Changes (only tests and simulation report; engine, paytable, `index.html`, art, music and sounds untouched)
- `tests/engine.test.js`: the progression test now accepts **equal** values inside the same tier (5, 6, 7, 8, 9, 10–11, 12–14, 15+), requires a strictly higher value when a new tier starts, and for symbol rank requires non-increasing payouts (the documented table has equal values for symbols 5/6 and 7/8, and 3/4 at size 7) with the top symbol always above the bottom one.
- `sim/run-sim.js`: report now carries `targetRtp` 0.94, `deltaVsTarget`, `targetInsideCi95` and `volatilityIndexSd` (per-round standard deviation in bets). No change to the simulation itself.
- New result file `sim/results-v5.1-validation-seed20261128-4M.json`.

### Tests actually executed (Node v22.23.5)
- `node --test tests/engine.test.js tests/trace.test.js`: **22/22 pass** (was 21/22).
- Paytable check, 8 symbols × cluster sizes 5–49 against the documented table: **360/360** (same script as the workflow, run locally).
- Not run this session: `tests/ui-tests.py` (browser), Safari/iPhone, audio by ear, GitHub Pages. No render code was changed.

### 4 000 000-round validation (virtual bet = 1, Free Play, seed not used before)
Command: `node sim/run-sim.js --rounds 4000000 --seed 20261128 --workers 4 --out sim/results-v5.1-validation-seed20261128-4M.json` (47 s).
- **RTP 105.349 %**, SE 0.556 pts, 95 % CI **[104.259 %, 106.439 %]**. 94.00 % is outside the interval (+11.35 pts); 96.20 % also outside.
- **Volatility:** standard deviation of the win per round **11.12 bets**; hit rate 48.84 %; highest win 1 423.4x (cap 5 083x never hit); 415 rounds ≥ 500x, 3 632 in 100–500x, 32 174 in 20–100x, 75 379 in 5–20x, 361 348 in 1–5x, 1 480 669 in 0–1x, 2 046 383 zero-win rounds. Average 1.45 cascades per round.
- Features per round: Fluctometer awards 0.591, Quantumeter L1 2.93 % / L2 0.96 % / L3 0.46 % / L4 0.52 %, Gargantoon 0.97 %, Pair Explosion 0.153.
- Cross-check, same script as the workflow (seeds 271126–271129, 1 000 000 each): RTP **106.0083 %**, SE 0.569 pts, CI [104.893 %, 107.124 %], SD 11.38, hit rate 48.86 %, max 1 415x. This reproduces the figure the owner reported. The two runs differ by 0.66 pts, which is within sampling noise.
- Caveats: the interval is a normal approximation from per-round variance and wins are heavy-tailed, so it may be optimistic. This is the RTP of this project's own engine with the documented paytable, not evidence about the original game. The RTP rose from about 96 % (session 3, with a provisional paytable and a global payScale) to about 105–106 % after the documented Austrian paytable replaced it; the engine has no payScale any more.

### Open problem and options (decision for the owner, not applied)
RTP is about 11 pts above target while the documented paytable must stay unchanged. Reaching 94 % therefore has to come from the non-paytable parameters, for example symbol weights, wild-source rates (`startUnchargedCum`, `pUnchargedAfterCascade`), Fluctometer threshold or Quantumeter charging, followed by a recalibration on a large seed and a fresh validation on other seeds. A uniform payout multiplier (about 0.892) would also work but would change the documented table, so it was not used.

### Remaining / blockers
- RTP 94.00 % not reached; tuning plan above awaits a decision.
- The Actions run for this branch will re-run on push; its result is not known yet.
- Nothing was pushed to `main`.

## Session 4b (Claude, 2026-11-27) — house reserve ("limite rígido", session balance), same branch, NOT merged to main
**Owner request:** the house must always have a return, never a loss; adjust by balance. Owner chose: **hard limit** and **balance of the current session** (resets when the page is opened or reloaded).
**Rule implemented:** per session, total paid ≤ 0.94 × total wagered at every moment, so the house keeps at least 6 % of everything wagered. Before each round the engine computes the largest win the reserve can pay; a drawn round that would pay more is discarded and the next draw from the same RNG stream is used (rejection sampling). The plain engine (`playRound`, `playRoundTrace`, `simulate`) and the documented paytable are unchanged.
**Honest description of what this is:** rounds are no longer independent draws; the outcome depends on the session balance, and large wins can only appear when the reserve covers them. This is disclosed in the info menu ("Regra da casa (Free Play)"). It is not a claim of equivalence with any original game. Free Play only, no real money.
**Files:** `engine/engine.js` (new: `createGovernor`, `governorAllowance`, `playGovernedRound`, `governorSettle`, `simulateGoverned`), `index.html` (spin uses `playGovernedRound` and settles the credited win; info-menu note; engine script cache `?v=52`; test hook `__rr.gov`), `tests/governor.test.js` (new, 9 tests), `tests/ui-tests.py` (replay test uses the governed engine; new reserve check), `sim/run-governor.js` (new), workflow regression step now also runs `tests/governor.test.js`.
**Tests executed:** `node --test tests/engine.test.js tests/trace.test.js tests/governor.test.js` 31/31; `python3 tests/ui-tests.py` 38/38 (Chrome headless only). Not run: Safari, iPhone, audio by ear, GitHub Pages.
**Guarantee checked in simulation:** 0 rounds with paid > 0.94 × wagered and 0 rounds with the player ahead, in 7 000 000 simulated rounds, plus 100 000 rounds with mixed bets in the unit tests and 30 000 rounds with 0.05 bets and cent rounding.
**Simulation (bet 1, independent sessions with a fresh reserve; interval on session RTPs, normal approximation):**
| session length | sessions × rounds | effective RTP | 95 % CI | session RTP min–max | per-round SD | max win | rerolls/round |
|---|---|---|---|---|---|---|---|
| 100 | 10 000 × 1 000 000 | 48.41 % | 48.11–48.71 % | 11.6–93.3 % | 1.82 | 68.7x | 0.013 |
| 1 000 | 4 000 × 4 000 000 | 76.60 % | 76.31–76.90 % | 43.3–93.9 % | 4.47 | 269.1x | 0.003 |
| 10 000 | 200 × 2 000 000 | 89.48 % | 89.07–89.90 % | 77.1–93.9 % | 6.17 | 1 020.7x | 0.0008 |
Files: `sim/results-governor-len100-1M.json`, `sim/results-governor-len1000-4M.json`, `sim/results-governor-len10000-2M.json` (seeds 20261130, 20261129, 20261131).
**Result vs target:** the 94.00 % RTP target is **not met** as a player-facing figure. The reserve caps RTP at 94 % but, with this volatile engine, the effective RTP is far lower in realistic sessions (about 48 % at 100 rounds, 77 % at 1 000, 89 % at 10 000) because the large wins that make up most of the raw 105 % RTP are rejected while the reserve is small. The "house never loses" guarantee holds; "RTP 94 %" does not.
**Options (owner decision, not applied):** (a) lower the raw volatility (symbol weights, wild rates, Quantumeter charging, a lower `maxWin`) so more of the RTP comes from small and medium wins that the reserve can pay, then re-measure; (b) raise `rtpCap` above 0.94, which lowers the guaranteed house margin; (c) accept the reserve as is and describe the game honestly as a session-limited payout. Option (a) is the one that moves effective RTP toward 94 % without weakening the guarantee.
**Remaining:** decision on (a)/(b)/(c); Actions run for this commit; browser/iPhone/audio checks; nothing pushed to `main`.

## Session 4c (Claude, 2026-11-27) — exploration: effective RTP under the house reserve (no game change)
Owner said "continua"; Claude took option (a) (lower raw volatility, keep the documented paytable and the 0.94 reserve) and ran quick probes. **Nothing in the engine, `DEFAULTS` or `index.html` was changed.** Scripts: `sim/explore-governor/` (`node grid.js grid1.txt` etc.; labels `name@cap`). Each probe: 300 000 raw rounds (seed 9101), 2 000 × 100 governed (seed 9102), 300 × 1 000 governed (seed 9103). Exploration only, not a validation; numbers have roughly ±1–2 pts noise.
| candidate | change vs DEFAULTS | cap | raw RTP | governed RTP, 100-round sessions | governed RTP, 1 000-round sessions | max win in 1 000-round sessions |
|---|---|---|---|---|---|---|
| base | none | 0.94 | 103.0 % | 48.3 % | 76.3 % | 260.6x |
| cap500 | maxWin 500 | 0.94 | 99.9 % | 48.5 % | 76.4 % | — |
| pc20 / pc10 | pUnchargedAfterCascade 0.20 / 0.10 | 0.94 | 94.3 / 83.1 % | 46.9 / 46.4 % | 71.2 / 68.9 % | — |
| ft6 | fluctThreshold 6 | 0.94 | 38.2 % | 31.6 % | 36.3 % | — |
| base | none | 0.99 | 103.0 % | 49.8 % | 78.9 % | 260.6x |
| lh1 | symbolWeights [0.3,0.4,0.55,0.8,1.8,2.2,2.6,3.1] | 0.94 / 0.99 | 156.7 % | 60.8 / 63.0 % | 88.8 / 92.7 % | 140.6x |
| lh2 | symbolWeights [0.25,0.35,0.5,0.7,2.0,2.4,2.9,3.4] | 0.94 / 0.97 | 246.2 % | 73.1 / 74.7 % | 91.7 / 94.4 % | 84.1x |
| lh4_pc15 | symbolWeights [0.15,0.25,0.35,0.5,2.4,2.8,3.4,4.0], pUnchargedAfterCascade 0.15 | 0.94 | 452.6 % | 85.3 % | 93.2 % | 41.9x |
0 reserve violations in every probe.
**Findings.** (1) Lowering volatility alone (fewer wilds, lower maxWin, higher Fluctometer threshold) *lowers* governed RTP, because it lowers raw RTP too. (2) Raising the cap barely helps the current game: the bottleneck is the start of each session, when the reserve is small and every win above it is rejected. (3) Governed RTP near 94 % in 1 000-round sessions needs a raw game that overpays heavily (≈250–450 % raw RTP from frequent small low-symbol wins), so the reserve, not the paytable, sets the return, and large wins (Gargantoon, QUANTUM, MAX) practically disappear (max ≈ 40–85x). (4) With a hard cap of 0.94, effective RTP is always below 94 %, and lower in short sessions (100 rounds: ≤ 85 % in every candidate).
**Decision needed from the owner** before any `DEFAULTS` change: which trade-off to validate with 4 000 000 rounds on new seeds (see chat).

## Session 4d (Claude, 2026-11-27) — V5.1 calibration "lh4" with house reserve 0.94 (owner decision), branch only, NOT merged to main
**Owner choice:** candidate lh4 from session 4c, reserve cap 0.94 (house keeps ≥ 6 % of everything wagered at every moment of every session).
**Change in `engine/engine.js` `DEFAULTS`:** `symbolWeights` [0.35,0.45,0.6,0.9,1.5,1.9,2.3,2.8] → **[0.15,0.25,0.35,0.5,2.4,2.8,3.4,4.0]**; `pUnchargedAfterCascade` 0.35 → **0.15**. Unchanged: documented paytable (360/360), four reactors, Wilds, cascades, `maxWin` 5 083x, graphics, music, sounds. `index.html`: info-menu RTP sentence updated with the measured figures below; engine cache `?v=53`.
**Unlike V5.0, these values were chosen by looking at the RTP under the reserve** (session 4c probes), not by feature frequencies.
### Tests executed
- `node --test tests/engine.test.js tests/trace.test.js tests/governor.test.js`: 31/31.
- `python3 tests/ui-tests.py`: 38/38 (Chrome headless; includes deterministic replay engine = UI, reserve check, longest task < 400 ms → 0 ms). Not run: Safari, iPhone, audio by ear, GitHub Pages.
### Validation on new seeds (never used for tuning), bet = 1, independent sessions with a fresh reserve; 95 % CI on session RTPs (normal approximation)
| session length | sessions × rounds | seed | effective RTP | 95 % CI | session RTP min–max | per-round SD | max win | hit rate | rerolls/round |
|---|---|---|---|---|---|---|---|---|---|
| 100 | 10 000 × 1 000 000 | 20261202 | **85.34 %** | 85.23–85.45 % | 56.90–93.95 % | 1.70 | 34.6x | 62.21 % | 0.156 |
| 1 000 | 4 000 × 4 000 000 | 20261201 | **93.13 %** | 93.11–93.15 % | 89.74–94.00 % | 1.88 | 48.6x | 62.80 % | 0.139 |
| 10 000 | 200 × 2 000 000 | 20261203 | **93.92 %** | 93.92–93.93 % | 93.79–94.00 % | 1.90 | 45.1x | 62.88 % | 0.137 |
House guarantee in all 7 000 000 governed rounds: 0 rounds with paid > 0.94 × wagered, 0 moments and 0 sessions with the player ahead. Win sizes (1 000-round run): 0x 37.2 %, 0–1x 38.5 %, 1–5x 19.8 %, 5–20x 4.4 %, 20–100x 0.04 %, ≥ 100x none.
Raw engine without the reserve (reference only, never used by the game): 4 000 000 rounds, seed 20261204, RTP 454.67 % (CI 452.85–456.49 %), SD 18.58, max 1 218.2x, hit rate 67.35 %, 4.29 cascades/round, Gargantoon in 7.21 % of rounds, Quantumeter L4 4.93 %. Files: `sim/results-v5.1-lh4-*.json`.
### Honest reading
- **RTP 94.00 % target:** reached only approximately and only for long sessions: 93.1 % at 1 000 rounds, 93.9 % at 10 000; 85.3 % at 100 rounds. With a hard 0.94 cap it can never be exceeded and never be exactly reached.
- **Volatility is now low:** per-round SD ≈ 1.9 bets (V5.0 raw: 11.1); no governed win ≥ 100x in 7 M rounds, so BIG/MEGA WIN still appear but SUPER/EPIC/QUANTUM/MAX WIN tiers and large Gargantoon/Quantumeter payouts effectively never pay. Features still trigger visually in rounds that pay small amounts; rounds whose total would exceed the reserve are re-drawn.
- Outcomes depend on the session balance and are not independent draws; this is stated in the info menu. Free Play only.
- The interval is narrow because session RTPs are tightly bounded by the cap; it describes this engine, not the original game.
### Remaining
- Safari / iPhone / audio / GitHub Pages checks; owner review of the low-volatility feel; merge to `main` only on the owner's instruction.

## Session 5 (Claude, 2026-11-27) — animated reactor art for QUANTUMETER / FLUCTOMETER; board fills the frame (branch only)
**Owner request:** the two meters only showed numbers; give them an animated reactor background, and make the pieces fill the central frame, without changing what already exists.
**Design note:** the owner asked to use the original game as reference. Claude did **not** copy the original's artwork or layout; the reactor art is an original design for this project (generic sci-fi containment tubes, rings, conduits).
**Added (nothing removed, no ids changed, no gameplay change):**
- `reactor-panels.css` and `reactor-panels.js` (linked from `index.html`). The script only appends `aria-hidden` decoration nodes.
- QUANTUMETER: animated chamber behind the panel (hex lattice, two counter-rotating containment rings, breathing core, conduits with flowing light, status lamps, light sweep). Each of the four tubes is now a glass capsule with metal caps, plasma fill with rising bubbles and a moving surface wave, a reactor core that grows and brightens with the charge, and electric arcs when the level is reached. Level numbers and thresholds stay (on the caps; centred in portrait).
- FLUCTOMETER: circuit traces with travelling pulses and a slow turbine behind the panel; spinning portal ring behind the floating symbol; the bar is an energy conduit with streaming plasma and a spark at the fill head; the four reactor pods (ENERGOON, ENERGOON 2×2, GARGANTOON, ×2) have a core and two rotating rings that light up when active.
- `index.html`: one line in the meter update also sets `--qn` (charge 0–1) next to the existing `--q`, used by the core and wave.
- All new animations stop under `prefers-reduced-motion`.
**Board:** in landscape the arena now covers the frame opening (left 25.45 cqw, top 9.3 cqh, 40.65 cqw × 69.7 cqh; was a 68.8 cqh square), in portrait the grid now fills the full arena height (was a square leaving empty bands). Cells are no longer forced square; symbol images use `background-size: contain`, so they are not stretched. Only the approved skin; the uploaded `rr33` skin is untouched.
**Tests:** `tests/ui-tests.py` 39/39 (Chrome headless). The four "grelha quadrada" checks were replaced by "grelha preenche a moldura" checks (grid = arena box, aspect 0.8–1.2, contain); one new check that the reactor art is present. Longest task 0 ms. Engine unchanged (31/31 last run). Not checked: Safari, iPhone, audio, GitHub Pages.

## Session 5b (Claude, 2026-11-27) — Fluctometer icon uses the board artwork
**Owner request:** the character next to the Fluctometer bar must be the same as the pieces on the board. It was the old SVG sprite (`<use href="#rr-tN">`), not the skin's piece images.
**Change (`reactor-panels.js`, `reactor-panels.css`, cache `?v=2`):** an image layer `.rq-fl-orb` sits on the old SVG and shows the board image of the current floating symbol, taken from a live board cell with the same `data-symbol` (fallback: the matching skin CSS rule). A MutationObserver follows the `href` the game already updates, so nothing in the game code changed. The old SVG stays in the DOM, hidden. Gentle bob animation; stops under reduced motion.
**Tests:** `tests/ui-tests.py` 40/40 (new check: the icon image equals the board image for all 8 symbols). Not checked: Safari, iPhone, audio.

## Session 6 (Claude, 2026-11-27) — Godot 4.3 graphics, Web (WebGL 2) export, branch only
**Owner request:** do the graphics in Godot and publish to GitHub as WebGL. **Owner decisions:** keep the validated JS engine (Godot draws only); export on the branch first, publish to `main`/Pages only after validation.
**What was built:** new folder `Reactor-Rush-Godot/` (see its README). Godot cannot run in Claude's container, so the project was written by hand and built by GitHub Actions (`barichello/godot-ci:4.3`).
- Layout reproduces the HTML version over the same approved artwork (percentages measured from the HTML DOM), landscape and portrait; tall phones stretch the portrait art (max +30%) like the HTML.
- Board in the frame opening; drop-in, win pulse, explosions with particles, cascades computed from the engine's frames (survivors fall, new pieces enter from above); electric bolts on pair explosions.
- QUANTUMETER and FLUCTOMETER redrawn in Godot with the same original reactor design (tubes with plasma, bubbles, waves, cores, arcs; portal, energy conduit, reactor pods). The floating symbol uses the board artwork.
- HUD values on the artwork, +1.000 CR, bet −/+, turbo, auto, sound, info screen with the house-rule disclosure and the measured RTP figures. Win tiers and feature banners use the approved celebration images.
- Music `Quantum Arcade.mp3` and synthesised effects (sound off by default).
- `web/rr_bridge.js`: same governed play as `index.html` (reserve 0.94, slack 0.005, credited `round2(win × bet)` then settled). Checked in Node with the real engine: 500 rounds, paid/wagered 92.88 %, balance = 1000 − wagered + paid.
**CI results (run 46072308773, commit 0b66f1a9):** export OK (index.wasm 35 MB, index.pck 18 MB); script check OK; Chromium WebGL 2 test 15/15: engine connected, orientation, 30 + 5 rounds, reserve paid ≤ 94 % of wagered, balance consistent, clicking the spin button plays a round, no script errors in the console. Screenshots are printed into the smoke log (artifacts cannot be downloaded from Claude's container).
**Not done / known gaps:** Gargantoon/Energoon giant blocks are drawn as individual wild tiles (no merged giant artwork yet); no paytable table in the info screen; skin upload of the HTML version not ported; audio not checked by ear; Safari/iPhone not tested; no GitHub Pages publication (by decision).
