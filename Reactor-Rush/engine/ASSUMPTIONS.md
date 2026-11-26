# Engine assumptions — what is sourced, what is interpreted, what is invented

**Evidence status:** the reference PDF (`pokerstars.it/.../Reactoonz 2.pdf`) named in `CLAUDE_TASKS.md`
could **not** be fetched (host not on the session's network allowlist). The rules below come from two public
secondary descriptions (casinos.com and slotcatalog.com review pages). Neither gives a paytable.
Nothing in this folder reproduces, or claims to reproduce, the original probabilities, reel weights or RTP.

Legend: **S** = stated by a source · **I** = interpretation of a source · **O** = original to this project.

| Area | Implemented rule | Status |
|---|---|---|
| Grid | 7x7, gravity cascades until no win | S |
| Clusters | orthogonal groups of one symbol, minimum 5 | I (slotcatalog says 5, casinos.com says 3 — conflict) |
| Wild sharing | each wild is claimed by at most one paid cluster; types served best to worst | O |
| Paytable | 8 symbols, per-symbol base x size growth table (`baseWin`, `SIZE_GROWTH`) | **O — no source gives the real one** |
| Symbol weights | skewed toward low symbols | **O** |
| Uncharged Wild | 0–4 at spin start, 35% chance of one more after each win; blocks clusters; a winning cluster touching it makes it Electric | S (behaviour) / O (rates) |
| Fluctometer | one low symbol type is fluctuating each spin (always); each fluctuating symbol removed in a win charges it; 4 charges = 1..3 Electric Wilds; off once a Gargantoon appears | S (behaviour) / **O (threshold 4, always-on)** |
| Electric Wild | substitutes; when part of a win it zaps one random symbol type on the grid (all instances vanish, unpaid) and is consumed | I (sources say "destroys all instances of the symbol it zaps") |
| Quantumeter | +1 per symbol removed by a zap or by a pair explosion; resets each spin; levels at 55 / 85 / 110 / 135 | S (levels, charging) / I (reset per spin) |
| Level 1 | four 1x1 Energoon Wilds at random cells; meter resets | S (slotcatalog) — casinos.com says "4x1", conflict |
| Level 2 | one 2x2 Energoon Wild; meter resets | S |
| Level 3 | one 3x3 Gargantoon; disables Quantumeter and Fluctometer | S |
| Level 4 | as level 3, and wins containing a Gargantoon piece pay x2 (not cumulative) | I |
| Gargantoon splitting | 3x3 hit by a win -> two 2x2; 2x2 hit -> nine 1x1; 1x1 hit -> removed. New pieces land at random positions | S (counts) / O (positions) |
| Block physics | 3x3 / 2x2 blocks are anchored; symbols fall and refill within each vertical segment | O |
| Pair Explosion | after cascades and Quantumeter, with >=2 Electric Wilds: adjacent pair wipes every regular symbol; non-adjacent pair wipes regular symbols inside their bounding rectangle; the pair is consumed; repeats | S (behaviour) / I (bounding rectangle) |
| Activation order | cascades -> Fluctometer (inside the cascade step) -> Quantumeter -> Pair Explosion -> cascades again | I (neither source numbers the order) |
| Max win | 5083 x bet, round stops at the cap | S |
| RTP reference | 96.20 % | S (one source says operators often run 94.2 %) |

## Known deviations from the reference, measured
* **Volatility is far lower.** Highest win in 6M validated rounds was ~278 x bet; the reference max is 5083 x.
* Feature frequencies (Gargantoon in ~1 % of rounds, level 1 in ~3 %) are tuned, not original.
* `payScale` (1.2258) is a single global factor calibrated on seed 111 (4M rounds) and validated on other seeds.

## Questions only the PDF can answer (please upload it or paste its tables)
1. Real paytable (cluster size x symbol) and whether the minimum cluster is 3 or 5.
2. Fluctometer threshold and how many wilds each charge awards.
3. Whether Electric Wilds are consumed when part of a win, and what a zap targets.
4. Whether the Quantumeter carries over between spins, and whether levels 1/2 reset it.
5. Whether Gargantoon x2 is per piece or per win, and where split pieces land.
