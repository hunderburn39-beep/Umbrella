/*
 * Reactor Rush — pure game engine (no DOM, no audio, no timers).
 *
 * Free Play only: every amount is a multiple of a virtual bet of 1.
 * The same file is meant to be used by the renderer (browser, window.RREngine)
 * and by the simulator/tests (Node, require()).
 *
 * IMPORTANT — evidence status
 * The reference PDF named in CLAUDE_TASKS.md could not be fetched in the session that
 * wrote this file (host not on the network allowlist). Mechanics below follow public
 * secondary descriptions (casinos.com, slotcatalog.com). Every rule that is an
 * interpretation, or that no source states, is tagged  [UNVERIFIED]  and is
 * listed in engine/ASSUMPTIONS.md. The PAYTABLE is original to this project:
 * no source gave the real one. Nothing here claims to reproduce the original
 * probabilities or RTP.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.RREngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const N = 7, CELLS = 49, TYPES = 8;
  // Cell codes: 0..7 regular symbols (0 = best, 7 = worst), then special cells.
  const U = 8;   // Uncharged Wild: blocker, becomes Electric when a win touches it
  const EL = 9;  // Electric Wild: substitutes, zaps when it is part of a win
  const EN = 10; // Energoon Wild (1x1 pieces, or a 2x2 block)
  const GA = 11; // Gargantoon Wild (3x3 / 2x2 blocks, or 1x1 pieces)

  const QM_LEVELS = [55, 85, 110, 135];          // from both secondary sources
  const SIZE_GROWTH = [1, 1.5, 2.2, 3.2, 4.6, 6.8, 10, 15, 23, 36, 60]; // sizes 5..15, original

  const DEFAULTS = {
    minCluster: 5,                 // [UNVERIFIED] slotcatalog says 5, casinos.com says 3
    maxWin: 5083,                  // x bet, stated by both sources
    payScale: 1.2258,              // single global factor: 0.962 / 0.78480 (calibration seed 111, 4M rounds, sim/calibration-seed111-4M.json)
    baseWin: [0.50, 0.40, 0.32, 0.26, 0.20, 0.16, 0.13, 0.10], // pay for a 5-cluster, original
    // Original tuning. With equal weights and the rules below, 5-clusters were rare (16% hit rate)
    // and the Quantumeter never reached level 1 in 100k rounds, so low symbols are weighted
    // heavier and wild sources are more frequent. Chosen by looking at feature frequencies
    // only (sim/explore results in DEVELOPMENT_LOG.md), never by looking at the RTP.
    symbolWeights: [0.35, 0.45, 0.6, 0.9, 1.5, 1.9, 2.3, 2.8],
    startUnchargedCum: [0.05, 0.25, 0.55, 0.80, 1], // P(0..4 uncharged wilds at spin start)
    pUnchargedAfterCascade: 0.35,  // [UNVERIFIED] sources only say "or after a cascade"
    pFluct: 1,                     // [UNVERIFIED] "may become" fluctuating
    fluctThreshold: 4,             // [UNVERIFIED] threshold not stated by any source
    fluctWildsMax: 3,              // "up to 3 Electric Wilds"
    qmLevels: QM_LEVELS,
    maxSteps: 400,
    maxCascades: 200,
  };

  // ---------- seeded PRNG (sfc32, splitmix32 seeding) ----------
  function createRng(seed) {
    let s = seed | 0;
    const sm = () => {
      s = (s + 0x9e3779b9) | 0;
      let t = s ^ (s >>> 16);
      t = Math.imul(t, 0x21f0aaac); t ^= t >>> 15;
      t = Math.imul(t, 0x735a2d97);
      return (t ^ (t >>> 15)) >>> 0;
    };
    let a = sm(), b = sm(), c = sm(), d = sm();
    const next = () => {
      a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0;
      let t = (a + b) | 0;
      a = b ^ (b >>> 9);
      b = (c + (c << 3)) | 0;
      c = (c << 21) | (c >>> 11);
      d = (d + 1) | 0;
      t = (t + d) | 0;
      c = (c + t) | 0;
      return (t >>> 0) / 4294967296;
    };
    for (let i = 0; i < 15; i++) next();
    return { next, int: n => Math.floor(next() * n) };
  }

  // ---------- paytable ----------
  function clusterPay(type, size, cfg) {
    let g = SIZE_GROWTH[Math.min(size, 15) - 5];
    if (g === undefined) g = SIZE_GROWTH[0] * Math.max(0.2, size / 5); // sizes below 5 (only if minCluster<5)
    if (size > 15) g *= 1 + (size - 15) * 0.35;
    return cfg.baseWin[type] * g * cfg.payScale;
  }

  function levelFor(charge, cfg) {
    const L = (cfg && cfg.qmLevels) || QM_LEVELS;
    let lv = 0;
    for (let i = 0; i < L.length; i++) if (charge >= L[i]) lv = i + 1;
    return lv;
  }

  // ---------- event trace (renderer support; never touches the RNG) ----------
  // Renderer cell format: {k,t,gid,size}. k: 'n' regular, 'u' Uncharged, 'e' Electric,
  // 'g1' Energoon 1x1, 'g2' Energoon 2x2, 'G3'/'G2'/'G1' Gargantoon 3x3/2x2/1x1.
  // t is the SPRITE index 0..7 = 7 - engine symbol (engine 0 = best, sprite 7 = best).
  function traceCell(st, i) {
    const v = st.g[i], id = st.bid[i], b = id ? st.blocks.get(id) : null;
    if (v < 8) return { k: 'n', t: 7 - v, gid: 0, size: 1 };
    if (v === U) return { k: 'u', t: -1, gid: 0, size: 1 };
    if (v === EL) return { k: 'e', t: -1, gid: 0, size: 1 };
    if (v === EN) return b && b.size === 2 ? { k: 'g2', t: -1, gid: id, size: 2 } : { k: 'g1', t: -1, gid: 0, size: 1 };
    return b && b.size === 3 ? { k: 'G3', t: -1, gid: id, size: 3 } : b && b.size === 2 ? { k: 'G2', t: -1, gid: id, size: 2 } : { k: 'G1', t: -1, gid: 0, size: 1 };
  }
  function traceGrid(st, hole) {
    const o = new Array(CELLS);
    for (let i = 0; i < CELLS; i++) o[i] = hole && hole[i] ? null : traceCell(st, i);
    return o;
  }
  function frame(st, type, extra) {
    if (!st.trace) return null;
    const f = extra || {};
    f.type = type; f.qm = st.qm; f.level = levelFor(st.qm, st.cfg); f.fl = st.fl; f.flMax = st.cfg.fluctThreshold;
    f.ovc = st.overcharge; f.garg = st.qmDisabled; f.total = st.total;
    st.trace.push(f); return f;
  }

  // ---------- state ----------
  function makeState(cfg, rng, grid) {
    const st = {
      cfg, rng,
      g: new Int8Array(CELLS), bid: new Int16Array(CELLS),
      blocks: new Map(), nextBid: 0,
      claimed: new Uint8Array(CELLS), vis: new Uint8Array(CELLS), rm: new Uint8Array(CELLS),
      stack: new Int16Array(CELLS * 4),
      fType: -1, fl: 0, qm: 0, qmDisabled: false, flDisabled: false, overcharge: false,
      total: 0, cascades: 0, steps: 0, capped: false,
      stats: { flAwards: 0, qmL: [0, 0, 0, 0], garg: false, splits3: 0, splits2: 0, explosions: 0, zaps: 0, zapped: 0, unchargedLit: 0 },
    };
    if (grid) for (let i = 0; i < CELLS; i++) st.g[i] = grid[i];
    return st;
  }

  const sumW = cfg => cfg.symbolWeights.reduce((a, b) => a + b, 0);
  function randSymbol(st) {
    const w = st.cfg.symbolWeights, tot = st._sumW || (st._sumW = sumW(st.cfg));
    let x = st.rng.next() * tot;
    for (let i = 0; i < TYPES; i++) { x -= w[i]; if (x < 0) return i; }
    return TYPES - 1;
  }

  // ---------- clusters ----------
  // Cluster = orthogonally connected cells of one regular type; Electric/Energoon/Gargantoon
  // substitute; Uncharged does not. Types are served from best to worst and every wild is
  // claimed by at most one paid cluster. [UNVERIFIED: wild sharing between clusters]
  function findClusters(st) {
    const g = st.g, claimed = st.claimed, vis = st.vis, stack = st.stack, min = st.cfg.minCluster, out = [];
    claimed.fill(0);
    for (let t = 0; t < TYPES; t++) {
      vis.fill(0);
      for (let s = 0; s < CELLS; s++) {
        if (g[s] !== t || claimed[s] || vis[s]) continue;
        let sp = 0; const cells = [];
        stack[sp++] = s; vis[s] = 1;
        while (sp) {
          const i = stack[--sp]; cells.push(i);
          const r = (i / N) | 0, c = i - r * N;
          if (r > 0) { const j = i - N; if (!claimed[j] && !vis[j] && (g[j] === t || g[j] >= EL)) { vis[j] = 1; stack[sp++] = j; } }
          if (r < N - 1) { const j = i + N; if (!claimed[j] && !vis[j] && (g[j] === t || g[j] >= EL)) { vis[j] = 1; stack[sp++] = j; } }
          if (c > 0) { const j = i - 1; if (!claimed[j] && !vis[j] && (g[j] === t || g[j] >= EL)) { vis[j] = 1; stack[sp++] = j; } }
          if (c < N - 1) { const j = i + 1; if (!claimed[j] && !vis[j] && (g[j] === t || g[j] >= EL)) { vis[j] = 1; stack[sp++] = j; } }
        }
        if (cells.length >= min) { for (const i of cells) claimed[i] = 1; out.push({ t, cells }); }
      }
    }
    return out;
  }

  // ---------- blocks ----------
  function blockFits(st, r, c, size) {
    if (r < 0 || c < 0 || r + size > N || c + size > N) return false;
    for (let y = r; y < r + size; y++) for (let x = c; x < c + size; x++) if (st.bid[y * N + x]) return false;
    return true;
  }
  function setBlock(st, r, c, size, kind) {
    const id = ++st.nextBid, cells = [];
    for (let y = r; y < r + size; y++) for (let x = c; x < c + size; x++) { const i = y * N + x; st.g[i] = kind; st.bid[i] = id; cells.push(i); }
    st.blocks.set(id, { kind, size, cells });
    return id;
  }
  function placeRandomBlock(st, size, kind) {
    const span = N - size + 1;
    for (let k = 0; k < 40; k++) {
      const r = st.rng.int(span), c = st.rng.int(span);
      if (blockFits(st, r, c, size)) return setBlock(st, r, c, size, kind), true;
    }
    for (let r = 0; r < span; r++) for (let c = 0; c < span; c++) if (blockFits(st, r, c, size)) return setBlock(st, r, c, size, kind), true;
    return false;
  }
  function randomFreeCells(st, n, predicate) {
    const pool = [];
    for (let i = 0; i < CELLS; i++) if (!st.bid[i] && (!predicate || predicate(st.g[i]))) pool.push(i);
    for (let i = 0; i < Math.min(n, pool.length); i++) { const j = i + st.rng.int(pool.length - i); const t = pool[i]; pool[i] = pool[j]; pool[j] = t; }
    return pool.slice(0, Math.min(n, pool.length));
  }

  // ---------- gravity with anchored blocks ----------
  // Blocks (3x3/2x2 wilds) stay in place. Cells fall inside each vertical segment between
  // anchors and the vacated top of the segment is refilled. [UNVERIFIED: original block physics]
  function gravityRefill(st) {
    const g = st.g, rm = st.rm, bid = st.bid;
    for (let c = 0; c < N; c++) {
      let r = N - 1;
      while (r >= 0) {
        if (bid[r * N + c] && !rm[r * N + c]) { r--; continue; }
        let top = r;
        while (top - 1 >= 0 && !(bid[(top - 1) * N + c] && !rm[(top - 1) * N + c])) top--;
        let w = r;
        for (let k = r; k >= top; k--) {
          const idx = k * N + c;
          if (!rm[idx]) { if (w !== k) g[w * N + c] = g[idx]; w--; }
        }
        for (let k = w; k >= top; k--) g[k * N + c] = randSymbol(st);
        r = top - 1;
      }
    }
    rm.fill(0);
  }

  // ---------- one winning step ----------
  function resolveStep(st, clusters) {
    const cfg = st.cfg, g = st.g, bid = st.bid, rm = st.rm, rng = st.rng;
    rm.fill(0);
    const tracing = !!st.trace, preGrid = tracing ? traceGrid(st) : null, tclusters = tracing ? [] : null, spawn = tracing ? [] : null;
    let stepWin = 0, flCount = 0;
    const winMask = new Uint8Array(CELLS), hit = new Set(), electricUsed = [];
    for (const cl of clusters) {
      let hasG = false;
      for (const i of cl.cells) {
        winMask[i] = 1; const v = g[i];
        if (v < 8) { rm[i] = 1; if (v === st.fType) flCount++; }
        else if (v === EL) { rm[i] = 1; electricUsed.push(i); }
        else if (v === EN) { if (bid[i]) hit.add(bid[i]); else rm[i] = 1; }
        else if (v === GA) { hasG = true; if (bid[i]) hit.add(bid[i]); else rm[i] = 1; }
      }
      const cpay = clusterPay(cl.t, cl.cells.length, cfg) * (st.overcharge && hasG ? 2 : 1);
      stepWin += cpay;
      if (tracing) { let wild = false; for (const i of cl.cells) if (g[i] >= 8) wild = true; tclusters.push({ type: 7 - cl.t, size: cl.cells.length, pay: cpay, cells: cl.cells.slice(), wild, gargX2: st.overcharge && hasG }); }
    }
    st.total += stepWin; st.cascades++;
    let wf = null;
    if (tracing) wf = frame(st, 'win', { grid: preGrid, clusters: tclusters, win: stepWin, cascade: st.cascades, zap: [], pendingStats: null });
    if (st.total >= cfg.maxWin) { st.total = cfg.maxWin; st.capped = true; if (wf) { wf.total = st.total; wf.capped = true; } return stepWin; }

    // Uncharged Wilds next to a winning cluster become Electric. Order: before removal.
    for (let i = 0; i < CELLS; i++) {
      if (g[i] !== U) continue;
      const r = (i / N) | 0, c = i - r * N;
      if ((r > 0 && winMask[i - N]) || (r < N - 1 && winMask[i + N]) || (c > 0 && winMask[i - 1]) || (c < N - 1 && winMask[i + 1])) { g[i] = EL; st.stats.unchargedLit++; }
    }
    // Fluctometer charged by fluctuating symbols removed in wins.
    if (!st.flDisabled) st.fl += flCount;

    // Block handling: Energoon blocks vanish; Gargantoon blocks split.
    let split3 = 0, split2 = 0;
    for (const id of hit) {
      const b = st.blocks.get(id); if (!b) continue;
      for (const i of b.cells) { rm[i] = 1; bid[i] = 0; }
      st.blocks.delete(id);
      if (b.kind === GA && b.size === 3) split3++;
      else if (b.kind === GA && b.size === 2) split2++;
    }
    // Electric Wilds that were part of a win zap one random regular symbol type on the grid:
    // every instance disappears and charges the Quantumeter 1 per symbol; the wild is consumed.
    // [UNVERIFIED] — sources only say "destroys all instances of the symbol it zaps".
    for (let k = 0; k < electricUsed.length; k++) {
      const counts = new Int16Array(TYPES); let present = 0;
      for (let i = 0; i < CELLS; i++) if (g[i] < 8 && !rm[i] && counts[g[i]]++ === 0) present++;
      if (!present) break;
      let pick = rng.int(present), type = 0;
      for (let t = 0; t < TYPES; t++) if (counts[t] && pick-- === 0) { type = t; break; }
      let n = 0; for (let i = 0; i < CELLS; i++) if (g[i] === type && !rm[i]) { rm[i] = 1; n++; if (wf) wf.zap.push(i); }
      st.stats.zaps++; st.stats.zapped += n;
      if (!st.qmDisabled) st.qm += n;
    }
    if (wf) { wf.qm = st.qm; wf.fl = st.fl; wf.level = levelFor(st.qm, cfg); wf.total = st.total; }
    gravityRefill(st);

    // Uncharged wild may appear after a cascade. [UNVERIFIED rate]
    if (rng.next() < cfg.pUnchargedAfterCascade) {
      const cell = randomFreeCells(st, 1, v => v < 8)[0]; if (cell !== undefined) g[cell] = U;
    }
    // Gargantoon splitting: 3x3 -> two 2x2, 2x2 -> nine 1x1.
    for (let k = 0; k < split3; k++) { st.stats.splits3++; placeRandomBlock(st, 2, GA); placeRandomBlock(st, 2, GA); if (spawn) spawn.push('G2', 'G2'); }
    for (let k = 0; k < split2; k++) { st.stats.splits2++; for (const i of randomFreeCells(st, 9)) g[i] = GA; if (spawn) spawn.push('G1'); }
    // Fluctometer award: 1..fluctWildsMax Electric Wilds per full charge.
    while (!st.flDisabled && st.fl >= cfg.fluctThreshold) {
      st.fl -= cfg.fluctThreshold; st.stats.flAwards++;
      for (const i of randomFreeCells(st, 1 + rng.int(cfg.fluctWildsMax), v => v < 8)) g[i] = EL;
      if (spawn) spawn.push('fluct');
    }
    if (tracing) frame(st, 'settle', { grid: traceGrid(st), cascade: st.cascades, spawn });
    return stepWin;
  }

  // ---------- Quantumeter ----------
  function runQuantumeter(st) {
    const lv = levelFor(st.qm, st.cfg);
    if (st.qmDisabled || lv === 0) return false;
    st.stats.qmL[lv - 1]++;
    if (st.trace) frame(st, 'level', { grid: traceGrid(st), reactor: lv });
    if (lv === 1) { for (const i of randomFreeCells(st, 4, v => v < 8)) st.g[i] = EN; st.qm = 0; }
    else if (lv === 2) { placeRandomBlock(st, 2, EN); st.qm = 0; }
    else {
      placeRandomBlock(st, 3, GA);
      st.qmDisabled = true; st.flDisabled = true; st.stats.garg = true; st.overcharge = lv === 4;
    }
    if (st.trace) frame(st, 'settle', { grid: traceGrid(st), cascade: st.cascades, spawn: [lv === 1 ? 'g1' : lv === 2 ? 'g2' : 'G3'], reactor: lv });
    return true;
  }

  // ---------- Wild Pair Explosion ----------
  function runPairExplosion(st) {
    const el = []; for (let i = 0; i < CELLS; i++) if (st.g[i] === EL) el.push(i);
    if (el.length < 2) return false;
    const a = el.splice(st.rng.int(el.length), 1)[0], b = el[st.rng.int(el.length)];
    const ra = (a / N) | 0, ca = a % N, rb = (b / N) | 0, cb = b % N;
    const adjacent = Math.abs(ra - rb) + Math.abs(ca - cb) === 1;
    st.rm.fill(0); let n = 0;
    const r0 = Math.min(ra, rb), r1 = Math.max(ra, rb), c0 = Math.min(ca, cb), c1 = Math.max(ca, cb);
    for (let i = 0; i < CELLS; i++) {
      if (st.g[i] >= 8) continue;
      const r = (i / N) | 0, c = i % N;
      if (adjacent || (r >= r0 && r <= r1 && c >= c0 && c <= c1)) { st.rm[i] = 1; n++; }
    }
    st.rm[a] = 1; st.rm[b] = 1;
    st.stats.explosions++;
    if (!st.qmDisabled) st.qm += n;
    if (st.trace) frame(st, 'explosion', { grid: traceGrid(st, st.rm), removed: n, pair: [a, b], electric: el.concat([a, b]) });
    gravityRefill(st);
    if (st.trace) frame(st, 'settle', { grid: traceGrid(st), cascade: st.cascades, spawn: [], afterExplosion: true });
    return true;
  }

  // ---------- full round ----------
  function startRound(st) {
    const cfg = st.cfg, rng = st.rng;
    for (let i = 0; i < CELLS; i++) st.g[i] = randSymbol(st);
    const x = rng.next(); let k = 0; while (k < cfg.startUnchargedCum.length - 1 && x >= cfg.startUnchargedCum[k]) k++;
    for (const i of randomFreeCells(st, k)) st.g[i] = U;
    st.fType = rng.next() < cfg.pFluct ? 4 + rng.int(4) : -1; // low-paying symbols only
  }

  // Same round as playRound (identical RNG consumption) plus a frame list for the renderer.
  function playRoundTrace(rng, userCfg) {
    const cfg = userCfg || DEFAULTS, st = makeState(cfg, rng);
    st.trace = [];
    startRound(st);
    frame(st, 'start', { grid: traceGrid(st), fluct: st.fType < 0 ? -1 : 7 - st.fType });
    runToRest(st);
    const r = summarize(st); r.frames = st.trace; return r;
  }

  function playRound(rng, userCfg) {
    const cfg = userCfg || DEFAULTS, st = makeState(cfg, rng);
    startRound(st);
    runToRest(st);
    return summarize(st);
  }

  function runToRest(st) {
    const cfg = st.cfg;
    for (; st.steps < cfg.maxSteps && !st.capped; st.steps++) {
      let did = false;
      while (!st.capped && st.cascades < cfg.maxCascades) {
        const cl = findClusters(st); if (!cl.length) break;
        resolveStep(st, cl); did = true;
      }
      if (st.capped) break;
      if (runQuantumeter(st)) continue;
      if (runPairExplosion(st)) continue;
      if (!did) break;
      // cascades produced something but nothing else is pending: re-check once more for safety
      if (!findClusters(st).length) break;
    }
  }

  function summarize(st) {
    return { win: st.total, cascades: st.cascades, capped: st.capped, steps: st.steps, qm: st.qm, stats: st.stats };
  }

  // ---------- batch simulation ----------
  function simulate(rounds, seed, userCfg) {
    const cfg = userCfg || DEFAULTS, rng = createRng(seed);
    const agg = { n: 0, sum: 0, sumSq: 0, hits: 0, maxWin: 0, capHits: 0, cascades: 0, steps: 0,
      flAwards: 0, qmL: [0, 0, 0, 0], garg: 0, splits3: 0, splits2: 0, explosions: 0, zaps: 0, unchargedLit: 0,
      buckets: { '0': 0, '0-1x': 0, '1-5x': 0, '5-20x': 0, '20-100x': 0, '100-500x': 0, '500x+': 0 } };
    for (let i = 0; i < rounds; i++) {
      const r = playRound(rng, cfg), w = r.win;
      agg.n++; agg.sum += w; agg.sumSq += w * w;
      if (w > 0) agg.hits++;
      if (w > agg.maxWin) agg.maxWin = w;
      if (r.capped) agg.capHits++;
      agg.cascades += r.cascades; agg.steps += r.steps;
      const s = r.stats;
      agg.flAwards += s.flAwards; for (let k = 0; k < 4; k++) agg.qmL[k] += s.qmL[k];
      if (s.garg) agg.garg++; agg.splits3 += s.splits3; agg.splits2 += s.splits2; agg.explosions += s.explosions; agg.zaps += s.zaps; agg.unchargedLit += s.unchargedLit;
      const b = agg.buckets; w === 0 ? b['0']++ : w < 1 ? b['0-1x']++ : w < 5 ? b['1-5x']++ : w < 20 ? b['5-20x']++ : w < 100 ? b['20-100x']++ : w < 500 ? b['100-500x']++ : b['500x+']++;
    }
    return agg;
  }

  function mergeAgg(list) {
    const out = { n: 0, sum: 0, sumSq: 0, hits: 0, maxWin: 0, capHits: 0, cascades: 0, steps: 0, flAwards: 0, qmL: [0, 0, 0, 0], garg: 0, splits3: 0, splits2: 0, explosions: 0, zaps: 0, unchargedLit: 0, buckets: {} };
    for (const a of list) {
      for (const k of ['n', 'sum', 'sumSq', 'hits', 'capHits', 'cascades', 'steps', 'flAwards', 'garg', 'splits3', 'splits2', 'explosions', 'zaps', 'unchargedLit']) out[k] += a[k];
      out.maxWin = Math.max(out.maxWin, a.maxWin);
      for (let k = 0; k < 4; k++) out.qmL[k] += a.qmL[k];
      for (const k in a.buckets) out.buckets[k] = (out.buckets[k] || 0) + a.buckets[k];
    }
    return out;
  }

  // RTP estimate with a normal-approximation 95% interval from the per-round variance.
  // Win distribution is heavy-tailed: the interval is approximate and may be optimistic.
  function rtpStats(a) {
    const mean = a.sum / a.n, variance = Math.max(0, (a.sumSq - a.n * mean * mean) / (a.n - 1));
    const se = Math.sqrt(variance / a.n);
    return { rtp: mean, se, ci95: [mean - 1.96 * se, mean + 1.96 * se], sd: Math.sqrt(variance), hitRate: a.hits / a.n };
  }

  return {
    N, CELLS, TYPES, U, EL, EN, GA, QM_LEVELS, DEFAULTS,
    createRng, clusterPay, levelFor, playRound, playRoundTrace, simulate, mergeAgg, rtpStats,
    _test: { makeState, findClusters, resolveStep, gravityRefill, runQuantumeter, runPairExplosion, startRound, runToRest, setBlock, blockFits, placeRandomBlock },
  };
});
